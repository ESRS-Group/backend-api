import os

os.environ["FLASK_ENV"] = "testing"

import pytest
import controllers


@pytest.fixture
def client():
    app = controllers.app
    app.config["TESTING"] = True
    client = app.test_client()
    print(client)
    yield client


def test_get_all_articles(client):
    response = client.get("/api/articles")
    assert response.status_code == 200
    assert isinstance(response.json, list) or response.json == []


def test_get_article_by_invalid_id(client):
    response = client.get("/api/articles/123invalidid")
    assert response.status_code == 404
    assert response.json["error"] == "Article not found"


def test_insert_comment(client):
    payload = {
        "user_id": "user123",
        "comment": "This is a test comment!"
    }

    response = client.post('/api/comments/214365', json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Comment added"


def test_delete_comment(client):
    payload = {
        "user_id": "user123",
        "comment": "This comment will be deleted."
    }
    post_response = client.post('api/comments/123placeholderID', json=payload)
    assert post_response.status_code == 201

    new_comment = post_response.get_json()["new_comment"]
    comment_id = new_comment["_id"]

    delete_response = client.delete(f"/api/comments/{comment_id}")

    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == "Comment deleted successfully"


def test_get_comments_by_article_id(client):
    test_comments = [
        {
            "user_id": "LukeTheNuke",
            "comment": "This article sucks!"
        },
        {
            "user_id": "KenzieTheWise",
            "comment": "This article is quite interesting actually."
        },
        {
            "user_id": "SamTheTinCan",
            "comment": "I feel indifferent towards this article"
        }
    ]

    mongo_ids = []

    # Insert our test comments into db
    for comment in test_comments:
        post_response = client.post('api/comments/123comments_by_id_test', json=comment)
        assert post_response.status_code == 201
        # Keep a list of MongoDB's own created ID's for cleanup
        mongo_ids.append(post_response.get_json()['new_comment']['_id'])

    # Main test call, try and get all comments with this test ID
    comments_by_id = client.get("/api/comments/123comments_by_id_test")
    assert comments_by_id.status_code == 200

    # Get the data from the response, check its a list and length 3
    data = comments_by_id.get_json()["data"]
    assert isinstance(data, list)
    assert len(data) == 3

    # Create a comparison list and compare the returned response comments with the inserted test data
    returned_comments = [(comment["user_id"], comment["comment"]) for comment in data]
    for test_comment in test_comments:
        assert (test_comment["user_id"], test_comment["comment"]) in returned_comments

    # Cleanup and delete the comments from the testDB
    for comment_id in mongo_ids:
        cleanup = client.delete(f"/api/comments/{comment_id}")
        assert cleanup.status_code == 200


def test_post_new_rating(client):
    rating_test = {
        "user_id": "rating_test_user",
        "accuracy": 12,
        "bias": 47,
        "insight": 87
    }

    insert_rating_response = client.post("/api/ratings/test_rating_article_id", json=rating_test)

    assert insert_rating_response.status_code == 201

    new_rating_data = insert_rating_response.get_json()['data']

    assert new_rating_data['user_id'] == rating_test['user_id']
    assert new_rating_data['accuracy'] == rating_test['accuracy']
    assert new_rating_data['bias'] == rating_test['bias']
    assert new_rating_data['insight'] == rating_test['insight']


def test_get_ratings_by_article_id(client):
    response = client.get("/api/ratings/test_get_ratings_articleID")
    ratings_data = response.get_json()
    assert response.status_code == 200
    assert len(ratings_data) == 3

    expected_keys = {"_id", "user_id", "article_id", "accuracy", "bias", "insight"}
    for rating in ratings_data:
        assert rating.keys() == expected_keys


def test_get_details_by_user_id(client):
    response = client.get("/api/user/testGOOGLEid")
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["google_id"] == "testGOOGLEid"
    assert response_data["email"] == "chocolatefrog@gmail.com"
    assert response_data["name"] == "Sullivan McScott"


from models import db


def test_create_collection_for_new_user(client):
    collections = db.article_collections
    test_user_id = "new_test_user_001"
    collection_name = "Brand New Collection"

    collections.delete_one({"user_id": test_user_id})

    response = client.post("/api/collections/create-new", json={
        "user_id": test_user_id,
        "collection_name": collection_name
    })

    assert response.status_code == 201
    data = response.get_json()

    collection_doc = data["added_collection"]

    assert collection_doc["user_id"] == test_user_id
    assert collection_doc["collections"][collection_name] == []

    in_db = collections.find_one({"user_id": test_user_id})
    assert in_db["collections"].get(collection_name) == []
    collections.delete_one({"user_id": test_user_id})


def test_add_collection_to_existing_user(client):
    collections = db.article_collections
    test_user_id = "existing_test_user_002"
    first_collection = "Already Exists"
    second_collection = "Add This One"

    collections.delete_one({"user_id": test_user_id})
    collections.insert_one({
        "user_id": test_user_id,
        "collections": {
            first_collection: []
        }
    })

    response = client.post("/api/collections/create-new", json={
        "user_id": test_user_id,
        "collection_name": second_collection
    })

    assert response.status_code == 201
    data = response.get_json()
    print(data)
    assert data["added_collection"]["collection_name"] == second_collection

    user_doc = collections.find_one({"user_id": test_user_id})
    assert first_collection in user_doc["collections"]
    assert second_collection in user_doc["collections"]

    collections.delete_one({"user_id": test_user_id})


def test_add_article_to_user_collection(client):
    collections = db.article_collections
    test_user_id = "article_add_user"
    collection_name = "Test Collection"
    article_id = "article_123"

    collections.delete_one({"user_id": test_user_id})

    collections.insert_one({
        "user_id": test_user_id,
        "collections": {
            collection_name: []
        }
    })

    response = client.post("/api/collections/add-article/", json={
        "user_id": test_user_id,
        "collection_name": collection_name,
        "article_id": article_id
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Article added to collection"

    doc = collections.find_one({"user_id": test_user_id})
    assert collection_name in doc["collections"]
    assert article_id in doc["collections"][collection_name]

    collections.delete_one({"user_id": test_user_id})


def test_delete_user_collection(client):
    collections = db.article_collections
    user_id = "delete_test_user"
    collection_name = "Trash"

    collections.insert_one({"user_id": user_id, "collections": {collection_name: []}})
    response = client.delete("/api/collections/delete", json={"user_id": user_id, "collection_name": collection_name})

    assert response.status_code == 200
    doc = collections.find_one({"user_id": user_id})
    assert collection_name not in doc["collections"]
    collections.delete_one({"user_id": user_id})


def test_remove_article_from_collection(client):
    user_id = "remove_article_user"
    collection_name = "Reading"
    article_id = "article_to_remove"

    db.article_collections.insert_one({
        "user_id": user_id,
        "collections": {collection_name: [article_id]}
    })

    response = client.post("/api/collections/remove-article", json={
        "user_id": user_id,
        "collection_name": collection_name,
        "article_id": article_id
    })

    assert response.status_code == 200
    doc = db.article_collections.find_one({"user_id": user_id})
    assert article_id not in doc["collections"][collection_name]
    db.article_collections.delete_one({"user_id": user_id})


def test_rename_collection(client):
    user_id = "rename_user"
    old_name = "Old Name"
    new_name = "New Name"

    db.article_collections.insert_one({
        "user_id": user_id,
        "collections": {old_name: ["abc"]}
    })

    response = client.patch("/api/collections/rename", json={
        "user_id": user_id,
        "old_name": old_name,
        "new_name": new_name
    })

    assert response.status_code == 200
    doc = db.article_collections.find_one({"user_id": user_id})
    assert new_name in doc["collections"]
    assert old_name not in doc["collections"]
    db.article_collections.delete_one({"user_id": user_id})
