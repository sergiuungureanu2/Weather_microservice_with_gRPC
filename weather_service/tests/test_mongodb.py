from datetime import datetime

def test_mongo_connection(mongo_client):
    db = mongo_client["weather_db"]
    coll = db["weather_logs"]
    assert coll is not None


def test_mongo_insert_and_retrieve(mongo_client):
    db = mongo_client["weather_db"]
    coll = db["weather_logs"]
    ts = int(datetime.utcnow().timestamp())
    doc = {"city": "London", "temperature": 7.2, "humidity": 75, "timestamp": ts, "datetime": datetime.utcnow()}
    coll.insert_one(doc)

    result = coll.find_one({"city": "London"})
    assert result["temperature"] == 7.2
    assert "datetime" in result
