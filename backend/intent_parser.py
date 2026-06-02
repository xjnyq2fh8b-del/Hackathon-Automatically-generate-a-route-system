from __future__ import annotations

import json
from typing import Any

from backend import llm_client


SUPPORTED_ADJUSTMENTS = {"restaurantBusy", "budget100", "noCoffee", "twoHours", "photo"}


def parse_intent(message: str) -> dict[str, Any]:
    llm_intent = _try_llm_intent(message)
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
    elif any(keyword in text for keyword in ["不要咖啡", "不喝咖啡", "no coffee"]):
        adjustment_type = "noCoffee"
    elif any(keyword in text for keyword in ["2小时", "两小时", "two hours"]):
        adjustment_type = "twoHours"
    elif any(keyword in text for keyword in ["拍照", "出片", "photo"]):
        adjustment_type = "photo"

    return {
        "source": "rules",
        "adjustmentType": adjustment_type,
        "rawText": message or "",
    }


def _try_llm_intent(message: str) -> dict[str, Any] | None:
    try:
        response = llm_client.call_llm_for_intent(message)
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

    adjustment_type = response.get("adjustmentType")
    if adjustment_type is not None and adjustment_type not in SUPPORTED_ADJUSTMENTS:
        return None
    return {"adjustmentType": adjustment_type}
