from pymongo import MongoClient

from app.settings.settings import Settings

settings = Settings()


def get_db(client: MongoClient):
    return client[settings.DB_NAME]


def get_collection(client: MongoClient, collection_name: str):
    db = get_db(client)
    collection = db[collection_name]
    if not [index["name"] for index in collection.list_indexes()]:
        collection.create_index("district")
    return collection


def get_all_districts(collection):
    return collection.distinct("district")


def get_district_average_field_mapping(collection, field: str = "psm"):
    district_average_field_map = dict()

    cursor = collection.aggregate(
        [
            {
                "$group": {
                    "_id": {"district": "$district"},
                    "psm_avg": {"$avg": f"${field}"},
                }
            }
        ]
    )

    for cur in cursor:
        district_average_field_map[cur["_id"]["district"]] = cur["psm_avg"]

    return district_average_field_map


def get_coords(collection, city_name: str):
    return collection.find(
        {"city1": city_name}, {"coords": {"lat": 1, "lng": 1}, "psm": 1}
    )