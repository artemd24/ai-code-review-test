import json

import pytest
from aiohttp import web

from app.lib.lib import set_values, create_hist
from app.schemas.schema import ParseCityRequest
from app.settings.settings import Settings

settings = Settings()


@pytest.mark.parametrize(
    ["url", "kwargs", "expected_result"],
    [
        ("localhost:8000/?token=1234", {}, "localhost:8000/?token=1234"),
        (
            "localhost:8000/?token=1234",
            {"city_name": "city"},
            "localhost:8000/?token=1234&q=city",
        ),
        (
            "localhost:8000/?token=1234",
            {"name": "name"},
            "localhost:8000/?token=1234&name=name",
        ),
    ],
)
def test_set_values(url, kwargs, expected_result):
    assert set_values(url, **kwargs) == expected_result


async def make_request(aiohttp_session_client, data):
    request_url = set_values("/", category_id=2, nedvigimost_type=2, **data.dict())
    print(request_url)

    async with aiohttp_session_client as session:
        async with session.get(request_url, ssl=False) as response:
            text = await response.text()
            print(text)

            return json.loads(text).get("data")


async def make_request_response(request):
    return web.Response(
        text='{"data": {"coords": {"lat": "59.871658","lng": "30.410038"},"address": "Софийская ул., 40К2"}}'
    )


@pytest.fixture
def cli(loop, aiohttp_client):
    request_url = "/&category_id=2&nedvigimost_type=2&q=Санкт-Петербург&date_from=2021-05-12+00:00:00&date_to=2021-05-12+01:00:00"

    app = web.Application()
    app.router.add_get(request_url, make_request_response)
    return loop.run_until_complete(aiohttp_client(app))


async def test_make_request(cli):
    data = ParseCityRequest(
        city_name="Санкт-Петербург",
        date_from="2021-05-12+00:00:00",
        date_to="2021-05-12+01:00:00",
    )

    assert await make_request(cli, data=data) == {
        "coords": {"lat": "59.871658", "lng": "30.410038"},
        "address": "Софийская ул., 40К2",
    }


# async def test_get_district(lat, lng):
#     request_url = set_values(settings.DADATA_API_URL, lat=lat, lon=lng, count=1)
#     logging.info(request_url)
#
#     async with aiohttp.ClientSession() as session:
#         async with session.get(request_url, headers={
#             "Accept": "application/json",
#             "Authorization": f"Token {settings.ADATA_TOKEN}"
#         }, verify_ssl=False) as response:
#             text = await response.text()
#
#             return json.loads(text).get('suggestions')[0].get('data').get('city_district')


@pytest.mark.parametrize(["field_name"], [("psm",), ("area",)])
def test_create_hist(field_name: str):
    try:
        file_path = create_hist(
            {"Фрунзенский": 2_550, "Центральный": 10_000}, "Санкт-Петербург", field_name
        )
        assert file_path.is_file()
    finally:
        file_path.unlink()
