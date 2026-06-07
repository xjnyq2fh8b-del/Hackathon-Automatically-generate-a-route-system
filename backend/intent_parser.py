from __future__ import annotations

import json
import re
from typing import Any

from backend import llm_client


SUPPORTED_ADJUSTMENTS = {"restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"}
SUPPORTED_INTENTS = {"createRoute", "adjustRoute"}
FOOD_EXCLUDE_CATEGORY = "food"
PHOTO_EXCLUDE_CATEGORY = "photo"


def parse_intent(message: str, currentRoute: dict | None = None) -> dict[str, Any]:
    llm_intent = _try_llm_intent(message, currentRoute)
    if llm_intent:
        return llm_intent
    return parse_intent_with_rules(message)


def parse_intent_with_rules(message: str) -> dict[str, Any]:
    text = (message or "").lower()
    wants_no_food = _contains_any(
        text,
        [
            "不想吃饭",
            "不吃饭",
            "不要餐饮",
            "去掉吃饭",
            "删除餐厅",
            "去掉餐厅",
            "不要吃饭",
            "不用吃饭",
            "不安排吃饭",
            "不安排餐厅",
            "不想用餐",
            "不要美食",
            "no food",
            "no restaurant",
        ],
    )
    wants_no_photo = _contains_any(
        text,
        [
            "不想拍照",
            "不拍照",
            "不要拍照",
            "不去拍照",
            "不去拍照点",
            "去掉拍照",
            "删除拍照",
            "不要拍照点",
            "no photo",
        ],
    )
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
    wants_shopping = _contains_any(text, ["逛街", "商场", "买东西", "购物", "逛商场", "湖滨银泰", "嘉里中心"])
    wants_snack = _contains_any(text, ["小吃", "随便吃点", "吃点小吃", "快点吃", "便宜吃", "简单吃"])
    wants_classic_scenic = _contains_any(text, ["经典西湖", "断桥", "白堤", "必打卡", "经典景点", "西湖经典"])
    has_elder = _contains_any(text, ["老人", "老年人", "长辈", "爸妈", "父母"])
    has_child = _contains_any(text, ["小孩", "孩子", "带娃", "亲子", "儿童"])

    constraints_patch: dict[str, Any] = {}
    if wants_budget100:
        constraints_patch["budgetMax"] = 100
    if wants_no_food:
        constraints_patch["excludeCategories"] = [FOOD_EXCLUDE_CATEGORY]
        constraints_patch["avoidTypes"] = ["coffee", "dinner", "snack"]
        constraints_patch["includeMeal"] = False
        constraints_patch["mealFirst"] = False
        constraints_patch["preferProperDinner"] = False
        constraints_patch["preferSnack"] = False
    if wants_no_photo:
        constraints_patch["excludeCategories"] = [PHOTO_EXCLUDE_CATEGORY]
        constraints_patch["avoidTypes"] = ["photo"]
        constraints_patch["preferPhoto"] = False
    if wants_no_coffee:
        constraints_patch["avoidTypes"] = ["coffee"]
    if wants_low_wait:
        constraints_patch["preferLowWait"] = True
    if wants_two_hours:
        constraints_patch["durationMinutes"] = 120
    if wants_photo and not wants_no_photo:
        constraints_patch["preferPhoto"] = True
    if wants_meal_first and not wants_no_food:
        constraints_patch["mealFirst"] = True
    if wants_proper_dinner and not wants_no_food:
        constraints_patch["preferProperDinner"] = True
    if wants_rest:
        constraints_patch["preferRest"] = True
    if wants_indoor:
        constraints_patch["preferIndoor"] = True
    if "下雨" in text or "雨天" in text or "避雨" in text:
        constraints_patch["weather"] = "rain"
    if wants_less_walking:
        constraints_patch["preferLessWalking"] = True
    if wants_shopping:
        constraints_patch["preferShopping"] = True
    if wants_snack and not wants_no_food:
        constraints_patch["preferSnack"] = True
    if wants_classic_scenic:
        constraints_patch["preferClassicScenic"] = True
    start_time = _extract_start_time(text)
    if start_time:
        constraints_patch["startTime"] = start_time
    companions = []
    if has_elder:
        companions.append("elder")
    if has_child:
        companions.append("child")
    if companions:
        constraints_patch["companions"] = sorted(set(companions))

    adjustment_type = None

    if wants_no_food or wants_no_photo:
        adjustment_type = None
    elif wants_two_hours:
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
        "intent": "adjustRoute" if adjustment_type or wants_no_food or wants_no_photo else "createRoute",
        "adjustmentType": adjustment_type,
        "constraintsPatch": constraints_patch,
        "rawText": message or "",
    }


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _extract_start_time(text: str) -> str | None:
    match = re.search(r"(下午|晚上|中午|上午|早上)?\s*(\d{1,2}|一|二|两|三|四|五|六|七|八|九|十|十一|十二)\s*[点:：]\s*(\d{1,2})?", text)
    if not match:
        return None
    period, hour_text, minute_text = match.groups()
    if not period and not hour_text.isdigit():
        return None
    hour = _parse_hour(hour_text)
    if hour is None:
        return None
    minute = int(minute_text) if minute_text else 0
    if minute < 0 or minute > 59:
        return None
    if period in {"下午", "晚上"} and hour < 12:
        hour += 12
    if period == "中午" and hour < 11:
        hour += 12
    if hour < 0 or hour > 23:
        return None
    return f"{hour:02d}:{minute:02d}"


def _parse_hour(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    chinese_hours = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "十一": 11,
        "十二": 12,
    }
    return chinese_hours.get(value)


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
    constraints_patch = response.get("constraintsPatch")
    constraints_patch = constraints_patch if isinstance(constraints_patch, dict) else {}
    if adjustment_type is None and constraints_patch.get("excludeCategories"):
        pass
    elif adjustment_type not in SUPPORTED_ADJUSTMENTS:
        return None
    return {
        "intent": "adjustRoute",
        "adjustmentType": adjustment_type,
        "targetNodeType": response.get("targetNodeType"),
        "constraintsPatch": constraints_patch,
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
    for key in ("mealFirst", "preferRest", "preferIndoor", "preferLessWalking", "preferProperDinner", "preferShopping", "preferSnack", "preferClassicScenic"):
        if isinstance(response.get(key), bool):
            result[key] = response[key]
    weather = response.get("weather")
    if isinstance(weather, str) and weather:
        result["weather"] = weather
    return result
