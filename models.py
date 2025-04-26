
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pymongo import MongoClient, errors
from bson import ObjectId
import certifi
from config import TestingConfig, Config
import os
import datetime
from datetime import timezone

app = Flask(__name__)
app.config.from_object(TestingConfig if os.getenv("FLASK_ENV") == "testing" else Config)


mongo_uri = app.config["MONGO_URI"]


client = MongoClient(mongo_uri, tlsCAFile=certifi.where()) if "mongodb+srv" in mongo_uri else MongoClient(mongo_uri)
db_name = mongo_uri.rsplit("/", 1)[-1]
db = client[db_name]
articles_collection = db.articles

def fetch_all_articles(genre=None, source=None):
    """Retrieve all articles from the database."""
    query = {}
    if genre:
        query["genre"] = genre
    if source:
        query["author"] = source

    articles = list(articles_collection.find(query))
    

    for article in articles:
        article["_id"] = str(article["_id"])

    return articles

def fetch_article_by_id(article_id):
    """Retrieve a single article by ObjectId."""
    try:
        specfic_article = articles_collection.find_one({"_id": ObjectId(article_id)})
        specfic_article["_id"] = str(specfic_article["_id"])

        return specfic_article
    except:
        return None


def post_user_by_info(id, email, name, picture):
    try:
        users_collection = db.users
        users_collection.update_one(
            {"google_id": id},
            {"$set": {"name": name, "email": email}},
            upsert=True
        )
    except:
        return None


def search_articles(query):
    """Search articles by matching query against title, summary, and source (Case Insensitive)."""
    search_filter = {
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"summary": {"$regex": query, "$options": "i"}},
            {"source": {"$regex": query, "$options": "i"}},
            {"genre": {"$regex": query, "$options": "i"}}
        ]
    }

    articles = list(articles_collection.find(search_filter))

    for article in articles:
        article["_id"] = str(article["_id"])

    return articles

def save_comment(article_id, user_id, comment_body):
    comments_coll = db.comments
    try:
        comment = {
            "article_id": article_id,
            "user_id": user_id,
            "comment": comment_body,
            "timestamp": datetime.datetime.now(timezone.utc)
        }
        result = comments_coll.insert_one(comment)
        comment["_id"] = str(result.inserted_id)
        return comment
    except Exception as e:
        print("Error saving comment:", e)
        return None

def fetch_comments_by_id(article_id, limit=10):
    comments_collection = db.comments
    comments_cursor = comments_collection.find({"article_id": article_id}).limit(limit)
    comments = []
    for c in comments_cursor:
        c["_id"] = str(c["_id"])
        # Convert datetime to string for JSON serialization
        if isinstance(c.get("timestamp"), datetime.datetime):
            c["timestamp"] = c["timestamp"].isoformat()
        comments.append(c)
    return comments

def delete_comment_by_id(comment_id):
    comments_coll = db.comments
    try:
        result = comments_coll.delete_one({"_id": ObjectId(comment_id)})
        return result.deleted_count == 1
    except Exception as e:
        print("Error deleting comment:", e)
        return False
    
def save_rating(article_id, user_id, accuracy, bias, insight):
    ratings_coll = db.ratings
    try:
        rating = {
            "article_id": article_id,
            "user_id": user_id,
            "accuracy": accuracy,
            "bias": bias,
            "insight": insight
        }

        result = ratings_coll.insert_one(rating)
        rating["_id"] = str(result.inserted_id)
        return rating
    except Exception as e:
        print("Error saving rating.", e)
        return None
    
def fetch_ratings_by_article_id(article_id):
    ratings_coll = db.ratings
    try:
        ratings = list(ratings_coll.find({'article_id': article_id}))
        for rating in ratings:
            rating['_id'] = str(rating["_id"])
        return ratings


    except Exception as e:
        print('Error fetching ratings', e)
        return []

def fetch_details_by_user_id(user_id):
    users = db.users
    try:
        user_details = users.find_one({"google_id": user_id})
        if user_details:
            user_details["_id"] = str(user_details["_id"])
            return user_details
    except Exception as e:
        return None

def create_collection(user_id, collection_name):
    try:
        collections = db.article_collections

        existing_user = collections.find_one({"user_id": user_id})

        if not existing_user:
            new_doc = {
                "user_id": user_id,
                "collections": {
                    collection_name: []
                }
            }
            result = collections.insert_one(new_doc)
            new_doc["_id"] = str(result.inserted_id)
            return new_doc

        else:
            update_result = collections.update_one(
                {"user_id": user_id},
                {"$set": {f"collections.{collection_name}": []}}
            )

            if update_result.modified_count > 0:
                return {
                    "user_id": user_id,
                    "collection_name": collection_name
                }
            else:
                return None

    except Exception as e:
        print("Error in create_collection:", e)
        return None



def add_article_to_collection(user_id, collection_name, article_id):
    try:
        collections = db.article_collections

        result = collections.update_one(
            {
                "user_id": user_id,
                f"collections.{collection_name}": {"$exists": True}
            },
            {
                "$addToSet": {
                    f"collections.{collection_name}": article_id
                }
            }
        )

        return result.modified_count > 0
    except Exception as e:
        print("Error updating user collection:", e)
        return False

def fetch_comments_by_user_id(user_id, limit=10):
    comments_collection = db.comments
    comments_cursor = comments_collection.find({"user_id": user_id}).limit(limit)
    comments = []
    for c in comments_cursor:
        c["_id"] = str(c["_id"])
        # Convert datetime to string for JSON serialization
        if isinstance(c.get("timestamp"), datetime.datetime):
            c["timestamp"] = c["timestamp"].isoformat()
        comments.append(c)
    return comments