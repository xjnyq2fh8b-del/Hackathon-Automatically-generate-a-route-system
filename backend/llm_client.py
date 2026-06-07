from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional when env vars are injected by platform
    load_dotenv = None


TRUE_VALUES = {"1", "true", "yes", "on"}
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_COMPLETION_TOKENS = 500
ROOT_DIR = Path(__file__).resolve().parents[1]

if load_dotenv:
    load_dotenv(ROOT_DIR / ".env")
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
  "strategy": "default",
  "mealFirst": false,
  "preferRest": false,
  "preferIndoor": false,
  "preferLessWalking": false,
  "preferProperDinner": false,
  "preferShopping": false,
  "preferSnack": false,
  "preferClassicScenic": false,
  "weather": null
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

支持的 adjustmentType 只有：restaurantBusy、budget100、noCoffee、twoHours、photo、null。
餐厅排队太久或换一家餐厅对应 restaurantBusy。
预算降到100以内对应 budget100。
不想喝咖啡对应 noCoffee。
只剩2小时对应 twoHours。
想更适合拍照对应 photo。
用户表达“不要/不想/去掉/删除”时，否定词优先于关键词。
不想吃饭、不吃饭、不要餐饮、去掉餐厅、删除餐厅：
{
  "intent": "adjustRoute",
  "adjustmentType": null,
  "targetNodeType": "food",
  "constraintsPatch": {
    "excludeCategories": ["food"],
    "avoidTypes": ["coffee", "dinner", "snack"],
    "includeMeal": false,
    "mealFirst": false,
    "preferProperDinner": false,
    "preferSnack": false
  }
}
不想拍照、不去拍照点、去掉拍照：
{
  "intent": "adjustRoute",
  "adjustmentType": null,
  "targetNodeType": "photo",
  "constraintsPatch": {
    "excludeCategories": ["photo"],
    "avoidTypes": ["photo"],
    "preferPhoto": false
  }
}

如果用户是第一次描述出行需求，优先输出 createRoute，并把自然语言转成偏好字段：
饿了、先吃饭、饭点、先找吃的 -> mealFirst true。
想吃好一点、杭帮菜、正餐、正式吃饭 -> preferProperDinner true。
休息一下、坐一会儿、找个地方歇 -> preferRest true。
下雨、太热、太冷、室内 -> preferIndoor true，并在下雨时 weather 为 rain。
老人、小孩、少走路、走不动、累了 -> preferLessWalking true，并保留 companions。
逛街、商场、买东西、购物 -> preferShopping true。
小吃、随便吃点、快点吃、便宜吃 -> preferSnack true。
经典西湖、断桥、白堤、必打卡 -> preferClassicScenic true。"""


@dataclass(frozen=True, repr=False)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    provider: str
    enabled: bool
    timeout_seconds: int
    max_completion_tokens: int

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
        timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
        max_completion_tokens=_env_int("LLM_MAX_COMPLETION_TOKENS", DEFAULT_MAX_COMPLETION_TOKENS),
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
        "max_tokens": config.max_completion_tokens,
        "max_completion_tokens": config.max_completion_tokens,
    }

    try:
        response_data = _post_chat_completions(config, payload)
        return _extract_message_content(response_data)
    except (OSError, TimeoutError, ValueError, KeyError, TypeError, error.URLError, error.HTTPError, json.JSONDecodeError):
        return None


def _env_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


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
    with request.urlopen(req, timeout=config.timeout_seconds) as response:
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
