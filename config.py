import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.environ["MONGO_PATH"]


class TestingConfig(Config):
    MONGO_URI = os.environ["MONGO_TEST_PATH"]
