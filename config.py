
class Config:
    MONGO_URI = "mongodb+srv://ringofthelords:frodo123@esrsdb.awdlh.mongodb.net/esrsdb"

class TestingConfig(Config):
    MONGO_URI = "mongodb+srv://ringlord:freddo3@esrstest.yf1qd.mongodb.net/ESRStest"  # Adjust if you're mocking
