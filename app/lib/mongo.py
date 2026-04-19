"""Модуль для работы с MongoDB: получение данных о районах и координатах."""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.settings.settings import Settings

# Загрузка настроек приложения
settings = Settings()


def get_database(client: MongoClient) -> Database:
    """
    Возвращает базу данных, указанную в настройках.

    Args:
        client: Подключение к MongoDB.

    Returns:
        Объект базы данных.
    """
    return client[settings.DB_NAME]


def ensure_district_index(collection: Collection) -> None:
    """
    Создаёт индекс по полю 'district', если он ещё не существует.

    Args:
        collection: Коллекция MongoDB.
    """
    existing_indexes = [index["name"] for index in collection.list_indexes()]
    if "district_1" not in existing_indexes:  # стандартное имя индекса для одного поля
        collection.create_index("district")


def get_collection(client: MongoClient, collection_name: str) -> Collection:
    """
    Возвращает коллекцию с гарантированным индексом на поле 'district'.

    Args:
        client: Подключение к MongoDB.
        collection_name: Имя коллекции.

    Returns:
        Объект коллекции.
    """
    db = get_database(client)
    collection = db[collection_name]
    ensure_district_index(collection)
    return collection


def get_all_districts(collection: Collection) -> list:
    """
    Возвращает список всех уникальных районов.

    Args:
        collection: Коллекция MongoDB.

    Returns:
        Список уникальных значений поля 'district'.
    """
    return collection.distinct("district")


def compute_average_by_district(collection: Collection, field: str = "psm") -> dict:
    """
    Вычисляет среднее значение указанного поля для каждого района.

    Args:
        collection: Коллекция MongoDB.
        field: Поле, для которого вычисляется среднее (по умолчанию 'psm').

    Returns:
        Словарь вида {район: среднее_значение}.
    """
    pipeline = [
        {
            "$group": {
                "_id": {"district": "$district"},
                "average_value": {"$avg": f"${field}"},
            }
        }
    ]

    result = {}
    for document in collection.aggregate(pipeline):
        district = document["_id"]["district"]
        average = document["average_value"]
        result[district] = average

    return result


def get_coordinates_by_city(collection: Collection, city_name: str):
    """
    Возвращает координаты и значение PSM для записей указанного города.

    Args:
        collection: Коллекция MongoDB.
        city_name: Название города (поле 'city1').

    Returns:
        Курсор с документами, содержащими поля 'coords.lat', 'coords.lng' и 'psm'.
    """
    projection = {
        "coords.lat": 1,
        "coords.lng": 1,
        "psm": 1,
        "_id": 0  # исключаем _id для чистоты результата
    }
    return collection.find({"city1": city_name}, projection)