import os

from flask import Flask
from routes.auth import auth_bp
from routes.restaurant import restaurant_bp
from routes.review import review_bp
from routes.favorite import favorite_bp
from routes.image import image_bp
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

allow = os.getenv("FRONTEND_URL", "").split(",") if os.getenv("ALLOW_ORIGINS", "") else []
allow.append("http://localhost:3000") # backend
allow.append("http://localhost:5173") # frontend

CORS(
    app,
    resources={r"/*": {"origins": allow or "*"}},  # 或者列出特定路徑)
    supports_credentials=True,
    methods=["GET","POST","PUT","DELETE","OPTIONS"],
    allow_headers=["Content-Type","Authorization","X-Requested-With"],
    max_age=86400,
)
    

app.register_blueprint(auth_bp)
app.register_blueprint(restaurant_bp)
app.register_blueprint(review_bp)
app.register_blueprint(favorite_bp)
app.register_blueprint(image_bp)

@app.route("/")
def hello():
    return {"message": "✅ API is running."}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)