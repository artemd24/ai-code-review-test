from pydantic import BaseModel


class ParseCityRequest(BaseModel):
    city_name: str
    date_from: str
    date_to: str

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "city_name": "Санкт-Петербург",
                "date_from": "2021-05-12+00:00:00",
                "date_to": "2021-05-12+01:00:00",
            }
        }


class ParseCity(ParseCityRequest):
    ...


class Coord(BaseModel):
    lat: str
    lng: str


class PositionCityResponse(BaseModel):
    coords: Coord
    address: str
    psm: float
    district: str

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "coords": {"lat": "59.871658", "lng": "30.410038"},
            "address": "Софийская ул., 40К2",
            "psm": 555.5555555555555,
            "district": "Фрунзенский",
        }


class FlatDBEntity(BaseModel):
    city1: str
    title: str
    coords: Coord
    address: str
    metro: str
    price: str
    params: dict
    psm: float
    district: str
    area: float
