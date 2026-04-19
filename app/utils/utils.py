import json

from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(self, o)


def count_psm(flat: dict) -> float:
    return float(flat["price"]) / float(flat["params"]["Площадь"])


def extract_area(flat: dict) -> float:
    return float(flat["params"]["Площадь"])


def prepare_coords_data(data, field: str = "psm"):
    return [*data["coords"].values(), data[field]]


def generate_date(
    day="01", month="05", year="2021", hour="00", minute="00", second="00"
):
    return f"{year}-{month}-{day}+{hour}:{minute}:{second}"


def serialize_datetime_to_dict(datetime):
    return dict(
        year=datetime.year,
        month=datetime.month,
        day=datetime.day,
        hour=datetime.hour,
        minute=datetime.minute,
        second=datetime.second,
    )
