from typing import List

import pytest

from app.utils.utils import count_psm, extract_area, prepare_coords_data

position_city = {
    "coords": {"lat": "59.871658", "lng": "30.410038"},
    "address": "Софийская ул., 40К2",
    "psm": 555.5555555555555,
    "district": "Фрунзенский",
    "area": 43.0,
}


@pytest.mark.parametrize(
    ["flat", "expected_result"],
    [({"price": 2300.0, "params": {"Площадь": 1000.0}}, 2.3)],
)
def test_count_psm(flat: dict, expected_result: float):
    assert count_psm(flat) == expected_result


@pytest.mark.parametrize(
    ["flat", "expected_result"],
    [({"price": 2300.0, "params": {"Площадь": 1000.0}}, 1000.0)],
)
def test_extract_area(flat: dict, expected_result: float):
    assert extract_area(flat) == expected_result


@pytest.mark.parametrize(
    ["data", "field", "expected_result"],
    [
        (position_city, "psm", ["59.871658", "30.410038", 555.5555555555555]),
        (position_city, "area", ["59.871658", "30.410038", 43.0]),
    ],
)
def test_prepare_coords_data(data, field: str, expected_result: List[float]):
    assert prepare_coords_data(data=data, field=field) == expected_result
