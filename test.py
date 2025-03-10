
from flask import Flask, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://ringofthelords:frodo123@esrsdb.awdlh.mongodb.net/"
mongo = PyMongo(app)


test_articles = [


    {"id": 1, "title": "Lorem Ipsum", "Genre": "Politics", "body": "This article has the ID of 1"},
    {"id": 2, "title": "Lorem Ipsum", "Genre": "Sports", "body": "This article has the ID of 2"},
    {"id": 3, "title": "Lorem Ipsum", "Genre": "Cooking", "body": "This article has the ID of 3"},
    {"id": 4, "title": "Lorem Ipsum", "Genre": "Entertainment", "body": "This article has the ID of 4"},
    {"id": 5, "title": "Lorem Ipsum", "Genre": "Sports Again", "body": "This article has the ID of 5"},
    
]

@app.route("/articles")
def get_articles():
    articles = test_articles
    return jsonify(articles)


@app.route("/articles/<id>")
def get_articles_by_id(id):
    articles = [a for a in test_articles if a["id"] == int(id)]
    return jsonify(articles)

if __name__ == "__main__":
    app.run(debug=True)
