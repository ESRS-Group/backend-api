import os
os.environ["FLASK_ENV"] = "testing"

import pytest
from unittest.mock import patch
from flask import json
import controllers
from models import db


os.environ["FLASK_ENV"] = "testing"

@pytest.fixture
def client():
    app = controllers.app
    app.config["TESTING"] = True
    client = app.test_client()
    yield client

def test_get_all_articles(client):
    response = client.get("/api/articles")
    assert response.status_code == 200
    assert isinstance(response.json, list) or response.json == []

def test_get_article_by_invalid_id(client):
    response = client.get("/api/articles/123invalidid")
    assert response.status_code == 404
    assert response.json["error"] == "Article not found"
