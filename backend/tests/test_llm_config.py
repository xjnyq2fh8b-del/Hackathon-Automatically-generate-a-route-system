from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.app import (
    CHAT_ROUTE_REQUESTS,
    LLM_DAILY_REQUESTS,
    TextRequest,
    _enforce_chat_route_rate_limit,
    _enforce_daily_llm_limit,
    _enforce_demo_token,
    _enforce_message_length,
    _allowed_origins,
    chat_route,
    generate_route,
    llm_status,
    platform_health,
)
from backend.llm_client import call_llm_for_intent
from backend.intent_parser import parse_intent


ROOT = Path(__file__).resolve().parents[2]
ROUTE_DATA_KEYS = {"constraints", "places", "optimizedPlaces", "route", "diff", "debug", "message", "adjustmentButtons"}


class LLMConfigTest(unittest.TestCase):
    def test_llm_disabled_does_not_call_model(self) -> None:
        with patch.dict("os.environ", {"LLM_ENABLED": "false", "LLM_API_KEY": "test-secret"}, clear=True):
            with patch("backend.llm_client._post_chat_completions") as post_chat:
                self.assertIsNone(call_llm_for_intent("预算降到100"))
        post_chat.assert_not_called()

    def test_missing_llm_api_key_returns_none_without_calling_model(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "LLM_ENABLED": "true",
                "LLM_BASE_URL": "https://token-plan-cn.xiaomimimo.com/v1",
                "LLM_MODEL": "mimo-v2.5-pro",
            },
            clear=True,
        ):
            with patch("backend.llm_client._post_chat_completions") as post_chat:
                self.assertIsNone(call_llm_for_intent("预算降到100"))
        post_chat.assert_not_called()

    def test_missing_llm_api_key_uses_rules_fallback(self) -> None:
        with patch.dict("os.environ", {"LLM_ENABLED": "true"}, clear=True):
            intent = parse_intent("餐厅排队太久，帮我换一个")
        self.assertEqual(intent["source"], "rules")
        self.assertEqual(intent["adjustmentType"], "restaurantBusy")

    def test_llm_disabled_uses_rules_fallback(self) -> None:
        with patch.dict("os.environ", {"LLM_ENABLED": "false", "LLM_API_KEY": "test-secret"}, clear=True):
            intent = parse_intent("预算降到100")
        self.assertEqual(intent["source"], "rules")
        self.assertEqual(intent["adjustmentType"], "budget100")

    def test_invalid_llm_json_uses_rules_fallback(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value="{invalid json"):
            intent = parse_intent("不要咖啡")
        self.assertEqual(intent["source"], "rules")
        self.assertEqual(intent["adjustmentType"], "noCoffee")

    def test_real_http_client_reads_openai_style_chat_completion(self) -> None:
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "intent": "adjustRoute",
                                "adjustmentType": "photo",
                                "targetNodeType": "scenic",
                                "constraintsPatch": {},
                            }
                        )
                    }
                }
            ]
        }
        with patch.dict(
            "os.environ",
            {
                "LLM_ENABLED": "true",
                "LLM_API_KEY": "test-secret",
                "LLM_BASE_URL": "https://token-plan-cn.xiaomimimo.com/v1",
                "LLM_MODEL": "mimo-v2.5-pro",
                "LLM_PROVIDER": "openai_compatible",
            },
            clear=True,
        ):
            with patch("backend.llm_client._post_chat_completions", return_value=response) as post_chat:
                content = call_llm_for_intent("想更适合拍照")
        self.assertIn('"adjustmentType": "photo"', content)
        post_chat.assert_called_once()
        payload = post_chat.call_args.args[1]
        self.assertEqual(payload["max_tokens"], 500)
        self.assertEqual(payload["max_completion_tokens"], 500)

    def test_llm_valid_create_route_json_keeps_chat_route_shape(self) -> None:
        llm_json = json.dumps(
            {
                "intent": "createRoute",
                "origin": "湖滨银泰 in77",
                "timeWindow": {"start": "now", "end": None, "durationMinutes": 180},
                "budgetMax": 150,
                "companions": "friends",
                "preferences": ["scenic", "coffee", "dinner", "low_wait"],
                "avoid": [],
                "strategy": "default",
            },
            ensure_ascii=False,
        )
        with patch("backend.llm_client.call_llm_for_intent", return_value=llm_json):
            response = chat_route(TextRequest(text="下午想逛西湖喝咖啡吃晚饭"))
        self.assertEqual(set(response["routeData"]), ROUTE_DATA_KEYS)
        self.assertNotIn("routePatch", response["routeData"])

    def test_generate_route_uses_llm_create_route_constraints(self) -> None:
        llm_json = json.dumps(
            {
                "intent": "createRoute",
                "origin": "湖滨银泰 in77",
                "timeWindow": {"start": "14:00", "end": "18:00", "durationMinutes": 180},
                "budgetMax": 120,
                "companions": ["elder", "child"],
                "preferences": ["rest", "less_walking"],
                "avoid": [],
                "strategy": "default",
                "preferRest": True,
                "preferLessWalking": True,
            },
            ensure_ascii=False,
        )
        with patch("backend.llm_client.call_llm_for_intent", return_value=llm_json):
            route_data = generate_route(TextRequest(text="带老人小孩看西湖，不想走太多路"))["routeData"]
        self.assertEqual(route_data["route"]["name"], "轻松休息友好线")
        self.assertTrue(route_data["constraints"]["preferRest"])
        self.assertTrue(route_data["constraints"]["preferLessWalking"])
        self.assertEqual(route_data["constraints"]["budgetMax"], 120)

    def test_llm_valid_adjust_route_json_triggers_adjustment(self) -> None:
        llm_json = json.dumps(
            {
                "intent": "adjustRoute",
                "adjustmentType": "restaurantBusy",
                "targetNodeType": "dinner",
                "constraintsPatch": {"waitRisk": "lower"},
            },
            ensure_ascii=False,
        )
        with patch("backend.llm_client.call_llm_for_intent", return_value=llm_json):
            response = chat_route(TextRequest(text="餐厅排队太久，换一家"))
        self.assertEqual(set(response["routeData"]), ROUTE_DATA_KEYS)
        self.assertIsInstance(response["routeData"]["diff"], dict)
        self.assertNotIn("routePatch", response["routeData"])

    def test_five_adjustment_phrases_parse_to_supported_types(self) -> None:
        cases = {
            "餐厅排队太久，换一家": "restaurantBusy",
            "预算降到100以内": "budget100",
            "不想喝咖啡了": "noCoffee",
            "只剩2小时": "twoHours",
            "想更适合拍照": "photo",
        }
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            for text, expected in cases.items():
                with self.subTest(text=text):
                    self.assertEqual(parse_intent(text)["adjustmentType"], expected)

    def test_negative_food_and_photo_phrases_parse_to_exclusions(self) -> None:
        cases = {
            "我不想吃饭": "food",
            "不吃饭了，去掉餐厅": "food",
            "我不想拍照": "photo",
            "不去拍照点": "photo",
        }
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            for text, expected_category in cases.items():
                with self.subTest(text=text):
                    intent = parse_intent(text)
                    self.assertEqual(intent["intent"], "adjustRoute")
                    self.assertIsNone(intent["adjustmentType"])
                    self.assertIn(expected_category, intent["constraintsPatch"]["excludeCategories"])
                    if expected_category == "photo":
                        self.assertFalse(intent["constraintsPatch"]["preferPhoto"])

    def test_llm_adjust_route_can_exclude_categories_without_adjustment_type(self) -> None:
        llm_json = json.dumps(
            {
                "intent": "adjustRoute",
                "adjustmentType": None,
                "targetNodeType": "food",
                "constraintsPatch": {
                    "excludeCategories": ["food"],
                    "avoidTypes": ["coffee", "dinner", "snack"],
                    "includeMeal": False,
                },
            },
            ensure_ascii=False,
        )
        with patch("backend.llm_client.call_llm_for_intent", return_value=llm_json):
            intent = parse_intent("我不想吃饭")
        self.assertEqual(intent["source"], "llm")
        self.assertEqual(intent["intent"], "adjustRoute")
        self.assertIsNone(intent["adjustmentType"])
        self.assertIn("food", intent["constraintsPatch"]["excludeCategories"])

    def test_extended_adjustment_phrases_parse_to_supported_types(self) -> None:
        cases = {
            "换个休息点": "noCoffee",
            "太贵了，省钱一点": "budget100",
            "人少点，换一家餐厅": "restaurantBusy",
            "时间不够，快一点": "twoHours",
            "风景好，好看一点": "photo",
        }
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            for text, expected in cases.items():
                with self.subTest(text=text):
                    self.assertEqual(parse_intent(text)["adjustmentType"], expected)

    def test_create_route_phrases_parse_to_constraints(self) -> None:
        cases = {
            "我饿了，想先吃饭": ("mealFirst", True),
            "想吃好一点的杭帮菜正餐": ("preferProperDinner", True),
            "我想找个地方休息一下": ("preferRest", True),
            "今天下雨，想室内少走路": ("weather", "rain"),
            "带老人小孩一起玩，少走路": ("preferLessWalking", True),
            "想逛街买东西，顺路看西湖": ("preferShopping", True),
            "想吃点小吃，便宜快点": ("preferSnack", True),
            "想去断桥白堤这种经典西湖景点": ("preferClassicScenic", True),
            "下午三点先吃饭": ("startTime", "15:00"),
        }
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            for text, (key, expected) in cases.items():
                with self.subTest(text=text):
                    intent = parse_intent(text)
                    self.assertEqual(intent["intent"], "createRoute")
                    self.assertEqual(intent["constraintsPatch"][key], expected)

    def test_time_parser_does_not_treat_degree_words_as_clock_time(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            intent = parse_intent("想吃好一点的杭帮菜正餐")
        self.assertNotIn("startTime", intent["constraintsPatch"])
        self.assertTrue(intent["constraintsPatch"]["preferProperDinner"])

    def test_chat_route_survives_llm_request_failure(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", side_effect=RuntimeError("llm failed")):
            response = chat_route(TextRequest(text="只剩两小时"))
        self.assertIn("routeData", response)
        self.assertIn("route", response["routeData"])

    def test_chat_route_accepts_message_field(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            response = chat_route(TextRequest(message="不想喝咖啡了"))
        self.assertIn("routeData", response)
        self.assertIsInstance(response["routeData"]["diff"], dict)

    def test_chat_route_returns_message_and_adjustment_buttons(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="我想找个地方休息一下"))["routeData"]
        self.assertEqual(set(route_data), ROUTE_DATA_KEYS)
        self.assertIsInstance(route_data["message"], str)
        self.assertTrue(route_data["adjustmentButtons"])

    def test_budget100_updates_constraints(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="预算降到100以内"))["routeData"]
        self.assertEqual(route_data["constraints"]["budgetMax"], 100)
        self.assertLessEqual(route_data["route"]["budgetPerPerson"], 100)

    def test_no_coffee_updates_constraints(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="不想喝咖啡了"))["routeData"]
        self.assertIn("coffee", route_data["constraints"]["avoidTypes"])
        place_types = [place["type"] for place in route_data["places"]]
        self.assertNotIn("coffee", place_types)

    def test_follow_up_no_food_removes_food_places_from_current_route(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            current = chat_route(TextRequest(message="我想现在出发逛西湖"))["routeData"]
            route_data = chat_route(
                TextRequest(
                    message="我不想吃饭",
                    currentRoute=current["route"],
                    currentPlaces=current["optimizedPlaces"],
                    currentConstraints=current["constraints"],
                )
            )["routeData"]
        self.assertIn("food", route_data["constraints"]["excludeCategories"])
        self.assertTrue(route_data["debug"]["isFollowUp"])
        self.assertTrue(route_data["debug"]["routeUpdated"])
        self.assertTrue(route_data["debug"]["removedPlaces"])
        self.assertNotIn("dinner", [place["type"] for place in route_data["places"]])
        self.assertNotIn("coffee", [place["type"] for place in route_data["places"]])

    def test_follow_up_no_photo_removes_photo_place_from_current_route(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            current = chat_route(TextRequest(message="想更适合拍照"))["routeData"]
            self.assertIn("photo", [place["type"] for place in current["places"]])
            route_data = chat_route(
                TextRequest(
                    message="我不想拍照",
                    currentRoute=current["route"],
                    currentPlaces=current["optimizedPlaces"],
                    currentConstraints=current["constraints"],
                )
            )["routeData"]
        self.assertIn("photo", route_data["constraints"]["excludeCategories"])
        self.assertFalse(route_data["constraints"]["preferPhoto"])
        self.assertTrue(route_data["debug"]["isFollowUp"])
        self.assertTrue(route_data["debug"]["routeUpdated"])
        self.assertNotIn("photo", [place["type"] for place in route_data["places"]])

    def test_chat_route_merges_active_constraints(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(
                TextRequest(
                    message="少排队",
                    activeConstraints={"budgetMax": 100},
                )
            )["routeData"]
        self.assertEqual(route_data["constraints"]["budgetMax"], 100)
        self.assertTrue(route_data["constraints"]["preferLowWait"])
        self.assertLessEqual(route_data["route"]["budgetPerPerson"], 100)

    def test_chat_route_place_ids_exist_in_places(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="想更适合拍照"))["routeData"]
        place_ids = set(route_data["route"]["placeIds"])
        response_place_ids = {place["id"] for place in route_data["places"]}
        self.assertTrue(place_ids)
        self.assertTrue(place_ids.issubset(response_place_ids))

    def test_chat_route_adjustments_change_place_ids_and_diff(self) -> None:
        messages = [
            "餐厅排队太久",
            "预算降到100以内",
            "不想喝咖啡",
            "只剩2小时",
            "想更适合拍照",
        ]
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            default_ids = chat_route(TextRequest(message="我想找个地方休息一下"))["routeData"]["route"]["placeIds"]
            for message in messages:
                with self.subTest(message=message):
                    route_data = chat_route(TextRequest(message=message))["routeData"]
                    self.assertNotEqual(default_ids, route_data["route"]["placeIds"])
                    self.assertIsInstance(route_data["diff"], dict)

    def test_create_route_strategies_change_route_without_adjustment_diff(self) -> None:
        cases = {
            "我想找个地方休息一下": "轻松休息友好线",
            "我饿了，想先吃饭": "先吃饭再逛线",
            "想吃好一点的杭帮菜正餐": "杭帮正餐体验线",
            "今天下雨，想室内少走路": "室内缓冲少走路线",
            "想逛街买东西，顺路看西湖": "湖滨逛街顺路线",
            "想吃点小吃，便宜快点": "西湖小吃轻量线",
            "想去断桥白堤这种经典西湖景点": "西湖经典打卡线",
        }
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            default_ids = chat_route(TextRequest(message="我想现在出发逛西湖"))["routeData"]["route"]["placeIds"]
            for message, expected_name in cases.items():
                with self.subTest(message=message):
                    route_data = chat_route(TextRequest(message=message))["routeData"]
                    self.assertEqual(route_data["route"]["name"], expected_name)
                    self.assertNotEqual(default_ids, route_data["route"]["placeIds"])
                    self.assertIsNone(route_data["diff"])

    def test_elder_child_and_rain_add_travel_advice(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="带老人小孩一起玩，少走路"))["routeData"]
        self.assertIn("建议必要时打车到下一站", route_data["route"]["transportSummary"])
        self.assertEqual(route_data["constraints"]["companions"], ["child", "elder"])
        self.assertTrue(route_data["constraints"]["preferLessWalking"])

    def test_constraints_chips_follow_user_input(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", return_value=None):
            route_data = chat_route(TextRequest(message="今天下雨，想室内少走路"))["routeData"]
        chips = {chip["key"]: chip["value"] for chip in route_data["constraints"]["chips"]}
        self.assertIn("室内优先", chips["偏好"])
        self.assertIn("少走路", chips["偏好"])
        self.assertEqual(chips["天气"], "下雨")

    def test_route_api_response_does_not_include_llm_api_key(self) -> None:
        secret = "sk-test-should-not-leak"
        with patch.dict("os.environ", {"LLM_ENABLED": "false", "LLM_API_KEY": secret}, clear=True):
            response = generate_route(TextRequest(text="想更适合拍照"))
        self.assertNotIn(secret, json.dumps(response, ensure_ascii=False))
        self.assertNotIn("LLM_API_KEY", json.dumps(response, ensure_ascii=False))

    def test_frontend_does_not_define_vite_llm_api_key(self) -> None:
        frontend_files = (ROOT / "frontend").glob("**/*")
        matches = []
        for path in frontend_files:
            if path.is_file() and path.suffix in {".js", ".mjs", ".html", ".css"}:
                if "VITE_LLM_API_KEY" in path.read_text(encoding="utf-8"):
                    matches.append(path)
        self.assertEqual(matches, [])

    def test_env_file_is_not_tracked(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), "")

    def test_env_example_exists_and_contains_only_safe_placeholders(self) -> None:
        env_example = ROOT / ".env.example"
        self.assertTrue(env_example.exists())
        content = env_example.read_text(encoding="utf-8")
        self.assertIn("LLM_API_KEY=your_api_key_here\n", content)
        self.assertIn("LLM_BASE_URL=your_base_url_here\n", content)
        self.assertIn("LLM_MODEL=your_model_here\n", content)
        self.assertIn("LLM_PROVIDER=openai_compatible\n", content)
        self.assertIn("LLM_ENABLED=false\n", content)
        self.assertIn("LLM_TIMEOUT_SECONDS=10\n", content)
        self.assertIn("LLM_MAX_COMPLETION_TOKENS=500\n", content)
        self.assertIn("LLM_DAILY_REQUEST_LIMIT=200\n", content)
        self.assertIn("FRONTEND_ORIGIN=https://your-frontend-domain.example\n", content)
        self.assertIn("ENABLE_DOCS=true\n", content)
        self.assertIn("CHAT_ROUTE_MAX_MESSAGE_CHARS=500\n", content)
        self.assertIn("DEMO_ACCESS_TOKEN=\n", content)
        self.assertNotIn("sk-", content)

    def test_platform_health_endpoint_payload(self) -> None:
        self.assertEqual(platform_health(), {"status": "ok"})

    def test_llm_status_endpoint_does_not_leak_secret(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "LLM_ENABLED": "true",
                "LLM_API_KEY": "sk-test-should-not-leak",
                "LLM_BASE_URL": "https://llm.example/v1",
                "LLM_MODEL": "test-model",
                "LLM_PROVIDER": "openai_compatible",
            },
            clear=True,
        ):
            status = llm_status()
        serialized = json.dumps(status, ensure_ascii=False)
        self.assertTrue(status["enabled"])
        self.assertEqual(status["provider"], "openai_compatible")
        self.assertNotIn("sk-test-should-not-leak", serialized)
        self.assertNotIn("LLM_API_KEY", serialized)

    def test_cors_allows_local_vite_and_frontend_origin(self) -> None:
        with patch.dict("os.environ", {"FRONTEND_ORIGIN": "https://frontend.example.com"}, clear=False):
            origins = _allowed_origins()
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://localhost:4173", origins)
        self.assertIn("https://cityroutemate.netlify.app", origins)
        self.assertIn("https://frontend.example.com", origins)

    def test_chat_route_rate_limit_returns_429_after_ten_requests_per_ip(self) -> None:
        CHAT_ROUTE_REQUESTS.clear()
        request = SimpleNamespace(headers={"x-forwarded-for": "203.0.113.10"}, client=SimpleNamespace(host="127.0.0.1"))
        for _ in range(10):
            _enforce_chat_route_rate_limit(request)

        with self.assertRaises(HTTPException) as error:
            _enforce_chat_route_rate_limit(request)
        self.assertEqual(error.exception.status_code, 429)
        CHAT_ROUTE_REQUESTS.clear()

    def test_health_is_not_rate_limited(self) -> None:
        CHAT_ROUTE_REQUESTS.clear()
        for _ in range(12):
            self.assertEqual(platform_health(), {"status": "ok"})
        self.assertEqual(CHAT_ROUTE_REQUESTS, {})
        CHAT_ROUTE_REQUESTS.clear()

    def test_message_length_limit_rejects_long_prompt(self) -> None:
        with patch.dict("os.environ", {"CHAT_ROUTE_MAX_MESSAGE_CHARS": "5"}, clear=False):
            with self.assertRaises(HTTPException) as error:
                _enforce_message_length("abcdef")
        self.assertEqual(error.exception.status_code, 413)

    def test_demo_token_is_optional_but_enforced_when_configured(self) -> None:
        request = SimpleNamespace(headers={"x-demo-token": "right-token"}, client=SimpleNamespace(host="127.0.0.1"))
        with patch.dict("os.environ", {}, clear=True):
            _enforce_demo_token(request)
        with patch.dict("os.environ", {"DEMO_ACCESS_TOKEN": "right-token"}, clear=True):
            _enforce_demo_token(request)
        with patch.dict("os.environ", {"DEMO_ACCESS_TOKEN": "right-token"}, clear=True):
            bad_request = SimpleNamespace(headers={"x-demo-token": "wrong-token"}, client=SimpleNamespace(host="127.0.0.1"))
            with self.assertRaises(HTTPException) as error:
                _enforce_demo_token(bad_request)
        self.assertEqual(error.exception.status_code, 403)

    def test_daily_llm_limit_returns_429_after_limit(self) -> None:
        LLM_DAILY_REQUESTS.clear()
        with patch.dict("os.environ", {"LLM_DAILY_REQUEST_LIMIT": "2"}, clear=False):
            _enforce_daily_llm_limit()
            _enforce_daily_llm_limit()
            with self.assertRaises(HTTPException) as error:
                _enforce_daily_llm_limit()
        self.assertEqual(error.exception.status_code, 429)
        LLM_DAILY_REQUESTS.clear()


if __name__ == "__main__":
    unittest.main()
