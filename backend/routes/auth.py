import routes.restaurant as res
import utils.db as db
from flask import Blueprint, jsonify, request
from utils.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)


# Search User
@auth_bp.route("/api/users")
def get_users():
    users = db.query_all("SELECT [user_id], [username], [role], [email] FROM [dbo].[User]")
    return jsonify(users)


# Register New User
@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    email = data.get("email")

    if not username or not password:
        return jsonify({"error": "缺少 username 或 password"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    conn.autocommit = False

    try:
        cursor.execute("SELECT 1 FROM [dbo].[User] WHERE [username] = ?", (username,))
        if cursor.fetchone():
            raise ValueError("帳號已存在")

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO [dbo].[User] ([username], [password], [role], [email])
            OUTPUT INSERTED.[user_id]
            VALUES (?, ?, ?, ?);
            """,
            (username, hashed_password, role, email),
        )
        user_id = int(cursor.fetchone()[0])

        # owner -> 建立餐廳資料（同一個 transaction）
        if role == "owner":
            rest = data.get("restaurant") or {}
            if not rest:
                return jsonify({"error": "owner 角色必須提供 restaurant 資料"}), 400

            required_fields = ["name", "address", "phone"]
            missing = [k for k in required_fields if not rest.get(k)]
            if missing:
                return jsonify({"error": f"restaurant 資料不完整，缺少: {', '.join(missing)}"}), 400

            restaurant_id = res.generate_unique_restaurant_id(cursor)
            rest["owner_id"] = user_id
            rest["restaurant_id"] = restaurant_id

            # 這裡的 insert_restaurant 必須「不要 commit」
            res.insert_restaurant(rest, cursor)

        conn.commit()
        return jsonify({"message": "OK", "user_id": user_id}), 201

    except ValueError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 409  # 或依情境分 400/409
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# User Login
@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "缺少 username 或 password"}), 400

    user = db.query_one(
        """
        SELECT [user_id], [username], [password] AS password_hash, [role], [email]
        FROM [dbo].[User]
        WHERE [username] = ?
        """,
        (username,),
    )

    if not user:
        return jsonify({"error": "Wrong username or password"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Wrong username or password"}), 401

    user.pop("password_hash", None)
    return jsonify({"message": "Login successfully", "user": user}), 200


# Update User Info
@auth_bp.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    email = data.get("email")

    # 至少要有一個欄位要更新
    if username is None and password is None and role is None and email is None:
        return jsonify({"error": "沒有提供任何要更新的欄位"}), 400

    hashed_password = generate_password_hash(password) if password else None

    # 用 COALESCE 做 partial update
    sql = """
        UPDATE [dbo].[User] SET
            [username] = COALESCE(?, [username]),
            [password] = COALESCE(?, [password]),
            [role]     = COALESCE(?, [role]),
            [email]    = COALESCE(?, [email])
        WHERE [user_id] = ?
    """
    params = (username, hashed_password, role, email, user_id)

    try:
        rows = db.execute(sql, params)
        if rows == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User info updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete User
@auth_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    sql = "DELETE FROM [dbo].[User] WHERE [user_id] = ?"

    try:
        rows = db.execute(sql, (user_id,))
        if rows == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
