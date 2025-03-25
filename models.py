
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pymongo import MongoClient, errors
from bson import ObjectId
import certifi


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://ringofthelords:frodo123@esrsdb.awdlh.mongodb.net/"


client = MongoClient("mongodb+srv://ringofthelords:frodo123@esrsdb.awdlh.mongodb.net/", tlsCAFile=certifi.where())
db = client.esrsdb
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

        
