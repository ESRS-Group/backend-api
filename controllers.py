
from flask import Flask, jsonify, request
import models

app = Flask(__name__)

"""
TO DO

Need to think about proper error handling, how this might work in the front end.
Need to start unit testing.
Hosting will need to be done if 

"""


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

