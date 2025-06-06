import datetime
import os

from flask import request, jsonify, Flask
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import requests

import models
from models import db

app = Flask(__name__)

from flask_cors import CORS

CORS(app, origins=["http://localhost:5173", "http://localhost:8000"])

GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_SECRET")

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    token = request.json.get("token")

    if not token:
        return jsonify({"error": "Missing token"}), 400

    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(),
            '924933737757-s0f1a66cdpi2qesbgrmov0bttu8tq7ba.apps.googleusercontent.com')

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

    return jsonify(articles), 200


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
    limit = request.args.get("limit", default=None, type=int)
    try:
        result = models.fetch_comments_by_id(article_id, limit)
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
        return jsonify({"error": "Couldn't get user details"})


@app.route("/api/collections/create-new", methods=["POST"])
def create_new_user_collection():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        collection_name = data.get("collection_name")

        if not user_id or not collection_name:
            return jsonify({"error": "Missing user_id or collection_name"}), 400

        new_collection = models.create_collection(user_id, collection_name)

        if new_collection:
            return jsonify({
                "message": "Collection created successfully",
                "added_collection": new_collection
            }), 201
        else:
            return jsonify({"error": "Collection could not be created"}), 500

    except Exception as e:
        print("Error creating collection:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/collections/add-article/", methods=["POST"])
def add_article_to_user_collection():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        collection_name = data.get("collection_name")
        article_id = data.get("article_id")

        if not all([user_id, collection_name, article_id]):
            return jsonify({"error": "Missing required fields"}), 400

        updated = models.add_article_to_collection(user_id, collection_name, article_id)

        if updated:
            return jsonify({"message": "Article added to collection"}), 200
        else:
            return jsonify({"error": "Collection not found or article already exists"}), 404

    except Exception as e:
        print("Error adding article to collection:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/user/<string:user_id>/comments", methods=["GET"])
def get_comments_by_user_id(user_id):
    try:
        result = models.fetch_comments_by_user_id(user_id)
        if result:
            return jsonify({"msg": "Retrieved user comments.", "data": result}), 200
        else:
            return jsonify({"msg": "No comments found for this user.", "data": []}), 200
    except Exception as e:
        print("Error is: ", e)
        return jsonify({"error": "Server error."}), 500


@app.route("/api/articles/paginated", methods=["GET"])
def get_articles_paginated():
    genre = request.args.get("genre")
    source = request.args.get("source")
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)

    articles = models.fetch_all_articles_paginated(genre, source, page, limit)

    # Get the total count for pagination info
    # This is needed since we're returning just the paginated data
    query = {}
    if genre:
        query["genre"] = genre
    if source:
        query["author"] = source
    total_count = models.db.articles.count_documents(query)

    return jsonify({
        "page": page,
        "limit": limit,
        "count": len(articles),
        "total": total_count,
        "pages": (total_count + limit - 1) // limit,
        "data": articles
    }), 200


@app.route("/api/collections/<string:user_id>", methods=["GET"])
def get_user_collections(user_id):
    try:
        collections = models.fetch_user_collections(user_id)
        if collections:
            return jsonify(collections), 200
        else:
            return jsonify({"message": "No collections found", "collections": {}}), 200
    except Exception as e:
        print("Error fetching collections:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/collections/<string:user_id>/with-articles", methods=["GET"])
def get_collections_with_articles(user_id):
    """Get all collections for a user with article details."""
    try:
        collections = models.fetch_collections_with_articles(user_id)
        if collections:
            return jsonify(collections), 200
        else:
            return jsonify({"message": "No collections found", "collections": {}}), 200
    except Exception as e:
        print("Error fetching collections with articles:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/user/<string:user_id>/ratings", methods=["GET"])
def get_ratings_by_user_id(user_id):
    limit = request.args.get("limit", default=None, type=int)
    try:
        result = models.fetch_ratings_by_user_id(user_id, limit)
        if result:
            return jsonify({"msg": "Retrieved user ratings.", "data": result}), 200
        else:
            return jsonify({"msg": "No ratings found for this user.", "data": []}), 200
    except Exception as e:
        print("Error is: ", e)
        return jsonify({"error": "Server error."}), 500


@app.route("/api/collections/delete", methods=["DELETE"])
def delete_collection():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        collection_name = data.get("collection_name")

        if not user_id or not collection_name:
            return jsonify({"error": "Missing required fields"}), 400

        success = models.delete_collection(user_id, collection_name)

        if success:
            return jsonify({"message": "Collection deleted"}), 200
        else:
            return jsonify({"error": "Collection not found"}), 404
    except Exception as e:
        print("Error deleting collection:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/collections/remove-article", methods=["POST"])
def remove_article_from_collection():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        collection_name = data.get("collection_name")
        article_id = data.get("article_id")

        if not all([user_id, collection_name, article_id]):
            return jsonify({"error": "Missing fields"}), 400

        success = models.remove_article_from_collection(user_id, collection_name, article_id)
        if success:
            return jsonify({"message": "Article removed"}), 200
        else:
            return jsonify({"error": "Collection or article not found"}), 404
    except Exception as e:
        print("Error removing article:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/collections/rename", methods=["PATCH"])
def rename_collection():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        old_name = data.get("old_name")
        new_name = data.get("new_name")

        if not all([user_id, old_name, new_name]):
            return jsonify({"error": "Missing fields"}), 400

        success = models.rename_collection(user_id, old_name, new_name)
        if success:
            return jsonify({"message": "Collection renamed"}), 200
        else:
            return jsonify({"error": "Collection not found"}), 404
    except Exception as e:
        print("Error renaming collection:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/auth/google/code", methods=["POST"])
def google_auth_code():
    code = request.json.get("code")
    redirect_uri = request.json.get("redirect_uri")

    if not code or not redirect_uri:
        return jsonify({"error": "Missing code or redirect_uri"}), 400

    try:
        # Exchange code for token
        token_request = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": "924933737757-s0f1a66cdpi2qesbgrmov0bttu8tq7ba.apps.googleusercontent.com",
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )

        token_data = token_request.json()

        if "error" in token_data:
            return jsonify({"error": f"Token exchange failed: {token_data['error']}"}), 400

        # Verify the ID token
        id_token_value = token_data.get("id_token")
        if not id_token_value:
            return jsonify({"error": "No ID token in response"}), 400

        # Verify the token
        info = id_token.verify_oauth2_token(
            id_token_value,
            google_requests.Request(),
            "924933737757-s0f1a66cdpi2qesbgrmov0bttu8tq7ba.apps.googleusercontent.com"
        )

        user_data = {
            "id": info["sub"],
            "google_id": info["sub"],
            "email": info["email"],
            "name": info["name"],
            "picture": info["picture"]
        }

        models.post_user_by_info(info["sub"], info["email"], info["name"], info["picture"])

        return jsonify({"msg": "User authenticated", "user": user_data, "token": id_token_value}), 200
    except Exception as e:
        print("Google code verification failed:", e)
        return jsonify({"error": f"Invalid code: {str(e)}"}), 401
