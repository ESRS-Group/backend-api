
from flask import request, jsonify, Flask
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models import db
import models
import datetime

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


@app.route("/api/articles/search", methods=["GET"])
def search_articles():
    query = request.args.get("q")

    if not query:
        return jsonify({"error": "Missing search query"}), 400

    articles = models.search_articles(query)

    return jsonify(articles), 200


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/api/comments/<string:id>", methods=["POST"])
def post_comment(id):
    data = request.get_json()
    author = data.get("user_id")
    content = data.get("comment")

    if not author or not content:
        return jsonify({"error": "Missing author or content"}), 400

    new_comment = models.save_comment(id, author, content)

    if new_comment:
        # Convert datetime to string for JSON serialization
        if isinstance(new_comment.get("timestamp"), datetime.datetime):
            new_comment["timestamp"] = new_comment["timestamp"].isoformat()
        return jsonify({"message": "Comment added", "new_comment": new_comment}), 201
    else:
        return jsonify({"error": "Failed to add comment"}), 500
    
@app.route("/api/comments/<string:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    try:
        result = models.delete_comment_by_id(comment_id)
        if result:
            return jsonify({"message": "Comment deleted successfully"}), 200
        else:
            return jsonify({"error": "Comment not found"}), 404
    except Exception as e:
        print("Error is: ", e)
        return jsonify({"error": "Server error"}), 500
    
@app.route("/api/comments/<string:article_id>", methods=["GET"])
def get_comments_by_article_id(article_id):
    limit = request.args.get("limit", default=10, type=int)
    try:
        result = models.fetch_comments_by_id(article_id, limit)
        print(result)
        if result:
            return jsonify({"msg": "Retrieved comments.", "data": result}), 200
        else:
            return jsonify({"error": "Failed to retrieve comments."}), 404
    except Exception as e:
        print("Error is: ", e)
        return jsonify({"error": "Server error."}), 500
    

@app.route("/api/ratings/<string:article_id>", methods=['POST'])
def post_new_rating(article_id):
    data = request.get_json()
    user_id = data.get("user_id")
    accuracy = data.get("accuracy")
    bias = data.get("bias")
    insight = data.get("insight")

    if not user_id or accuracy is None or bias is None or insight is None:
        return jsonify({"error": "Missing one or more required fields."})
    
    new_rating = models.save_rating(article_id, user_id, accuracy, bias, insight)

    if new_rating:
        return jsonify({"msg": "New rating submitted", "data": new_rating}), 201
    else:
        return jsonify({"error": "Failed to submit rating"}), 500
    

@app.route("/api/ratings/<string:article_id>", methods=["GET"])
def get_ratings_by_article_id(article_id):
    try:
        ratings = models.fetch_ratings_by_article_id(article_id)
        return jsonify(ratings), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch ratings properly."}), 500
    

@app.route("/api/user/<string:user_id>", methods=["GET"])
def get_user_details_by_user_id(user_id):
    try:
        details = models.fetch_details_by_user_id(user_id)
        if details is None:
            return jsonify({"error": "User not found."}), 404
        return jsonify(details), 200
    except Exception as e:
        return jsonify({"error": "Couldn't get user details."})