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
    adjustment_type = None

    if any(keyword in text for keyword in ["排队", "等位", "queue", "busy"]):
        adjustment_type = "restaurantBusy"
    elif any(keyword in text for keyword in ["100", "预算", "便宜", "省钱", "budget"]):
        adjustment_type = "budget100"
    elif any(keyword in text for keyword in ["不要咖啡", "不喝咖啡", "不想喝咖啡", "no coffee"]):
        adjustment_type = "noCoffee"
    elif any(keyword in text for keyword in ["2小时", "两小时", "two hours"]):
        adjustment_type = "twoHours"
    elif any(keyword in text for keyword in ["拍照", "出片", "photo"]):
        adjustment_type = "photo"

    return {
        "source": "rules",
        "intent": "adjustRoute" if adjustment_type else "createRoute",
        "adjustmentType": adjustment_type,
        "rawText": message or "",
    }


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
    return {
        "intent": "createRoute",
        "origin": response.get("origin"),
        "timeWindow": time_window if isinstance(time_window, dict) else {},
        "budgetMax": budget_max,
        "companions": response.get("companions"),
        "preferences": preferences,
        "avoid": avoid if isinstance(avoid, list) else [],
        "strategy": response.get("strategy") or "default",
    }
