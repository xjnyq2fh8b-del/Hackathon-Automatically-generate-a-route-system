from __future__ import annotations

import json
from typing import Any

from backend import llm_client


SUPPORTED_ADJUSTMENTS = {"restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"}
SUPPORTED_INTENTS = {"createRoute", "adjustRoute"}


def parse_intent(message: str, currentRoute: dict | None = None) -> dict[str, Any]:
    llm_intent = _try_llm_intent(message, currentRoute)
    if llm_intent:
        return llm_intent
    return parse_intent_with_rules(message)


def parse_intent_with_rules(message: str) -> dict[str, Any]:
    text = (message or "").lower()
    wants_no_coffee = _contains_any(text, ["不想喝咖啡", "不要咖啡", "不喝咖啡", "不想咖啡", "换个休息点", "换一个休息点", "no coffee"])
    wants_budget100 = _contains_any(text, ["预算100", "100以内", "100内", "降到100", "便宜点", "省钱一点", "省钱", "太贵了", "预算", "budget"])
    wants_low_wait = _contains_any(text, ["排队太久", "少排队", "人少点", "换一家餐厅", "餐厅太挤", "餐厅排队", "等位", "queue", "busy"])
    wants_two_hours = _contains_any(text, ["只剩2小时", "只剩两小时", "两小时内", "2小时内", "时间不够", "快一点", "2小时", "两小时", "two hours"])
    wants_photo = _contains_any(text, ["拍照", "出片", "适合拍照", "好看一点", "风景好", "photo"])
    wants_meal_first = _contains_any(text, ["饿了", "先吃饭", "先找吃", "先吃点", "饭点", "吃饭优先", "先用餐"])
    wants_proper_dinner = _contains_any(text, ["吃好一点", "吃好点", "杭帮菜", "正餐", "正式吃饭", "像样点", "不要快餐"])
    wants_rest = _contains_any(text, ["休息一下", "坐一会", "坐一下", "歇一会", "找个地方休息", "想休息", "走累了"])
    wants_indoor = _contains_any(text, ["下雨", "雨天", "室内", "太热", "太冷", "避雨", "有遮挡"])
    wants_less_walking = _contains_any(text, ["少走路", "别走太多", "不要走太久", "走不动", "老人", "老年人", "小孩", "孩子", "带娃", "亲子", "累了"])
    has_elder = _contains_any(text, ["老人", "老年人", "长辈", "爸妈", "父母"])
    has_child = _contains_any(text, ["小孩", "孩子", "带娃", "亲子", "儿童"])

    constraints_patch: dict[str, Any] = {}
    if wants_budget100:
        constraints_patch["budgetMax"] = 100
    if wants_no_coffee:
        constraints_patch["avoidTypes"] = ["coffee"]
    if wants_low_wait:
        constraints_patch["preferLowWait"] = True
    if wants_two_hours:
        constraints_patch["durationMinutes"] = 120
    if wants_photo:
        constraints_patch["preferPhoto"] = True
    if wants_meal_first:
        constraints_patch["mealFirst"] = True
    if wants_proper_dinner:
        constraints_patch["preferProperDinner"] = True
    if wants_rest:
        constraints_patch["preferRest"] = True
    if wants_indoor:
        constraints_patch["preferIndoor"] = True
    if "下雨" in text or "雨天" in text or "避雨" in text:
        constraints_patch["weather"] = "rain"
    if wants_less_walking:
        constraints_patch["preferLessWalking"] = True
    companions = []
    if has_elder:
        companions.append("elder")
    if has_child:
        companions.append("child")
    if companions:
        constraints_patch["companions"] = sorted(set(companions))

    adjustment_type = None

    if wants_two_hours:
        adjustment_type = "twoHours"
    elif wants_no_coffee:
        adjustment_type = "noCoffee"
    elif wants_budget100:
        adjustment_type = "budget100"
    elif wants_photo:
        adjustment_type = "photo"
    elif wants_low_wait:
        adjustment_type = "restaurantBusy"

    return {
        "source": "rules",
        "intent": "adjustRoute" if adjustment_type else "createRoute",
        "adjustmentType": adjustment_type,
        "constraintsPatch": constraints_patch,
        "rawText": message or "",
    }


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _try_llm_intent(message: str, currentRoute: dict | None) -> dict[str, Any] | None:
    try:
        response = llm_client.call_llm_for_intent(message, currentRoute=currentRoute)
    except Exception:
        return None

    intent = _coerce_intent(response)
    if not intent:
        return None
    intent["source"] = "llm"
    return intent


def _coerce_intent(response: str | dict | None) -> dict[str, Any] | None:
    if response is None:
        return None
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            return None
    if not isinstance(response, dict):
        return None

    intent = response.get("intent")
    if intent not in SUPPORTED_INTENTS:
        return None
    if intent == "adjustRoute":
        return _coerce_adjust_route(response)
    return _coerce_create_route(response)


def _coerce_adjust_route(response: dict[str, Any]) -> dict[str, Any] | None:
    adjustment_type = response.get("adjustmentType")
    if adjustment_type not in SUPPORTED_ADJUSTMENTS:
        return None
    constraints_patch = response.get("constraintsPatch")
    return {
        "intent": "adjustRoute",
        "adjustmentType": adjustment_type,
        "targetNodeType": response.get("targetNodeType"),
        "constraintsPatch": constraints_patch if isinstance(constraints_patch, dict) else {},
    }


def _coerce_create_route(response: dict[str, Any]) -> dict[str, Any] | None:
    preferences = response.get("preferences")
    if not isinstance(preferences, list):
        return None

    budget_max = response.get("budgetMax")
    if not isinstance(budget_max, (int, float)) or isinstance(budget_max, bool):
        budget_max = None

    time_window = response.get("timeWindow")
    avoid = response.get("avoid")
    result = {
        "intent": "createRoute",
        "origin": response.get("origin"),
        "timeWindow": time_window if isinstance(time_window, dict) else {},
        "budgetMax": budget_max,
        "companions": response.get("companions"),
        "preferences": preferences,
        "avoid": avoid if isinstance(avoid, list) else [],
        "strategy": response.get("strategy") or "default",
    }
    for key in ("mealFirst", "preferRest", "preferIndoor", "preferLessWalking", "preferProperDinner"):
        if isinstance(response.get(key), bool):
            result[key] = response[key]
    weather = response.get("weather")
    if isinstance(weather, str) and weather:
        result["weather"] = weather
    return result
