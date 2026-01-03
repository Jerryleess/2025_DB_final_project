from flask import Blueprint, request, jsonify
from utils.db_config import get_db_connection

review_bp = Blueprint("review", __name__, url_prefix="/api/reviews")

# 查看指定餐廳的所有評論
@review_bp.route("/<restaurant_id>", methods=["GET"])
def get_reviews(restaurant_id):
    print(f"🔍 查詢餐廳 {restaurant_id} 的所有評論")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Reviews.*, User.username
        FROM Reviews
        JOIN User ON Reviews.user_id = User.user_id
        WHERE Reviews.restaurant_id = %s
    """, (restaurant_id,))
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(reviews)


# 新增一則評論
@review_bp.route("", methods=["POST"])
def add_review():
    print("🔍 新增評論")
    data = request.json
    user_id = data.get("user_id")
    restaurant_id = data.get("restaurant_id")
    rating = data.get("rating")
    comment = data.get("comment")
    review_date = data.get("review_date")  # 格式: YYYY-MM-DD

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Reviews (user_id, restaurant_id, rating, comment, review_date)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, restaurant_id, rating, comment, review_date)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Review added successfully"}), 201

# 編輯一則評論
@review_bp.route("/<int:review_id>", methods=["PUT"])
def update_review(review_id):
    print(f"🔍 更新評論 {review_id}")
    data = request.json
    rating = data.get("rating")
    comment = data.get("comment")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Reviews SET rating = %s, comment = %s
        WHERE review_id = %s
        """,
        (rating, comment, review_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Review updated successfully"})

# 刪除一則評論
@review_bp.route("/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    print(f"🔍 刪除評論 {review_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Reviews WHERE review_id = %s", (review_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Review deleted successfully"})