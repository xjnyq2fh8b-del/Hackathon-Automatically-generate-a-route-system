from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from backend.app import generate_route, TextRequest
from backend.poi_catalog import (
    calculate_route_budget,
    csv_to_catalog,
    get_buffer_candidates,
    get_non_coffee_buffer_candidates,
    is_open_at,
    load_poi_catalog_or_fallback,
    parse_opening_hours_text,
    to_frontend_places,
    validate_poi_catalog,
    validate_poi_catalog_with_warnings,
    write_catalog_json,
)
from backend.app import adjust_route, AdjustRequest


ROOT = Path(__file__).resolve().parents[2]
ROUTE_DATA_KEYS = {"constraints", "places", "optimizedPlaces", "route", "diff", "debug", "message", "adjustmentButtons"}


def sample_catalog() -> list[dict]:
    with (ROOT / "data" / "poiCatalog.sample.json").open("r", encoding="utf-8") as file:
        return json.load(file)


class PoiCatalogTest(unittest.TestCase):
    def test_sample_json_passes_validation(self) -> None:
        self.assertEqual(validate_poi_catalog(sample_catalog()), [])

    def test_sample_csv_passes_validation(self) -> None:
        _, result = csv_to_catalog(ROOT / "data" / "poiCatalog.sample.csv")
        self.assertEqual(result.errors, [])

    def test_csv_converts_arrays_and_location(self) -> None:
        catalog, result = csv_to_catalog(ROOT / "data" / "poiCatalog.sample.csv")
        self.assertEqual(result.errors, [])
        self.assertIsInstance(catalog[0]["tags"], list)
        self.assertIsInstance(catalog[0]["experienceTags"], list)
        self.assertIsInstance(catalog[0]["location"], dict)
        self.assertIn("lng", catalog[0]["location"])
        self.assertIn("lat", catalog[0]["location"])

    def test_frontend_places_keep_manual_image_url_first(self) -> None:
        places = to_frontend_places(
            [
                {
                    "id": "manual",
                    "name": "manual image",
                    "type": "scenic",
                    "imageUrl": "https://manual.example/image.jpg",
                    "photos": [{"url": "https://amap.example/image.jpg"}],
                }
            ]
        )
        self.assertEqual(places[0]["imageUrl"], "https://manual.example/image.jpg")

    def test_frontend_places_use_first_amap_photo_when_no_manual_image(self) -> None:
        places = to_frontend_places(
            [
                {
                    "id": "amap",
                    "name": "amap image",
                    "type": "scenic",
                    "photos": [{"url": "https://amap.example/image.jpg"}],
                }
            ]
        )
        self.assertEqual(places[0]["imageUrl"], "https://amap.example/image.jpg")

    def test_frontend_places_omit_image_url_when_missing(self) -> None:
        places = to_frontend_places([{"id": "no-image", "name": "no image", "type": "scenic"}])
        self.assertNotIn("imageUrl", places[0])

    def test_frontend_places_generate_reason_when_catalog_note_is_empty(self) -> None:
        places = to_frontend_places(
            [
                {
                    "id": "scenic",
                    "name": "西湖景点",
                    "type": "scenic",
                    "tags": ["湖景", "步行友好"],
                    "note": "",
                }
            ]
        )
        self.assertIn("湖景", places[0]["reason"])
        self.assertNotEqual(places[0]["reason"], "")

    def test_csv_can_be_written_to_json(self) -> None:
        catalog, result = csv_to_catalog(ROOT / "data" / "poiCatalog.sample.csv")
        self.assertEqual(result.errors, [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "poiCatalog.json"
            write_catalog_json(catalog, output_path)
            self.assertTrue(output_path.exists())
            self.assertIsInstance(json.loads(output_path.read_text(encoding="utf-8")), list)

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

    def test_invalid_wait_risk_is_detected(self) -> None:
        catalog = sample_catalog()
        catalog[0]["waitRisk"] = "maybe"
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("waitRisk" in error for error in errors))

    def test_invalid_crowd_risk_is_detected(self) -> None:
        catalog = sample_catalog()
        catalog[0]["crowdRisk"] = "maybe"
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("crowdRisk" in error for error in errors))

    def test_missing_catalog_falls_back_to_mock(self) -> None:
        fallback = [{"id": "mock", "name": "mock place"}]
        catalog, loaded, errors = load_poi_catalog_or_fallback(ROOT / "data" / "missing-poiCatalog.json", fallback)
        self.assertFalse(loaded)
        self.assertEqual(catalog, fallback)
        self.assertTrue(errors)

    def test_route_api_shape_stays_stable(self) -> None:
        data = generate_route(TextRequest(text="test"))["routeData"]
        self.assertEqual(set(data), ROUTE_DATA_KEYS)

    def test_opening_hours_period_validation(self) -> None:
        catalog = sample_catalog()
        poi = copy.deepcopy(catalog[0])
        poi["openingHours"] = [
            {"days": [1], "periods": [{"open": "22:00", "close": "10:00", "crossDay": False}]}
        ]
        poi["openHoursConfidence"] = "high"
        errors = validate_poi_catalog([poi, *catalog[1:]])
        self.assertTrue(any("close" in error and "crossDay" in error for error in errors))

    def test_complex_open_hours_warns(self) -> None:
        catalog = sample_catalog()
        poi = copy.deepcopy(catalog[0])
        poi["openHoursText"] = "周一至周五10:30-14:00;16:00-21:00"
        poi["openingHours"] = []
        poi["openHoursConfidence"] = "medium"
        result = validate_poi_catalog_with_warnings([poi, *catalog[1:]])
        self.assertEqual(result.errors, [])
        self.assertTrue(any("openingHours" in warning for warning in result.warnings))

    def test_24_hours_text_parses_to_always_open(self) -> None:
        opening_hours = parse_opening_hours_text("24小时营业")
        self.assertEqual(opening_hours[0]["days"], [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(opening_hours[0]["periods"][0]["open"], "00:00")
        self.assertEqual(opening_hours[0]["periods"][0]["close"], "23:59")

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

    def test_buffer_candidate_counts(self) -> None:
        catalog = sample_catalog()
        self.assertGreaterEqual(len(get_buffer_candidates(catalog)), 6)
        self.assertGreaterEqual(len(get_non_coffee_buffer_candidates(catalog)), 3)

    def test_buffer_candidate_shortage_is_detected(self) -> None:
        catalog = [poi for poi in sample_catalog() if poi["type"] not in {"coffee", "rest", "snack", "mall"}]
        errors = validate_poi_catalog(catalog)
        self.assertTrue(any("bufferCandidates" in error for error in errors))
        self.assertTrue(any("nonCoffeeBufferCandidates" in error for error in errors))

    def test_budget_rules_by_role_and_type(self) -> None:
        catalog = [
            {"id": "start", "type": "start", "avgCost": 999},
            {"id": "scenic", "type": "scenic", "avgCost": 999},
            {"id": "photo", "type": "photo", "avgCost": 999},
            {"id": "coffee", "type": "coffee", "avgCost": 30},
            {"id": "dinner", "type": "dinner", "avgCost": 80},
            {"id": "snack", "type": "snack", "avgCost": 12},
            {"id": "mall", "type": "mall", "avgCost": 999},
            {"id": "rest", "type": "rest", "avgCost": 999},
            {"id": "mall-paid", "type": "mall", "avgCost": 20, "costIncludedByDefault": True},
        ]
        route_nodes = [{"placeId": poi["id"]} for poi in catalog]
        self.assertEqual(calculate_route_budget(route_nodes, catalog), 142)

    def test_start_role_overrides_poi_type_for_budget(self) -> None:
        catalog = [{"id": "coffee-start", "type": "coffee", "avgCost": 40}]
        route_nodes = [{"placeId": "coffee-start", "role": "start"}]
        self.assertEqual(calculate_route_budget(route_nodes, catalog), 0)

    def test_adjustment_apis_return_route_and_diff_without_route_patch(self) -> None:
        for adjustment_type in ["restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"]:
            data = adjust_route(AdjustRequest(adjustmentType=adjustment_type))["routeData"]
            self.assertIn("route", data)
            self.assertIn("diff", data)
            self.assertNotIn("routePatch", data)


if __name__ == "__main__":
    unittest.main()
