import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiohttp
import matplotlib

from app.lib.mongo import get_collection
from app.schemas.schema import ParseCity, FlatDBEntity
from app.settings.paths import TMP_PATH
from app.settings.settings import Settings
from app.utils.utils import (
    generate_date,
    count_psm,
    extract_area,
    JSONEncoder,
    serialize_datetime_to_dict,
)

matplotlib.use("Agg")

import matplotlib.pyplot as plt

settings = Settings()


def set_values(url, **kwargs):
    for k, v in kwargs.items():
        if k == "city_name":
            url += f"&q={v}"
        else:
            url += f"&{k}={v}"
    return url


async def make_request(data):
    request_url = set_values(
        settings.AUTHORIZED_ADS_API_URL,
        category_id=2,
        nedvigimost_type=2,
        **data.dict(),
    )
    logging.info(request_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(request_url, verify_ssl=False) as response:
            text = await response.text()

            return json.loads(text).get("data")


async def get_district(lat, lng):
    request_url = set_values(settings.DADATA_API_URL, lat=lat, lon=lng, count=1)
    logging.info(request_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            request_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {settings.ADATA_TOKEN}",
            },
            verify_ssl=False,
        ) as response:
            text = await response.text()

            return (
                json.loads(text).get("suggestions")[0].get("data").get("city_district")
            )


def create_hist(data, city_name: str, field_name: str):
    hist_path = TMP_PATH / f"{city_name}/{field_name}.png"

    if hist_path.exists():
        created_timestamp = hist_path.stat().st_birthtime
        if datetime.fromtimestamp(created_timestamp) > datetime.now() - timedelta(
            minutes=5
        ):
            return hist_path

    plt.figure(figsize=(10, 10))
    plt.bar(list(data.keys()), data.values(), color="#607c8e")

    plt.title(f"Цена съема жилья на квадратный метр в городе {city_name}")
    plt.xlabel("Районы")

    plt.ylabel(settings.Y_LABEL_MAPPING[field_name])

    plt.tick_params(axis="x", rotation=40)
    plt.tight_layout()

    plt.savefig(hist_path)
    return hist_path


def configure_data(city_name):
    now_datetime = datetime.now()
    recent_datetime = now_datetime - timedelta(minutes=5)

    return ParseCity(
        city_name=city_name,
        date_from=generate_date(serialize_datetime_to_dict(now_datetime)),
        date_to=generate_date(serialize_datetime_to_dict(recent_datetime)),
    )


async def parse_city(client, city_name):
    request = configure_data(city_name)

    data = await make_request(request)

    collection = get_collection(client=client, collection_name=city_name)

    response = []
    for flat in data:
        district = await get_district(**flat.get("coords"))

        if district is not None:
            response.append(
                collection.insert(
                    FlatDBEntity(
                        **flat,
                        psm=count_psm(flat),
                        district=district,
                        area=extract_area(flat),
                    ).dict()
                )
            )

    return JSONEncoder().encode(response)


async def get_cities():
    for city in settings.DEFAULT_CITIES:
        yield city


async def background_parsing(client):
    while True:
        async for city in get_cities():
            await parse_city(client, city)

        await asyncio.sleep(settings.PARSE_PERIOD)
