from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app import TextRequest, chat_route, generate_route
from backend.intent_parser import parse_intent


ROOT = Path(__file__).resolve().parents[2]


class LLMConfigTest(unittest.TestCase):
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

    def test_chat_route_survives_llm_request_failure(self) -> None:
        with patch("backend.llm_client.call_llm_for_intent", side_effect=RuntimeError("llm failed")):
            response = chat_route(TextRequest(text="只剩两小时"))
        self.assertIn("routeData", response)
        self.assertIn("route", response["routeData"])

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
        self.assertIn("LLM_API_KEY=\n", content)
        self.assertIn("LLM_BASE_URL=\n", content)
        self.assertIn("LLM_MODEL=\n", content)
        self.assertIn("LLM_PROVIDER=openai_compatible\n", content)
        self.assertIn("LLM_ENABLED=false\n", content)
        self.assertNotIn("sk-", content)


if __name__ == "__main__":
    unittest.main()
