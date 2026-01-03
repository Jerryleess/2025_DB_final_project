import os
import base64
import re

from flask import Blueprint, request, jsonify
from utils.db import query_all, execute, get_db_connection

restaurant_bp = Blueprint("restaurant", __name__, url_prefix="/api/restaurants")


INSERT_RES = """
IF NOT EXISTS (
    SELECT 1 FROM [dbo].[Restaurant]
    WHERE [restaurant_id] = ?
)
BEGIN
    INSERT INTO [dbo].[Restaurant] (
        [restaurant_id],
        [owner_id],
        [name],
        [address],
        [phone],
        [price_range],
        [rating],
        [cover],
        [county],
        [district],
        [station_name],
        [latitude],
        [longitude]
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
END
"""

INSERT_CUISINE = """
IF NOT EXISTS (
    SELECT 1 FROM [dbo].[Cuisine] WHERE [slug] = ?
)
BEGIN
    INSERT INTO [dbo].[Cuisine] ([name], [slug])
    VALUES (?, ?)
END
"""

GET_CUISINE_ID = "SELECT [id] FROM [dbo].[Cuisine] WHERE [slug] = ?"

INSERT_RES_TO_CUI = """
IF NOT EXISTS (
    SELECT 1 FROM [dbo].[Res_to_Cui]
    WHERE [restaurant_id] = ? AND [cuisine_id] = ?
)
BEGIN
    INSERT INTO [dbo].[Res_to_Cui] ([restaurant_id], [cuisine_id])
    VALUES (?, ?)
END
"""

def generate_unique_restaurant_id(cursor):
    while True:
        rand = os.urandom(9)
        candidate = "ChIJ" + base64.urlsafe_b64encode(rand).decode("utf-8").rstrip("=")
        cursor.execute("SELECT 1 FROM [dbo].[Restaurant] WHERE [restaurant_id] = ?", (candidate,))
        if cursor.fetchone() is None:
            return candidate

def slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

def insert_restaurant(data: dict, cursor):
    # 基本欄位保護（避免 KeyError）
    required = ["restaurant_id", "owner_id", "name", "address", "phone"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise Exception(f"restaurant 缺少必要欄位: {', '.join(missing)}")

    # 允許缺省的 nested 欄位
    district = data.get("district") or {}
    station_name = data.get("station_name") or {}
    location = data.get("location") or {}

    cursor.execute(
        INSERT_RES,
        data["restaurant_id"],         # IF NOT EXISTS check
        data["restaurant_id"],         # insert restaurant_id
        data["owner_id"],
        data["name"],
        data["address"],
        data["phone"],
        data.get("price_range"),
        data.get("rating", 0),
        data.get("cover") or data.get("image"),
        district.get("county", ""),
        district.get("district", ""),
        station_name.get("cn", ""),
        location.get("latitude"),
        location.get("longitude"),
    )

    # cuisine_type 可能是 list 或 None
    cuisine_list = data.get("cuisine_type") or []
    for cuisine in cuisine_list:
        slug = slugify(cuisine)
        if not slug:
            continue

        cursor.execute(INSERT_CUISINE, (slug, cuisine, slug))

        cursor.execute(GET_CUISINE_ID, (slug,))
        row = cursor.fetchone()
        if not row:
            raise Exception(f"無法取得 cuisine id: {cuisine}")
        cuisine_id = row[0]

        cursor.execute(
            INSERT_RES_TO_CUI,
            (data["restaurant_id"], cuisine_id, data["restaurant_id"], cuisine_id),
        )

# 📌 新增店家
@restaurant_bp.route("", methods=["POST"])
def create_restaurant():
    print("🔍 新增店家")
    data = request.get_json()
    restaurant_id = generate_unique_restaurant_id()

    sql = """
        INSERT INTO Restaurant (
            restaurant_id, owner_id, name, address, phone,
            price_range, cuisine_type, rating, cover,
            county, district, station_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        restaurant_id,
        data.get("owner_id"),
        data.get("name"),
        data.get("address"),
        data.get("phone"),
        data.get("price_range"),
        data.get("cuisine_type"),
        data.get("rating", 0),
        data.get("cover"),
        data.get("county"),
        data.get("district"),
        data.get("station_name"),
    )
    print("✅ 新產生的 restaurant_id:", restaurant_id)
    execute(sql, params)
    return jsonify({"message": "✅ 店家新增成功", "restaurant_id": restaurant_id}), 201

# ✏️ 編輯店家
@restaurant_bp.route("/<restaurant_id>", methods=["PUT"])
def update_restaurant(restaurant_id):
    print(f"🔍 更新店家 {restaurant_id}")
    data = request.get_json()
    sql = """
        UPDATE Restaurant SET
            name=%s, address=%s, phone=%s,
            price_range=%s, cuisine_type=%s, rating=%s, cover=%s,
            county=%s, district=%s, station_name=%s
        WHERE restaurant_id = %s
    """
    params = (
        data.get("name"),
        data.get("address"),
        data.get("phone"),
        data.get("price_range"),
        data.get("cuisine_type"),
        data.get("rating"),
        data.get("cover"),
        data.get("county"),
        data.get("district"),
        data.get("station_name"),
        restaurant_id
    )
    execute(sql, params)
    return jsonify({"message": "✅ 店家資訊已更新"})

# 🔍 查詢店家（支援條件篩選）
# restaurant.py 中的 get_restaurants()
@restaurant_bp.route("", methods=["GET"])
def get_restaurants():
    print("🔍 查詢店家")
    conditions = []
    values = []

    if q := request.args.get("q"):
        conditions.append("name LIKE %s")
        values.append(f"%{q}%")
    if county := request.args.get("county"):
        conditions.append("county = %s")
        values.append(county)
    if district := request.args.get("district"):
        conditions.append("district = %s")
        values.append(district)
    if station := request.args.get("station"):
        conditions.append("station_name = %s")
        values.append(station)
    if cuisine := request.args.get("cuisine"):
        conditions.append("cuisine_type LIKE %s")
        values.append(f"%{cuisine}%")
    if owner_id := request.args.get("owner_id"):
        conditions.append("owner_id = %s")
        values.append(owner_id)

    sql = "SELECT * FROM Restaurant"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    results = query_all(sql, values)
    return jsonify(results)


# 🔍 查詢單一店家
@restaurant_bp.route("/<restaurant_id>", methods=["GET"])
def get_restaurant(restaurant_id):
    print(f"🔍 查詢店家 {restaurant_id}")
    sql = "SELECT * FROM Restaurant WHERE restaurant_id = %s"
    result = query_all(sql, (restaurant_id,))
    if not result:
        return jsonify({"message": "找不到該店家"}), 404
    return jsonify(result[0])

# ❌ 刪除店家
@restaurant_bp.route("/<restaurant_id>", methods=["DELETE"])
def delete_restaurant(restaurant_id):
    print(f"🔍 刪除店家 {restaurant_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Restaurant WHERE restaurant_id = %s", (restaurant_id,))
        conn.commit()
        return jsonify({"message": "餐廳刪除成功"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()