from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from backend.app import generate_route, TextRequest
from backend.poi_catalog import (
    is_open_at,
    load_poi_catalog_or_fallback,
    validate_poi_catalog,
)


ROOT = Path(__file__).resolve().parents[2]


def sample_catalog() -> list[dict]:
    with (ROOT / "data" / "poiCatalog.sample.json").open("r", encoding="utf-8") as file:
        return json.load(file)


class PoiCatalogTest(unittest.TestCase):
    def test_sample_json_passes_validation(self) -> None:
        self.assertEqual(validate_poi_catalog(sample_catalog()), [])

    def test_invalid_type_is_detected(self) -> None:
        catalog = sample_catalog()
        catalog[0]["type"] = "park"
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("type" in error for error in errors))

    def test_score_out_of_range_is_detected(self) -> None:
        catalog = sample_catalog()
        catalog[0]["photoScore"] = 6
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("photoScore" in error for error in errors))

    def test_duplicate_id_is_detected(self) -> None:
        catalog = sample_catalog()
        catalog[1]["id"] = catalog[0]["id"]
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("duplicated" in error for error in errors))

    def test_missing_catalog_falls_back_to_mock(self) -> None:
        fallback = [{"id": "mock", "name": "mock place"}]
        catalog, loaded, errors = load_poi_catalog_or_fallback(ROOT / "data" / "missing-poiCatalog.json", fallback)
        self.assertFalse(loaded)
        self.assertEqual(catalog, fallback)
        self.assertTrue(errors)

    def test_route_api_shape_stays_stable(self) -> None:
        data = generate_route(TextRequest(text="test"))["routeData"]
        self.assertEqual(set(data), {"constraints", "places", "route", "diff"})

    def test_opening_hours_period_validation(self) -> None:
        catalog = sample_catalog()
        poi = copy.deepcopy(catalog[0])
        poi["openingHours"] = [
            {"days": [1], "periods": [{"open": "22:00", "close": "10:00", "crossDay": False}]}
        ]
        poi["openHoursConfidence"] = "high"
        errors = validate_poi_catalog([poi, *catalog[1:]])
        self.assertTrue(any("close" in error and "crossDay" in error for error in errors))

    def test_cross_day_opening_hours_is_supported(self) -> None:
        poi = {
            "openingHours": [
                {"days": [1], "periods": [{"open": "18:00", "close": "02:00", "crossDay": True}]}
            ],
            "openHoursConfidence": "high",
        }
        self.assertTrue(is_open_at(poi, 1, "23:00"))
        self.assertTrue(is_open_at(poi, 2, "01:30"))
        self.assertFalse(is_open_at(poi, 2, "03:00"))

    def test_unknown_opening_hours_returns_none(self) -> None:
        poi = {"openingHours": [], "openHoursConfidence": "unknown"}
        self.assertIsNone(is_open_at(poi, 1, "12:00"))


if __name__ == "__main__":
    unittest.main()
