from __future__ import annotations

import json
import time
import unittest
from pathlib import Path

import backend.app as app_module
from backend.app import AdjustRequest, TextRequest, adjust_route, generate_route
from backend.poi_catalog import calculate_route_budget
from backend.route_planner import generate_adjusted_route, generate_default_route, generate_route_for_constraints


ROOT = Path(__file__).resolve().parents[2]
ROUTE_DATA_KEYS = {"constraints", "places", "route", "diff", "message", "adjustmentButtons"}


def catalog() -> list[dict]:
    with (ROOT / "data" / "poiCatalog.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def route_data_for(adjustment_type: str | None = None) -> dict:
    if adjustment_type is None:
        return generate_route(TextRequest(text="test"))["routeData"]
    return adjust_route(AdjustRequest(adjustmentType=adjustment_type))["routeData"]


def place_by_id(route_data: dict) -> dict[str, dict]:
    return {place["id"]: place for place in route_data["places"]}


def assert_route_shape(testcase: unittest.TestCase, route_data: dict) -> None:
    testcase.assertEqual(set(route_data), ROUTE_DATA_KEYS)
    testcase.assertNotIn("routePatch", route_data)
    testcase.assertIsInstance(route_data["message"], str)
    testcase.assertTrue(route_data["adjustmentButtons"])
    route = route_data["route"]
    place_ids = route["placeIds"]
    places = place_by_id(route_data)
    testcase.assertGreaterEqual(len(place_ids), 3)
    testcase.assertLessEqual(len(place_ids), 5)
    testcase.assertEqual(set(place_ids), set(places))
    testcase.assertEqual([item["placeId"] for item in route["timeline"]], place_ids)
    testcase.assertEqual(len(route["transportSegments"]), max(0, len(place_ids) - 1))
    for segment, from_id, to_id in zip(route["transportSegments"], place_ids, place_ids[1:]):
        testcase.assertEqual(segment["fromId"], from_id)
        testcase.assertEqual(segment["toId"], to_id)
        testcase.assertIn("duration", segment)
    testcase.assertIsInstance(route["budgetPerPerson"], (int, float))
    testcase.assertIsInstance(route["durationMinutes"], int)
    testcase.assertIsInstance(route["walkingKm"], (int, float))


class RoutePlannerApiTest(unittest.TestCase):
    def test_default_route_uses_poi_catalog_not_legacy_mock(self) -> None:
        data = route_data_for()
        assert_route_shape(self, data)
        self.assertIn("start_in77_hubin", data["route"]["placeIds"])
        self.assertNotIn("in77", data["route"]["placeIds"])

    def test_all_adjustments_return_full_route_and_diff(self) -> None:
        for adjustment_type in ["restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"]:
            with self.subTest(adjustment_type=adjustment_type):
                data = route_data_for(adjustment_type)
                assert_route_shape(self, data)
                self.assertIsInstance(data["diff"], dict)
                self.assertTrue(data["diff"]["rows"])

    def test_restaurant_busy_only_replaces_dinner_node(self) -> None:
        default_ids = route_data_for()["route"]["placeIds"]
        adjusted_ids = route_data_for("restaurantBusy")["route"]["placeIds"]
        self.assertEqual(default_ids[:3], adjusted_ids[:3])
        self.assertNotEqual(default_ids[3], adjusted_ids[3])
        self.assertEqual(place_by_id(route_data_for("restaurantBusy"))[adjusted_ids[3]]["type"], "dinner")

    def test_budget100_lowers_or_controls_budget_near_100(self) -> None:
        default_budget = route_data_for()["route"]["budgetPerPerson"]
        adjusted_budget = route_data_for("budget100")["route"]["budgetPerPerson"]
        self.assertLessEqual(adjusted_budget, default_budget)
        self.assertLessEqual(adjusted_budget, 100)

    def test_default_route_prefers_full_dinner_over_snack_dinner(self) -> None:
        planned = generate_default_route(catalog())
        dinner = next(poi for poi in planned["selectedPois"] if poi["type"] == "dinner")
        self.assertNotIn("snack", dinner["experienceTags"])

    def test_create_route_food_preferences_pick_different_food_nodes(self) -> None:
        data = catalog()
        default_route = generate_default_route(data)
        proper_route = generate_route_for_constraints(data, {"preferProperDinner": True})
        proper_dinner = next(
            poi
            for poi in proper_route["selectedPois"]
            if poi["type"] == "dinner"
        )
        snack_node = next(
            poi
            for poi in generate_route_for_constraints(data, {"preferSnack": True})["selectedPois"]
            if poi["type"] == "snack"
        )
        self.assertNotEqual(default_route["route"]["placeIds"], proper_route["route"]["placeIds"])
        self.assertNotIn("snack", proper_dinner["experienceTags"])
        self.assertIn("local-cuisine", proper_dinner["experienceTags"])
        self.assertIn("snack", snack_node["experienceTags"])

    def test_meal_first_avoids_closed_split_shift_restaurant(self) -> None:
        planned = generate_route_for_constraints(catalog(), {"mealFirst": True, "startTime": "15:00"})
        dinner = next(poi for poi in planned["selectedPois"] if poi["type"] == "dinner")
        self.assertNotEqual(dinner["id"], "dinner_xinbailu_hubin88")
        self.assertEqual(planned["route"]["timeline"][0]["arrive"], "15:00")

    def test_closed_status_uses_open_hours_text_when_structured_hours_missing(self) -> None:
        data = catalog()
        xinbailu = next(poi for poi in data if poi["id"] == "dinner_xinbailu_hubin88")
        self.assertEqual(xinbailu["openingHours"], [])
        planned = generate_route_for_constraints(data, {"mealFirst": True, "startTime": "15:00"})
        self.assertNotIn("dinner_xinbailu_hubin88", planned["route"]["placeIds"])

    def test_no_coffee_route_contains_no_coffee_type(self) -> None:
        data = route_data_for("noCoffee")
        types = [place["type"] for place in data["places"]]
        self.assertNotIn("coffee", types)

    def test_two_hours_removes_buffer_and_shortens_duration(self) -> None:
        default = route_data_for()
        adjusted = route_data_for("twoHours")
        self.assertLess(len(adjusted["route"]["placeIds"]), len(default["route"]["placeIds"]))
        self.assertLessEqual(adjusted["route"]["durationMinutes"], 120)

    def test_timeline_stay_minutes_are_clamped_by_place_type(self) -> None:
        planned = generate_route_for_constraints(catalog(), {"preferProperDinner": True})
        places = {poi["id"]: poi for poi in planned["selectedPois"]}
        for item in planned["route"]["timeline"]:
            poi = places[item["placeId"]]
            arrive_hour, arrive_minute = [int(part) for part in item["arrive"].split(":")]
            leave_hour, leave_minute = [int(part) for part in item["leave"].split(":")]
            stay = (leave_hour * 60 + leave_minute) - (arrive_hour * 60 + arrive_minute)
            if poi["type"] == "start":
                self.assertLessEqual(stay, 5)
            if poi["type"] == "dinner":
                self.assertGreaterEqual(stay, 50)
                self.assertLessEqual(stay, 75)

    def test_photo_route_prefers_high_photo_score_node(self) -> None:
        planned = generate_adjusted_route("photo", catalog())
        photo_poi = next(poi for poi in planned["selectedPois"] if poi["type"] == "photo")
        self.assertGreaterEqual(photo_poi["photoScore"], 4)

    def test_budget_recalculation_matches_selected_pois(self) -> None:
        for adjustment_type in [None, "restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"]:
            planned = generate_default_route(catalog()) if adjustment_type is None else generate_adjusted_route(adjustment_type, catalog())
            route_nodes = [
                {"placeId": poi["id"], "role": "start" if poi["type"] == "start" else poi["type"], "type": poi["type"]}
                for poi in planned["selectedPois"]
            ]
            self.assertEqual(planned["route"]["budgetPerPerson"], calculate_route_budget(route_nodes, planned["selectedPois"]))

    def test_empty_opening_hours_does_not_hard_filter_candidates(self) -> None:
        data = catalog()
        self.assertTrue(any(not poi["openingHours"] for poi in data))
        planned = generate_default_route(data)
        self.assertTrue(planned["route"]["placeIds"])

    def test_missing_catalog_still_falls_back_to_mock_route(self) -> None:
        original_loaded = app_module.POI_CATALOG_LOADED
        try:
            app_module.POI_CATALOG_LOADED = False
            data = route_data_for()
            self.assertIn("in77", data["route"]["placeIds"])
            self.assertEqual(set(data), ROUTE_DATA_KEYS)
        finally:
            app_module.POI_CATALOG_LOADED = original_loaded

    def test_route_api_calls_finish_under_ten_seconds(self) -> None:
        for adjustment_type in [None, "restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"]:
            with self.subTest(adjustment_type=adjustment_type or "default"):
                start = time.perf_counter()
                route_data_for(adjustment_type)
                elapsed = time.perf_counter() - start
                self.assertLess(elapsed, 10)


if __name__ == "__main__":
    unittest.main()
