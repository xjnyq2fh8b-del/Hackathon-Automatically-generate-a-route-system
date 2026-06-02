from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


TRUE_VALUES = {"1", "true", "yes", "on"}
DEFAULT_TIMEOUT_SECONDS = 20
SYSTEM_PROMPT = """你是本地路线 Agent 的意图解析器。
你只输出 JSON。
不要输出 Markdown。
不要输出解释。
不要生成路线。
不要编造 POI。
不要计算距离。
不要判断真实营业时间。
只把用户输入解析为 createRoute 或 adjustRoute。

createRoute 输出格式：
{
  "intent": "createRoute",
  "origin": "湖滨银泰 in77",
  "timeWindow": {
    "start": "now",
    "end": null,
    "durationMinutes": 180
  },
  "budgetMax": 150,
  "companions": "friends",
  "preferences": ["scenic", "coffee", "dinner", "low_wait"],
  "avoid": [],
  "strategy": "default"
}

adjustRoute 输出格式：
{
  "intent": "adjustRoute",
  "adjustmentType": "restaurantBusy",
  "targetNodeType": "dinner",
  "constraintsPatch": {
    "waitRisk": "lower"
  }
}

支持的 adjustmentType 只有：restaurantBusy、budget100、noCoffee、twoHours、photo。
餐厅排队太久或换一家餐厅对应 restaurantBusy。
预算降到100以内对应 budget100。
不想喝咖啡对应 noCoffee。
只剩2小时对应 twoHours。
想更适合拍照对应 photo。"""


@dataclass(frozen=True, repr=False)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    provider: str
    enabled: bool

    @property
    def is_ready(self) -> bool:
        return self.enabled and bool(self.api_key and self.base_url and self.model)


def load_llm_config() -> LLMConfig:
    return LLMConfig(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", ""),
        model=os.getenv("LLM_MODEL", ""),
        provider=os.getenv("LLM_PROVIDER", "openai_compatible"),
        enabled=_env_enabled(os.getenv("LLM_ENABLED", "false")),
    )


def get_llm_status() -> dict[str, str | bool]:
    config = load_llm_config()
    if not config.enabled:
        return {"enabled": False, "reason": "disabled"}
    if not config.api_key:
        return {"enabled": False, "reason": "missing_api_key"}
    if not config.base_url:
        return {"enabled": False, "reason": "missing_base_url"}
    if not config.model:
        return {"enabled": False, "reason": "missing_model"}
    return {"enabled": True, "provider": config.provider}


def call_llm_for_intent(message: str, currentRoute: dict | None = None) -> str | dict | None:
    config = load_llm_config()
    if not config.is_ready:
        return None

    if config.provider != "openai_compatible":
        return None

    payload = {
        "model": config.model,
        "messages": _build_messages(message, currentRoute),
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        response_data = _post_chat_completions(config, payload)
        return _extract_message_content(response_data)
    except (OSError, TimeoutError, ValueError, KeyError, TypeError, error.URLError, error.HTTPError, json.JSONDecodeError):
        return None


def _env_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUE_VALUES


def _build_messages(message: str, currentRoute: dict | None) -> list[dict[str, str]]:
    user_content = message or ""
    if currentRoute:
        route_summary = {
            "placeIds": currentRoute.get("placeIds", []),
            "durationMinutes": currentRoute.get("durationMinutes"),
            "budgetPerPerson": currentRoute.get("budgetPerPerson"),
            "waitRisk": currentRoute.get("waitRisk"),
        }
        user_content = f"{user_content}\n\n当前路线摘要：{json.dumps(route_summary, ensure_ascii=False)}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _post_chat_completions(config: LLMConfig, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        _chat_completions_url(config.base_url),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _chat_completions_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/chat/completions"


def _extract_message_content(response_data: dict[str, Any]) -> str | dict | None:
    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if content:
        return content
    return message.get("reasoning_content")
