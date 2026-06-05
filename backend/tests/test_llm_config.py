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
    platform_health,
)
from backend.llm_client import call_llm_for_intent
from backend.intent_parser import parse_intent


ROOT = Path(__file__).resolve().parents[2]


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
        self.assertEqual(set(response["routeData"]), {"constraints", "places", "route", "diff"})
        self.assertNotIn("routePatch", response["routeData"])

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
        self.assertEqual(set(response["routeData"]), {"constraints", "places", "route", "diff"})
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

    def test_cors_allows_local_vite_and_frontend_origin(self) -> None:
        with patch.dict("os.environ", {"FRONTEND_ORIGIN": "https://frontend.example.com"}, clear=False):
            origins = _allowed_origins()
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://localhost:4173", origins)
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
