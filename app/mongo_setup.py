from pymongo import MongoClient
from datetime import datetime, timezone

MONGO_URI = "mongodb+srv://artjominnbox:fxNQp9mGuhUPav8c@covid19project.bunrdt6.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["covid19_supplementary"]
collection = db["comments"]

def insert_comment(country, province, date, user, comment, source, annotations=None, data_point_id=None):
    doc = {
        "data_point_id": data_point_id or f"{country}-{province}-{date.strftime('%Y-%m-%d')}",
        "country": country,
        "province": province,
        "date": date,
        "user": user,
        "comment": comment,
        "source": source,
        "annotations": annotations or [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    collection.insert_one(doc)
    print(f"Document for {country}, {province}, {date.strftime('%Y-%m-%d')} inserted successfully!")

def query_mongo(country=None, province=None, limit=100):
    query = {}
    if country:
        query["country"] = country
    if province:
        query["province"] = province
    cursor = collection.find(query).limit(limit)
    return list(cursor)
