from typing import Dict, Any, List
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from app.settings.settings import Settings

settings = Settings()


def get_db(client: MongoClient):
    """Возвращает объект базы данных по имени из настроек."""
    return client[settings.DB_NAME]


def get_collection(client: MongoClient, collection_name: str) -> Collection:
    """
    Возвращает коллекцию MongoDB.
    Если у коллекции нет индекса по 'district', создаёт его.
    """
    db = get_db(client)
    collection = db[collection_name]

    # Проверяем, есть ли индекс по 'district'
    existing_indexes = [index["name"] for index in collection.list_indexes()]
    if "district_1" not in existing_indexes:
        collection.create_index([("district", ASCENDING)], name="district_1")

    return collection


def get_all_districts(collection: Collection) -> List[str]:
    """Возвращает список всех уникальных районов."""
    return collection.distinct("district")


def get_district_average_field_mapping(
    collection: Collection, field: str = "psm"
) -> Dict[str, float]:
    """
    Возвращает словарь: район → среднее значение указанного поля.
    По умолчанию считает среднее для поля 'psm'.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$district",
                "avg_value": {"$avg": f"${field}"},
            }
        }
    ]

    return {
        doc["_id"]: doc["avg_value"]
        for doc in collection.aggregate(pipeline)
        if doc.get("_id") is not None
    }


def get_coords(collection: Collection, city_name: str):
    """
    Возвращает координаты и значение 'psm' для всех документов по городу.
    """
    projection = {"coords.lat": 1, "coords.lng": 1, "psm": 1, "_id": 0}
    return collection.find({"city1": city_name}, projection)
