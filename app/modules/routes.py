import asyncio
import os

import folium
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from folium.plugins import HeatMap
from pymongo import MongoClient

from app.lib.lib import (
    make_request,
    get_district,
    create_hist,
    background_parsing,
)
from app.lib.mongo import (
    get_collection,
    get_district_average_field_mapping,
    get_coords,
)
from app.schemas.schema import (
    ParseCityRequest,
    FlatDBEntity,
    PositionCityResponse,
)
from app.settings.paths import TMP_PATH
from app.settings.settings import Settings
from app.utils.utils import (
    JSONEncoder,
    count_psm,
    extract_area,
    prepare_coords_data,
)

settings = Settings()
router = APIRouter()
client: MongoClient = MongoClient(settings.DB_URL)


@router.get("/")
def root():
    return "success"


@router.on_event("startup")
async def start_background_parsing():
    asyncio.create_task(background_parsing(client))


@router.on_event("startup")
async def create_city_dirs_tmp():
    for city in settings.DEFAULT_CITIES:
        path = TMP_PATH / city
        if not path.exists():
            os.mkdir(path)


@router.post("/parse")
async def parse(request: ParseCityRequest):
    data = await make_request(request)
    collection = get_collection(client=client, collection_name=request.city_name)

    response = []
    for flat in data:
        district = await get_district(**flat.get("coords"))

        if district is not None:
            entity = FlatDBEntity(
                **flat,
                psm=count_psm(flat),
                district=district,
                area=extract_area(flat),
            )
            response.append(collection.insert(entity.dict()))

    return JSONEncoder().encode(response)


@router.get("/positions/{city_name}")
async def positions(city_name: str):
    collection = get_collection(client=client, collection_name=city_name)
    result = collection.find(
        {"city1": city_name},
        {"coords": 1, "address": 1, "psm": 1, "district": 1},
    )

    return [PositionCityResponse(**item) for item in result]


@router.get("/average/{city_name}/{field_name}")
async def get_average(city_name: str, field_name: str):
    if field_name not in ("psm", "area"):
        raise HTTPException(
            status_code=404,
            detail='Field is not supported. Use one of ("psm", "area")',
        )

    collection = get_collection(client=client, collection_name=city_name)
    result = get_district_average_field_mapping(collection=collection, field=field_name)
    return result


@router.get("/build_hist/{city_name}/{field_name}")
async def build_hist(city_name: str, field_name: str):
    if field_name not in ("psm", "area"):
        raise HTTPException(
            status_code=404,
            detail='Field is not supported. Use one of ("psm", "area")',
        )

    collection = get_collection(client=client, collection_name=city_name)
    result = get_district_average_field_mapping(collection=collection, field=field_name)
    hist_path = create_hist(result, city_name, field_name)

    return FileResponse(hist_path)


@router.get("/heatmap")
async def heatmap(city_name: str):
    collection = get_collection(client=client, collection_name=city_name)
    result = get_coords(collection, city_name)

    coords_list = [prepare_coords_data(flat) for flat in result]
    map_obj = folium.Map(
        location=settings.COORDS[city_name],
        tiles="stamentoner",
        zoom_start=6,
    )

    HeatMap(coords_list).add_to(map_obj)
    return HTMLResponse(map_obj._repr_html_())
