from pymongo import MongoClient
from app.settings.settings import Settings

settings = Settings()

def get_db(client):
    return client[settings.DB_NAME]

def get_collection(client, collection_name):
    db = get_db(client)
    collection = db[collection_name]
    if "district_1" not in [idx["name"] for idx in collection.list_indexes()]:
        collection.create_index("district")
    return collection

def get_all_districts(collection):
    return collection.distinct("district")

def get_district_average_field_mapping(collection, field="psm"):
    res = {}
    for doc in collection.aggregate([{"$group": {"_id": {"district": "$district"}, "avg": {"$avg": f"${field}"}}}]):
        res[doc["_id"]["district"]] = doc["avg"]
    return res

def get_coords(collection, city_name):
    return collection.find({"city1": city_name}, {"coords.lat": 1, "coords.lng": 1, "psm": 1, "_id": 0})