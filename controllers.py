
from flask import request, jsonify, Flask
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models import db
import models

app = Flask(__name__)

from flask_cors import CORS

CORS(app, origins=["http://localhost:5173"])

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    token = request.json.get("token")
    
    if not token:
        return jsonify({"error": "Missing token"}), 400
    
    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), '924933737757-s0f1a66cdpi2qesbgrmov0bttu8tq7ba.apps.googleusercontent.com')

        user_data = {
            "google_id": info["sub"],
            "email": info["email"],
            "name": info["name"],
            "picture": info["picture"]
        }

        models.post_user_by_info(info["sub"], info["email"], info["name"], info["picture"])

        return jsonify({"msg": "User authenticated", "user": user_data}), 200
    except ValueError as e:
        print("Google token verification failed:", e)
        return jsonify({"error": "Invalid token"}), 401

"""
Example query
/api/articles?genre=World&source=BBC-News

"""
@app.route("/api/articles", methods=["GET"])
def get_articles():
    genre = request.args.get("genre")
    source = request.args.get("source")
    articles = models.fetch_all_articles(genre, source)

    return articles, 200

"""
Example query
/api/articles/67bf73248d2ae870c932d262
"""

@app.route("/api/articles/<string:id>")
def get_article_by_id(id):
    article = models.fetch_article_by_id(id)
    if article:
        return article, 200
    return jsonify({"error": "Article not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)

