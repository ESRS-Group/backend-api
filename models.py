
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pymongo import MongoClient, errors
from bson import ObjectId
import certifi
from config import TestingConfig, Config
import os


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
            {"source": {"$regex": query, "$options": "i"}}
        ]
    }

    articles = list(articles_collection.find(search_filter))

    for article in articles:
        article["_id"] = str(article["_id"])

    return articles
    
    
        
