from flask import Blueprint, request, jsonify
from utils.db_config import get_db_connection

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/favorites")

# 查詢某使用者的收藏清單
@favorite_bp.route("/<int:user_id>", methods=["GET"])
def get_favorites(user_id):
    print(f"🔍 查詢使用者 {user_id} 的收藏清單")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT R.* FROM Favorite F
        JOIN Restaurant R ON F.restaurant_id = R.restaurant_id
        WHERE F.user_id = %s
    """, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

# 加入收藏
@favorite_bp.route("", methods=["POST"])
def add_favorite():
    print("🔍 新增收藏")
    data = request.get_json()
    user_id = data.get("user_id")
    restaurant_id = data.get("restaurant_id")

    if not user_id or not restaurant_id:
        return jsonify({"error": "Missing user_id or restaurant_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Favorite (user_id, restaurant_id) VALUES (%s, %s)",
            (user_id, restaurant_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Added to favorites"})

# 移除收藏
@favorite_bp.route("", methods=["DELETE"])
def remove_favorite():
    print("🔍 移除收藏")
    data = request.get_json()
    user_id = data.get("user_id")
    restaurant_id = data.get("restaurant_id")

    if not user_id or not restaurant_id:
        return jsonify({"error": "Missing user_id or restaurant_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM Favorite WHERE user_id = %s AND restaurant_id = %s",
            (user_id, restaurant_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Removed from favorites"})