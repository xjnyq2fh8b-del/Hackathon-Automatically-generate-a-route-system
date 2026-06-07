import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.intent_parser import parse_intent
from backend.llm_client import get_llm_status
from backend.poi_catalog import load_poi_catalog_or_fallback, to_frontend_places
from backend.route_planner import (
    RoutePlannerError,
    generate_adjusted_route,
    generate_default_route,
    generate_route_excluding_categories,
    generate_route_for_constraints,
    is_excluded_poi,
)


TRUE_VALUES = {"1", "true", "yes", "on"}
CHAT_ROUTE_RATE_LIMIT = 10
CHAT_ROUTE_RATE_WINDOW_SECONDS = 60
CHAT_ROUTE_REQUESTS: dict[str, list[float]] = {}
LLM_DAILY_REQUESTS: dict[str, int | str] = {"day": "", "count": 0}


def _env_enabled(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() in TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _docs_path(path: str) -> str | None:
    return path if _env_enabled("ENABLE_DOCS", "true") else None


def _allowed_origins() -> list[str]:
    origins = ["http://localhost:3000", "http://localhost:4173", "https://cityroutemate.netlify.app"]
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip()
    if frontend_origin:
        origins.append(frontend_origin)
    # Before public deployment, set FRONTEND_ORIGIN to the production frontend URL.
    return origins


app = FastAPI(
    title="Westlake Route Agent API",
    docs_url=_docs_path("/docs"),
    redoc_url=_docs_path("/redoc"),
    openapi_url=_docs_path("/openapi.json"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Demo-Token"],
)


class TextRequest(BaseModel):
    text: str = ""
    message: str = ""
    activeConstraints: dict[str, Any] | None = None
    currentRoute: dict[str, Any] | None = None
    currentPlaces: list[dict[str, Any]] | None = None
    currentConstraints: dict[str, Any] | None = None
    routeData: dict[str, Any] | None = None
    sessionId: str | None = None

    def input_text(self) -> str:
        return self.text or self.message


class AdjustRequest(BaseModel):
    adjustmentType: str | None = None
    adjustmentId: str | None = None
    action: Literal["replace", "delete", "moveUp", "moveDown"] | None = None
    nodeId: str | None = None
    route: dict | None = None


CONSTRAINTS = {
    "summary": "湖滨银泰｜14:00-18:00｜人均150｜少排队",
    "chips": [
        {"key": "出发地", "value": "湖滨银泰 in77"},
        {"key": "时间", "value": "14:00-18:00"},
        {"key": "预算", "value": "人均150"},
        {"key": "偏好", "value": "少排队"},
    ],
}


PLACES = [
    {
        "id": "in77",
        "type": "start",
        "name": "湖滨银泰 in77",
        "shortName": "湖滨银泰",
        "address": "上城区湖滨商圈",
        "openHours": "全天可达",
        "rating": "4.7",
        "price": "免费",
        "tags": ["地铁近", "集合方便", "商圈补给"],
        "reason": "作为出发点，减少集合点和线路成本。",
        "note": "",
        "map": {"x": 72, "y": 28},
    },
    {
        "id": "brokenBridge",
        "type": "scenic",
        "name": "断桥残雪",
        "shortName": "断桥残雪",
        "address": "西湖区北山街",
        "openHours": "全天开放",
        "rating": "4.6",
        "price": "免费",
        "tags": ["西湖经典", "拍照友好", "游客友好"],
        "reason": "先去断桥，能最快进入西湖氛围，也方便后面顺路去咖啡点。",
        "note": "游客较多，但不影响路线执行。",
        "map": {"x": 42, "y": 42},
    },
    {
        "id": "baitacoffee",
        "type": "coffee",
        "name": "湖畔白塔咖啡",
        "shortName": "白塔咖啡",
        "address": "湖滨路附近",
        "openHours": "10:00-21:30",
        "rating": "4.5",
        "price": "人均42元",
        "tags": ["安静", "低等待估计", "可休息"],
        "reason": "安排在中段休息，既不打断游览，也给晚饭前留缓冲。",
        "note": "低等待为估计标签，不代表实时排队。",
        "map": {"x": 55, "y": 63},
    },
    {
        "id": "xinbailu",
        "type": "dinner",
        "name": "新白鹿餐厅湖滨店",
        "shortName": "新白鹿",
        "address": "上城区延安路附近",
        "openHours": "10:30-21:30",
        "rating": "4.4",
        "price": "人均78元",
        "tags": ["杭帮菜", "预算友好", "家庭友好"],
        "reason": "最后回到湖滨附近吃晚饭，结束后打车或地铁都方便。",
        "note": "晚高峰可能短时等待。",
        "map": {"x": 76, "y": 72},
    },
    {
        "id": "nongtangli",
        "type": "dinner",
        "name": "弄堂里湖滨店",
        "shortName": "弄堂里",
        "address": "湖滨商圈附近",
        "openHours": "10:30-21:00",
        "rating": "4.3",
        "price": "人均65元",
        "tags": ["杭帮菜", "等待低", "预算更低"],
        "reason": "比原餐厅等待风险更低，人均更低，距离路线也更顺。",
        "note": "晚餐等待风险更低，适合作为当前替换点。",
        "map": {"x": 70, "y": 70},
    },
    {
        "id": "convenienceRest",
        "type": "rest",
        "name": "湖滨轻休息点",
        "shortName": "轻休息点",
        "address": "湖滨步行街附近",
        "openHours": "全天可达",
        "rating": "4.2",
        "price": "免费",
        "tags": ["省预算", "少停留", "顺路"],
        "reason": "保留休息缓冲，同时把预算留给晚餐。",
        "note": "停留时间较短，适合预算收紧时使用。",
        "map": {"x": 60, "y": 58},
    },
    {
        "id": "photoPoint",
        "type": "scenic",
        "name": "北山街湖景点",
        "shortName": "北山街湖景",
        "address": "西湖区北山街沿线",
        "openHours": "全天开放",
        "rating": "4.5",
        "price": "免费",
        "tags": ["湖景", "拍照好看", "不太网红"],
        "reason": "比热门机位更分散，适合想拍照但不想太拥挤的路线。",
        "note": "下午光线较柔和，但仍建议避开桥面人流。",
        "map": {"x": 36, "y": 54},
    },
]


PLACE_BY_ID = {place["id"]: place for place in PLACES}

ROOT_DIR = Path(__file__).resolve().parents[1]
POI_CATALOG_PATH = ROOT_DIR / "data" / "poiCatalog.json"
POI_CATALOG, POI_CATALOG_LOADED, POI_CATALOG_ERRORS = load_poi_catalog_or_fallback(POI_CATALOG_PATH, PLACES)


ADJUSTMENT_BUTTONS = [
    {"type": "restaurantBusy", "label": "餐厅排队太久"},
    {"type": "budget100", "label": "预算降到100"},
    {"type": "noCoffee", "label": "不想喝咖啡"},
    {"type": "twoHours", "label": "只剩2小时"},
    {"type": "photo", "label": "想更适合拍照"},
]


DEFAULT_ROUTE = {
    "id": "westlake-half-day",
    "label": "当前推荐",
    "name": "轻松西湖半日线",
    "explanation": "先从湖滨银泰进入西湖核心景观，再安排咖啡休息，最后顺路吃晚饭。",
    "durationMinutes": 166,
    "budgetPerPerson": 120,
    "walkingKm": 2.3,
    "waitRisk": "低-中",
    "placeIds": ["in77", "brokenBridge", "baitacoffee", "xinbailu"],
    "timeline": [
        {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
        {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:52"},
        {"placeId": "baitacoffee", "arrive": "15:04", "leave": "15:39"},
        {"placeId": "xinbailu", "arrive": "15:51", "leave": "16:46"},
    ],
    "transportSummary": "全程步行优先，单段最长约12分钟；如带老人小孩，可将咖啡到晚餐段改为打车。",
    "transportSegments": [
        {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
        {"fromId": "brokenBridge", "toId": "baitacoffee", "method": "步行", "duration": "约8分钟"},
        {"fromId": "baitacoffee", "toId": "xinbailu", "method": "步行", "duration": "约10分钟"},
    ],
}


ADJUSTMENTS = {
    "restaurantBusy": {
        "route": {
            "explanation": "已为你只替换晚餐点，其他安排保持不变。",
            "durationMinutes": 152,
            "budgetPerPerson": 108,
            "walkingKm": 2.1,
            "waitRisk": "低",
            "placeIds": ["in77", "brokenBridge", "baitacoffee", "nongtangli"],
            "timeline": [
                {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
                {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:52"},
                {"placeId": "baitacoffee", "arrive": "15:04", "leave": "15:39"},
                {"placeId": "nongtangli", "arrive": "15:46", "leave": "16:32"},
            ],
            "transportSegments": [
                {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
                {"fromId": "brokenBridge", "toId": "baitacoffee", "method": "步行", "duration": "约8分钟"},
                {"fromId": "baitacoffee", "toId": "nongtangli", "method": "步行", "duration": "约7分钟"},
            ],
        },
        "diff": {
            "title": "已避开排队晚餐",
            "action": "晚餐改为弄堂里湖滨店，其他节点保持不变。",
            "rows": [
                {"label": "晚餐", "value": "新白鹿餐厅湖滨店 → 弄堂里湖滨店"},
                {"label": "等待风险", "value": "低-中 → 低"},
                {"label": "预计人均", "value": "120元 → 108元"},
                {"label": "总时长", "value": "2小时46分钟 → 2小时32分钟"},
                {"label": "步行距离", "value": "2.3km → 2.1km"},
                {"label": "保留节点", "value": "湖滨银泰 in77、断桥残雪、湖畔白塔咖啡"},
            ],
        },
    },
    "budget100": {
        "route": {
            "explanation": "已把预算压到人均100以内。",
            "durationMinutes": 145,
            "budgetPerPerson": 95,
            "walkingKm": 2.0,
            "waitRisk": "低",
            "placeIds": ["in77", "brokenBridge", "convenienceRest", "nongtangli"],
            "timeline": [
                {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
                {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:52"},
                {"placeId": "convenienceRest", "arrive": "15:00", "leave": "15:12"},
                {"placeId": "nongtangli", "arrive": "15:20", "leave": "16:05"},
            ],
            "transportSegments": [
                {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
                {"fromId": "brokenBridge", "toId": "convenienceRest", "method": "步行", "duration": "约8分钟"},
                {"fromId": "convenienceRest", "toId": "nongtangli", "method": "步行", "duration": "约8分钟"},
            ],
        },
        "diff": {
            "title": "预算已压到 100 内",
            "action": "咖啡改为轻休息点，晚餐改为更低预算方案。",
            "rows": [
                {"label": "预计人均", "value": "120元 → 95元"},
                {"label": "调整节点", "value": "湖畔白塔咖啡 → 湖滨轻休息点；晚餐 → 弄堂里"},
                {"label": "总时长", "value": "2小时46分钟 → 2小时25分钟"},
                {"label": "保留节点", "value": "湖滨银泰 in77、断桥残雪"},
            ],
        },
    },
    "noCoffee": {
        "route": {
            "explanation": "已删除咖啡节点，路线更短。",
            "durationMinutes": 125,
            "budgetPerPerson": 78,
            "walkingKm": 2.0,
            "waitRisk": "中",
            "placeIds": ["in77", "brokenBridge", "xinbailu"],
            "timeline": [
                {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
                {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:52"},
                {"placeId": "xinbailu", "arrive": "15:06", "leave": "15:53"},
            ],
            "transportSegments": [
                {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
                {"fromId": "brokenBridge", "toId": "xinbailu", "method": "步行", "duration": "约14分钟"},
            ],
        },
        "diff": {
            "title": "已删除咖啡点",
            "action": "中途少一次停留，直接从景点前往晚餐。",
            "rows": [
                {"label": "删除节点", "value": "湖畔白塔咖啡"},
                {"label": "预计人均", "value": "120元 → 78元"},
                {"label": "总时长", "value": "2小时46分钟 → 2小时05分钟"},
                {"label": "步行距离", "value": "2.3km → 2.0km"},
                {"label": "保留节点", "value": "湖滨银泰 in77、断桥残雪、新白鹿餐厅湖滨店"},
            ],
        },
    },
    "twoHours": {
        "route": {
            "explanation": "已压缩到约2小时，优先保留核心景点和晚餐。",
            "durationMinutes": 118,
            "budgetPerPerson": 78,
            "walkingKm": 1.8,
            "waitRisk": "中",
            "placeIds": ["in77", "brokenBridge", "xinbailu"],
            "timeline": [
                {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
                {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:42"},
                {"placeId": "xinbailu", "arrive": "14:56", "leave": "15:45"},
            ],
            "transportSegments": [
                {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
                {"fromId": "brokenBridge", "toId": "xinbailu", "method": "步行", "duration": "约14分钟"},
            ],
        },
        "diff": {
            "title": "已压缩到 2 小时",
            "action": "删除或压缩中途停留，牺牲一部分体验完整度。",
            "rows": [
                {"label": "总时长", "value": "2小时46分钟 → 1小时58分钟"},
                {"label": "调整方式", "value": "只保留起点、断桥和晚餐"},
                {"label": "保留节点", "value": "湖滨银泰 in77、断桥残雪、新白鹿餐厅湖滨店"},
            ],
        },
    },
    "photo": {
        "route": {
            "explanation": "已增加更适合拍照的湖景停留点。",
            "durationMinutes": 175,
            "budgetPerPerson": 120,
            "walkingKm": 2.6,
            "waitRisk": "低-中",
            "placeIds": ["in77", "brokenBridge", "photoPoint", "baitacoffee", "xinbailu"],
            "timeline": [
                {"placeId": "in77", "arrive": "14:00", "leave": "14:05"},
                {"placeId": "brokenBridge", "arrive": "14:17", "leave": "14:52"},
                {"placeId": "photoPoint", "arrive": "14:59", "leave": "15:20"},
                {"placeId": "baitacoffee", "arrive": "15:29", "leave": "16:04"},
                {"placeId": "xinbailu", "arrive": "16:14", "leave": "17:01"},
            ],
            "transportSegments": [
                {"fromId": "in77", "toId": "brokenBridge", "method": "步行", "duration": "约12分钟"},
                {"fromId": "brokenBridge", "toId": "photoPoint", "method": "步行", "duration": "约7分钟"},
                {"fromId": "photoPoint", "toId": "baitacoffee", "method": "步行", "duration": "约9分钟"},
                {"fromId": "baitacoffee", "toId": "xinbailu", "method": "步行", "duration": "约10分钟"},
            ],
        },
        "diff": {
            "title": "已加强拍照体验",
            "action": "增加北山街湖景点，同时保留断桥。",
            "rows": [
                {"label": "新增节点", "value": "北山街湖景点"},
                {"label": "总时长", "value": "2小时46分钟 → 2小时55分钟"},
                {"label": "步行距离", "value": "2.3km → 2.6km"},
                {"label": "保留节点", "value": "湖滨银泰 in77、断桥残雪、湖畔白塔咖啡、新白鹿餐厅湖滨店"},
            ],
        },
    },
}


LEGACY_ADJUSTMENT_ALIASES = {
    "queueTooLong": "restaurantBusy",
    "budgetTo100": "budget100",
    "onlyTwoHours": "twoHours",
    "morePhotoFriendly": "photo",
}

NATURAL_ORDER = ["in77", "brokenBridge", "photoPoint", "baitacoffee", "convenienceRest", "xinbailu", "nongtangli"]


def _route_data(
    route: dict | None = None,
    diff: dict | None = None,
    constraints: dict | None = None,
    message: str = "",
) -> dict:
    route_payload = deepcopy(route or DEFAULT_ROUTE)
    places = _places_for_route(route_payload)
    debug = _debug_for_unoptimized_route(route_payload, fallback_used=not POI_CATALOG_LOADED)
    return {
        "constraints": _constraints_payload(constraints),
        "places": places,
        "optimizedPlaces": deepcopy(places),
        "route": route_payload,
        "diff": deepcopy(diff),
        "debug": debug,
        "message": message,
        "adjustmentButtons": deepcopy(ADJUSTMENT_BUTTONS),
    }


def _catalog_route_data(planned: dict, constraints: dict | None = None, message: str = "") -> dict:
    optimized_places = deepcopy(planned.get("optimizedPlaces") or planned["places"])
    return {
        "constraints": _constraints_payload(constraints),
        "places": deepcopy(planned["places"]),
        "optimizedPlaces": optimized_places,
        "route": deepcopy(planned["route"]),
        "diff": deepcopy(planned.get("diff")),
        "debug": deepcopy(planned.get("debug") or _debug_for_unoptimized_route(planned["route"])),
        "message": message,
        "adjustmentButtons": deepcopy(ADJUSTMENT_BUTTONS),
    }


def _debug_for_unoptimized_route(route: dict, fallback_used: bool = True) -> dict:
    place_ids = deepcopy(route.get("placeIds", []))
    walking_km = route.get("walkingKm", 0)
    duration_minutes = route.get("durationMinutes", 0)
    return {
        "beforeOrder": place_ids,
        "afterOrder": place_ids,
        "routeOptimized": False,
        "fallbackUsed": fallback_used,
        "optimizeMethod": "legacy_route_order",
        "routeTotalDistance": round(float(walking_km) * 1000) if isinstance(walking_km, (int, float)) else 0,
        "routeTotalDuration": int(duration_minutes) if isinstance(duration_minutes, (int, float)) else 0,
    }


def _try_catalog_default_route(constraints: dict | None = None, message: str = "") -> dict | None:
    if not POI_CATALOG_LOADED:
        return None
    try:
        planned = generate_route_for_constraints(POI_CATALOG, constraints or {})
        return _catalog_route_data(planned, constraints=constraints, message=message)
    except (RoutePlannerError, KeyError, TypeError, ValueError):
        return None


def _try_catalog_adjusted_route(
    adjustment_type: str,
    constraints: dict | None = None,
    message: str = "",
) -> dict | None:
    if not POI_CATALOG_LOADED:
        return None
    try:
        return _catalog_route_data(
            generate_adjusted_route(adjustment_type, POI_CATALOG),
            constraints=constraints,
            message=message,
        )
    except (RoutePlannerError, KeyError, TypeError, ValueError):
        return None


def _constraints_payload(active_constraints: dict | None = None) -> dict:
    payload = deepcopy(CONSTRAINTS)
    constraints = deepcopy(active_constraints or {})
    for key, value in constraints.items():
        if value not in (None, "", []):
            payload[key] = value
    if constraints:
        payload["chips"] = _constraint_chips(constraints)
        payload["summary"] = "｜".join(chip["value"] for chip in payload["chips"] if chip.get("value"))
    return payload


def _constraint_chips(constraints: dict) -> list[dict[str, str]]:
    chips = [{"key": "出发地", "value": "湖滨银泰 in77"}]
    duration = constraints.get("durationMinutes")
    start_time = constraints.get("startTime")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        time_label = f"{int(duration)}分钟内"
    elif isinstance(start_time, str) and start_time:
        time_label = f"{start_time}出发"
    else:
        time_label = "14:00-18:00"
    chips.append({"key": "时间", "value": time_label})
    budget = constraints.get("budgetMax")
    chips.append({"key": "预算", "value": f"人均{int(budget)}以内" if isinstance(budget, (int, float)) and not isinstance(budget, bool) else "人均150"})

    preferences = []
    avoid_types = constraints.get("avoidTypes", [])
    if constraints.get("preferLowWait") is True:
        preferences.append("少排队")
    if isinstance(avoid_types, list) and "coffee" in avoid_types:
        preferences.append("不喝咖啡")
    if constraints.get("preferPhoto") is True:
        preferences.append("适合拍照")
    if constraints.get("mealFirst") is True:
        preferences.append("先吃饭")
    if constraints.get("preferProperDinner") is True:
        preferences.append("正餐")
    if constraints.get("preferRest") is True:
        preferences.append("可休息")
    if constraints.get("preferIndoor") is True:
        preferences.append("室内优先")
    if constraints.get("preferLessWalking") is True:
        preferences.append("少走路")
    if constraints.get("preferShopping") is True:
        preferences.append("逛街")
    if constraints.get("preferSnack") is True:
        preferences.append("小吃")
    if constraints.get("preferClassicScenic") is True:
        preferences.append("经典景点")
    excluded_categories = _excluded_categories(constraints)
    if "food" in excluded_categories:
        preferences = [item for item in preferences if item not in {"正餐", "小吃"}]
        preferences.append("不安排餐饮")
    if "photo" in excluded_categories:
        preferences = [item for item in preferences if item != "适合拍照"]
        preferences.append("不安排拍照点")
    chips.append({"key": "偏好", "value": "、".join(preferences) if preferences else "少排队"})

    companions = constraints.get("companions", [])
    if isinstance(companions, list) and companions:
        labels = {"elder": "老人", "child": "小孩"}
        chips.append({"key": "同行", "value": "、".join(labels.get(item, str(item)) for item in companions)})
    if constraints.get("weather") == "rain":
        chips.append({"key": "天气", "value": "下雨"})
    return chips


def _merge_constraints(active_constraints: dict | None, constraints_patch: dict | None) -> dict:
    merged = deepcopy(active_constraints) if isinstance(active_constraints, dict) else {}
    patch = constraints_patch if isinstance(constraints_patch, dict) else {}
    for key, value in patch.items():
        if value in (None, "", []):
            continue
        if key in {"avoidTypes", "excludeCategories"}:
            existing = merged.get("avoidTypes", [])
            if key == "excludeCategories":
                existing = merged.get("excludeCategories", [])
            if not isinstance(existing, list):
                existing = []
            incoming = value if isinstance(value, list) else [value]
            merged[key] = sorted({item for item in [*existing, *incoming] if isinstance(item, str) and item})
        else:
            merged[key] = value
    excluded_categories = _excluded_categories(merged)
    if "food" in excluded_categories:
        merged["includeMeal"] = False
        merged["mealFirst"] = False
        merged["preferProperDinner"] = False
        merged["preferSnack"] = False
        avoid_types = merged.get("avoidTypes", [])
        if not isinstance(avoid_types, list):
            avoid_types = []
        merged["avoidTypes"] = sorted({*avoid_types, "coffee", "dinner", "snack"})
    if "photo" in excluded_categories:
        merged["preferPhoto"] = False
        avoid_types = merged.get("avoidTypes", [])
        if not isinstance(avoid_types, list):
            avoid_types = []
        merged["avoidTypes"] = sorted({*avoid_types, "photo"})
    return merged


def _has_excluded_food(constraints: dict | None) -> bool:
    return "food" in _excluded_categories(constraints)


def _has_excluded_categories(constraints: dict | None) -> bool:
    return bool(_excluded_categories(constraints))


def _excluded_categories(constraints: dict | None) -> set[str]:
    if not isinstance(constraints, dict):
        return set()
    categories = constraints.get("excludeCategories", [])
    if isinstance(categories, str):
        categories = [categories]
    avoid_types = constraints.get("avoidTypes", [])
    if isinstance(avoid_types, str):
        avoid_types = [avoid_types]
    result = {category for category in categories if isinstance(category, str)}
    avoid_set = {item for item in avoid_types if isinstance(item, str)}
    if {"coffee", "dinner", "snack"}.issubset(avoid_set):
        result.add("food")
    if "photo" in avoid_set:
        result.add("photo")
    return result


def _request_current_route(request: TextRequest) -> dict | None:
    if isinstance(request.currentRoute, dict):
        return deepcopy(request.currentRoute)
    if isinstance(request.routeData, dict) and isinstance(request.routeData.get("route"), dict):
        return deepcopy(request.routeData["route"])
    return None


def _request_current_places(request: TextRequest) -> list[dict] | None:
    if isinstance(request.currentPlaces, list):
        return deepcopy(request.currentPlaces)
    if isinstance(request.routeData, dict):
        places = request.routeData.get("optimizedPlaces") or request.routeData.get("places")
        if isinstance(places, list):
            return deepcopy(places)
    return None


def _request_current_constraints(request: TextRequest) -> dict:
    if isinstance(request.currentConstraints, dict):
        return deepcopy(request.currentConstraints)
    if isinstance(request.routeData, dict) and isinstance(request.routeData.get("constraints"), dict):
        return deepcopy(request.routeData["constraints"])
    return {}


def _current_place_ids(current_route: dict | None, current_places: list[dict] | None) -> list[str]:
    if isinstance(current_route, dict):
        place_ids = current_route.get("order") or current_route.get("placeIds")
        if isinstance(place_ids, list):
            return [place_id for place_id in place_ids if isinstance(place_id, str)]
    if isinstance(current_places, list):
        return [place["id"] for place in current_places if isinstance(place, dict) and isinstance(place.get("id"), str)]
    return []


def _attach_chat_debug(
    route_data: dict,
    is_follow_up: bool,
    intent: dict,
    old_constraints: dict,
    user_diff: dict,
    merged_constraints: dict,
    current_places: list[dict] | None,
) -> None:
    debug = deepcopy(route_data.get("debug") or {})
    before_places = [
        place.get("id")
        for place in current_places or []
        if isinstance(place, dict) and isinstance(place.get("id"), str)
    ]
    after_places = deepcopy(route_data.get("route", {}).get("placeIds", []))
    removed_places = [place_id for place_id in before_places if place_id not in after_places]
    debug.update(
        {
            "isFollowUp": is_follow_up,
            "intent": intent.get("intent"),
            "oldConstraints": old_constraints,
            "userDiff": user_diff,
            "mergedConstraints": merged_constraints,
            "beforePlaces": before_places,
            "removedPlaces": removed_places,
            "afterPlaces": after_places,
            "routeUpdated": before_places != after_places if before_places else bool(route_data.get("route", {}).get("placeIds")),
        }
    )
    route_data["debug"] = debug


def _constraints_patch_from_intent(intent: dict) -> dict:
    patch = deepcopy(intent.get("constraintsPatch")) if isinstance(intent.get("constraintsPatch"), dict) else {}
    adjustment_type = intent.get("adjustmentType")
    if adjustment_type == "budget100":
        patch["budgetMax"] = 100
    elif adjustment_type == "noCoffee":
        patch["avoidTypes"] = [*patch.get("avoidTypes", []), "coffee"] if isinstance(patch.get("avoidTypes"), list) else ["coffee"]
    elif adjustment_type == "restaurantBusy":
        patch["preferLowWait"] = True
    elif adjustment_type == "twoHours":
        patch["durationMinutes"] = 120
    elif adjustment_type == "photo":
        patch["preferPhoto"] = True

    if isinstance(intent.get("budgetMax"), (int, float)) and not isinstance(intent.get("budgetMax"), bool):
        patch["budgetMax"] = int(intent["budgetMax"])
    time_window = intent.get("timeWindow")
    if isinstance(time_window, dict) and isinstance(time_window.get("durationMinutes"), (int, float)):
        patch["durationMinutes"] = int(time_window["durationMinutes"])
    if isinstance(time_window, dict) and isinstance(time_window.get("start"), str):
        start_time = time_window["start"].strip()
        if len(start_time) == 5 and start_time[2] == ":":
            patch["startTime"] = start_time
    preferences = intent.get("preferences")
    if isinstance(preferences, list):
        if "low_wait" in preferences:
            patch["preferLowWait"] = True
        if "photo" in preferences:
            patch["preferPhoto"] = True
        if any(item in preferences for item in ["food_first", "meal_first", "eat_first"]):
            patch["mealFirst"] = True
        if any(item in preferences for item in ["proper_dinner", "local_food", "local-cuisine", "dinner_quality"]):
            patch["preferProperDinner"] = True
        if any(item in preferences for item in ["rest", "rest_first", "sit", "relax"]):
            patch["preferRest"] = True
        if any(item in preferences for item in ["indoor", "shelter", "rain"]):
            patch["preferIndoor"] = True
        if any(item in preferences for item in ["less_walking", "short_walk", "family", "elder", "child"]):
            patch["preferLessWalking"] = True
        if any(item in preferences for item in ["shopping", "mall", "buy"]):
            patch["preferShopping"] = True
        if any(item in preferences for item in ["snack", "quick_food", "light_meal"]):
            patch["preferSnack"] = True
        if any(item in preferences for item in ["classic", "classic_scenic", "must_visit"]):
            patch["preferClassicScenic"] = True
    avoid = intent.get("avoid")
    if isinstance(avoid, list) and "coffee" in avoid:
        patch["avoidTypes"] = [*patch.get("avoidTypes", []), "coffee"] if isinstance(patch.get("avoidTypes"), list) else ["coffee"]
    if isinstance(avoid, list) and any(item in avoid for item in ["food", "restaurant", "meal", "dinner"]):
        patch["excludeCategories"] = [*patch.get("excludeCategories", []), "food"] if isinstance(patch.get("excludeCategories"), list) else ["food"]
    if isinstance(avoid, list) and "photo" in avoid:
        patch["excludeCategories"] = [*patch.get("excludeCategories", []), "photo"] if isinstance(patch.get("excludeCategories"), list) else ["photo"]
    for key in ("mealFirst", "preferRest", "preferIndoor", "preferLessWalking", "preferProperDinner", "preferShopping", "preferSnack", "preferClassicScenic"):
        if intent.get(key) is True:
            patch[key] = True
    if "food" in patch.get("excludeCategories", []):
        patch["includeMeal"] = False
        patch["mealFirst"] = False
        patch["preferProperDinner"] = False
        patch["preferSnack"] = False
    if "photo" in patch.get("excludeCategories", []):
        patch["preferPhoto"] = False
    weather = intent.get("weather")
    if isinstance(weather, str) and weather:
        patch["weather"] = weather
        if weather == "rain":
            patch["preferIndoor"] = True
    companions = _normalize_companions(intent.get("companions"))
    if companions:
        patch["companions"] = companions
        if any(item in companions for item in ["elder", "child"]):
            patch["preferLessWalking"] = True
    return patch


def _normalize_companions(value: Any) -> list[str]:
    raw_items = value if isinstance(value, list) else [value] if isinstance(value, str) else []
    companions = []
    for item in raw_items:
        if not isinstance(item, str):
            continue
        lowered = item.lower()
        if any(keyword in lowered for keyword in ["elder", "old", "老人", "长辈", "parent", "父母"]):
            companions.append("elder")
        elif any(keyword in lowered for keyword in ["child", "kid", "小孩", "孩子", "儿童", "family"]):
            companions.append("child")
        elif lowered:
            companions.append(lowered)
    return sorted(set(companions))


def _effective_adjustment(adjustment_type: str | None, constraints: dict) -> str | None:
    avoid_types = constraints.get("avoidTypes", [])
    if not isinstance(avoid_types, list):
        avoid_types = []
    budget_max = constraints.get("budgetMax")
    duration_minutes = constraints.get("durationMinutes")
    if isinstance(duration_minutes, (int, float)) and not isinstance(duration_minutes, bool) and duration_minutes <= 120:
        return "twoHours"
    if "coffee" in avoid_types:
        return "noCoffee"
    if isinstance(budget_max, (int, float)) and not isinstance(budget_max, bool) and budget_max <= 100:
        return "budget100"
    if constraints.get("preferPhoto") is True:
        return "photo"
    if constraints.get("preferLowWait") is True:
        return "restaurantBusy"
    return adjustment_type if adjustment_type in ADJUSTMENTS else None


def _places_for_route(route: dict) -> list[dict]:
    route_place_ids = set(route.get("placeIds", []))
    catalog_place_ids = {place.get("id") for place in POI_CATALOG}
    if POI_CATALOG_LOADED and route_place_ids.issubset(catalog_place_ids):
        return to_frontend_places(POI_CATALOG)
    return to_frontend_places(PLACES)


def _route_from_patch(patch: dict) -> dict:
    route = deepcopy(DEFAULT_ROUTE)
    route.update(deepcopy(patch))
    return route


def _place_names(place_ids: list[str]) -> str:
    return "、".join(PLACE_BY_ID[place_id]["name"] for place_id in place_ids if place_id in PLACE_BY_ID)


def _build_transport(place_ids: list[str]) -> list[dict]:
    return [
        {"fromId": from_id, "toId": to_id, "method": "步行", "duration": "约12分钟"}
        for from_id, to_id in zip(place_ids, place_ids[1:])
    ]


def _timeline_for_existing(route: dict, place_ids: list[str]) -> list[dict]:
    timeline_by_place = {item["placeId"]: item for item in route.get("timeline", [])}
    timeline = []
    for index, place_id in enumerate(place_ids):
        fallback_minutes = 14 * index
        fallback_arrive = f"14:{fallback_minutes:02d}" if fallback_minutes < 60 else f"15:{fallback_minutes - 60:02d}"
        timeline.append(
            deepcopy(
                timeline_by_place.get(
                    place_id,
                    {"placeId": place_id, "arrive": fallback_arrive, "leave": fallback_arrive},
                )
            )
        )
    return timeline


def _manual_route(base_route: dict, place_ids: list[str], explanation: str) -> dict:
    route = deepcopy(base_route)
    route["placeIds"] = place_ids
    route["timeline"] = _timeline_for_existing(base_route, place_ids)
    route["transportSegments"] = _build_transport(place_ids)
    route["explanation"] = explanation
    route["durationMinutes"] = max(35, base_route.get("durationMinutes", 166) - 18 * (len(base_route.get("placeIds", [])) - len(place_ids)))
    route["walkingKm"] = round(max(0.8, 0.55 * max(0, len(place_ids) - 1)), 1)
    return route


def _replace_node(route: dict, node_id: str) -> tuple[dict, dict]:
    place = PLACE_BY_ID.get(node_id)
    if not place:
        return route, _message_diff("无法替换节点", "没有找到这个节点。")
    if place["type"] == "dinner":
        return _shortcut_adjustment("restaurantBusy")
    if place["type"] == "coffee":
        return _shortcut_adjustment("budget100")
    if place["type"] == "scenic":
        return _shortcut_adjustment("photo")
    return route, _message_diff("建议保留起点", "起点用于继续计算路线，第一版先不替换。")


def _delete_node(route: dict, node_id: str) -> tuple[dict, dict]:
    place = PLACE_BY_ID.get(node_id)
    if not place:
        return route, _message_diff("无法删除节点", "没有找到这个节点。")
    if place["type"] == "start":
        return route, _message_diff("起点不能删除", "起点需要保留，方便继续计算路线。")

    current_ids = route.get("placeIds", DEFAULT_ROUTE["placeIds"])
    next_ids = [place_id for place_id in current_ids if place_id != node_id]
    next_route = _manual_route(route, next_ids, "已删除这个目的地，并同步更新后续路线。")
    return next_route, {
        "title": "已删除节点",
        "action": "已移除相关目的地，并重算路线。",
        "rows": [
            {"label": "删除节点", "value": place["name"]},
            {"label": "保留节点", "value": _place_names(next_ids)},
        ],
    }


def _move_node(route: dict, node_id: str, direction: int) -> tuple[dict, dict]:
    current_ids = route.get("placeIds", DEFAULT_ROUTE["placeIds"])
    if node_id not in current_ids:
        return route, _message_diff("无法移动节点", "没有找到这个节点。")

    index = current_ids.index(node_id)
    target = index + direction
    if target < 0 or target >= len(current_ids):
        return route, _message_diff("这个节点已经在边界位置", "当前节点无法继续移动。")

    next_ids = current_ids[:]
    next_ids[index], next_ids[target] = next_ids[target], next_ids[index]
    next_route = _manual_route(route, next_ids, "已按你的顺序重算路线。")
    penalty = _order_penalty(next_ids)
    if penalty:
        next_route["durationMinutes"] += penalty * 12
        next_route["walkingKm"] = round(next_route["walkingKm"] + penalty * 0.3, 1)

    return next_route, {
        "title": "顺序已调整",
        "action": "已重新计算总时长、步行距离和编号。",
        "rows": [
            {"label": "路线顺序", "value": " → ".join(PLACE_BY_ID[place_id]["name"] for place_id in next_ids)},
            {"label": "提示", "value": "这个顺序会略绕路，建议保留原顺序。" if penalty else "当前顺序仍然顺路。"},
        ],
    }


def _order_penalty(place_ids: list[str]) -> int:
    penalty = 0
    for previous, current in zip(place_ids, place_ids[1:]):
        if NATURAL_ORDER.index(previous) > NATURAL_ORDER.index(current):
            penalty += 1
    return penalty


def _shortcut_adjustment(adjustment_type: str) -> tuple[dict, dict]:
    adjustment = ADJUSTMENTS[adjustment_type]
    return _route_from_patch(adjustment["route"]), deepcopy(adjustment["diff"])


def _message_diff(title: str, action: str) -> dict:
    return {"title": title, "action": action, "rows": [{"label": "说明", "value": action}]}


def _client_ip(request: Request | None) -> str:
    if request is None:
        return "local-test"
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    if request.client:
        return request.client.host
    return "unknown"


def _enforce_chat_route_rate_limit(request: Request | None) -> None:
    ip = _client_ip(request)
    now = time.monotonic()
    window_start = now - CHAT_ROUTE_RATE_WINDOW_SECONDS
    recent_requests = [sent_at for sent_at in CHAT_ROUTE_REQUESTS.get(ip, []) if sent_at > window_start]
    if len(recent_requests) >= CHAT_ROUTE_RATE_LIMIT:
        CHAT_ROUTE_REQUESTS[ip] = recent_requests
        raise HTTPException(status_code=429, detail="Too many requests")
    recent_requests.append(now)
    CHAT_ROUTE_REQUESTS[ip] = recent_requests


def _enforce_demo_token(request: Request | None) -> None:
    expected_token = os.getenv("DEMO_ACCESS_TOKEN", "").strip()
    if not expected_token:
        return
    provided_token = request.headers.get("x-demo-token", "").strip() if request else ""
    if provided_token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden")


def _enforce_message_length(text: str) -> None:
    max_chars = _env_int("CHAT_ROUTE_MAX_MESSAGE_CHARS", 500)
    if len(text or "") > max_chars:
        raise HTTPException(status_code=413, detail="Message too long")


def _today_utc() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _enforce_daily_llm_limit() -> None:
    limit = _env_int("LLM_DAILY_REQUEST_LIMIT", 200)
    today = _today_utc()
    if LLM_DAILY_REQUESTS.get("day") != today:
        LLM_DAILY_REQUESTS["day"] = today
        LLM_DAILY_REQUESTS["count"] = 0
    count = int(LLM_DAILY_REQUESTS.get("count", 0))
    if count >= limit:
        raise HTTPException(status_code=429, detail="Daily LLM request limit reached")
    LLM_DAILY_REQUESTS["count"] = count + 1


@app.get("/api/health")
def health() -> dict:
    return {"message": "服务正常"}


@app.get("/health")
def platform_health() -> dict:
    return {"status": "ok"}


@app.get("/api/llm-status")
def llm_status() -> dict:
    return get_llm_status()


@app.post("/api/parse")
def parse_text(request: TextRequest) -> dict:
    parse_intent(request.input_text())
    return {"constraints": deepcopy(CONSTRAINTS)}


def _default_route_response(constraints: dict | None = None, message: str = "") -> dict:
    catalog_route_data = _try_catalog_default_route(constraints=constraints, message=message)
    if catalog_route_data:
        return {"routeData": catalog_route_data}
    return {"routeData": _route_data(diff=None, constraints=constraints, message=message)}


@app.post("/api/route/generate")
def generate_route(request: TextRequest) -> dict:
    intent = parse_intent(request.input_text())
    constraints = _merge_constraints(request.activeConstraints, _constraints_patch_from_intent(intent))
    return _default_route_response(constraints=constraints)


@app.post("/api/chat-route")
def chat_route_endpoint(request: TextRequest, http_request: Request) -> dict:
    _enforce_demo_token(http_request)
    _enforce_chat_route_rate_limit(http_request)
    _enforce_message_length(request.input_text())
    _enforce_daily_llm_limit()
    return chat_route(request)


def chat_route(request: TextRequest) -> dict:
    current_route = _request_current_route(request)
    current_places = _request_current_places(request)
    old_constraints = _request_current_constraints(request)
    is_follow_up = bool(current_route or current_places or old_constraints or request.sessionId)
    intent = parse_intent(request.input_text(), currentRoute=current_route)
    adjustment_type = intent.get("adjustmentType") if intent.get("intent") == "adjustRoute" else None
    constraints = _merge_constraints(_merge_constraints(old_constraints, request.activeConstraints), _constraints_patch_from_intent(intent))
    effective_adjustment = _effective_adjustment(adjustment_type, constraints)
    if _has_excluded_categories(constraints):
        response = _exclude_categories_route_response(
            current_route=current_route,
            current_places=current_places,
            constraints=constraints,
            message=request.input_text(),
        )
    elif effective_adjustment in ADJUSTMENTS:
        response = _adjust_route_response(effective_adjustment, constraints=constraints)
    else:
        response = _default_route_response(constraints=constraints)

    _attach_chat_debug(
        response["routeData"],
        is_follow_up=is_follow_up,
        intent=intent,
        old_constraints=old_constraints,
        user_diff=_constraints_patch_from_intent(intent),
        merged_constraints=constraints,
        current_places=current_places,
    )
    return response


def _exclude_categories_route_response(
    current_route: dict | None,
    current_places: list[dict] | None,
    constraints: dict | None,
    message: str = "",
) -> dict:
    place_ids = _current_place_ids(current_route, current_places)
    excluded_categories = _excluded_categories(constraints)
    if POI_CATALOG_LOADED:
        try:
            planned = generate_route_excluding_categories(
                POI_CATALOG,
                place_ids,
                sorted(excluded_categories),
                constraints=constraints,
            )
            return {"routeData": _catalog_route_data(planned, constraints=constraints, message=message)}
        except (RoutePlannerError, KeyError, TypeError, ValueError):
            pass

    route = deepcopy(current_route or DEFAULT_ROUTE)
    before_ids = route.get("placeIds", DEFAULT_ROUTE["placeIds"])
    places = _places_for_route(route)
    removed_ids = {place["id"] for place in places if is_excluded_poi(place, excluded_categories)}
    next_ids = [place_id for place_id in before_ids if place_id not in removed_ids]
    if len(next_ids) < 2:
        next_ids = [place_id for place_id in before_ids if place_id not in removed_ids] or before_ids[:1]
    next_route = _manual_route(route, next_ids, "已去掉相关点位，但附近可替代点不足。")
    route_data = _route_data(route=next_route, diff=_message_diff("已去掉相关点位", "已删除相关目的地，但当前 mock 可替代点不足。"), constraints=constraints, message=message)
    route_data["debug"]["removedPlaces"] = sorted(removed_ids)
    return {"routeData": route_data}


def _adjust_route_response(adjustment_type: str, constraints: dict | None = None, message: str = "") -> dict:
    catalog_route_data = _try_catalog_adjusted_route(adjustment_type, constraints=constraints, message=message)
    if catalog_route_data:
        return {"routeData": catalog_route_data}
    route, diff = _shortcut_adjustment(adjustment_type)
    return {"routeData": _route_data(route=route, diff=diff, constraints=constraints, message=message)}


@app.post("/api/route/adjust")
def adjust_route(request: AdjustRequest) -> dict:
    adjustment_type = request.adjustmentType or request.adjustmentId or ""
    adjustment_type = LEGACY_ADJUSTMENT_ALIASES.get(adjustment_type, adjustment_type)

    if adjustment_type in ADJUSTMENTS:
        constraints = _constraints_patch_from_intent({"intent": "adjustRoute", "adjustmentType": adjustment_type})
        return _adjust_route_response(adjustment_type, constraints=constraints)

    base_route = request.route or deepcopy(DEFAULT_ROUTE)
    if request.action and request.nodeId:
        if request.action == "replace":
            route, diff = _replace_node(base_route, request.nodeId)
        elif request.action == "delete":
            route, diff = _delete_node(base_route, request.nodeId)
        elif request.action == "moveUp":
            route, diff = _move_node(base_route, request.nodeId, -1)
        else:
            route, diff = _move_node(base_route, request.nodeId, 1)
        return {"routeData": _route_data(route=route, diff=diff)}

    return {
        "error": "这个调整暂时不支持",
        "supportedAdjustmentTypes": list(ADJUSTMENTS),
        "supportedNodeActions": ["replace", "delete", "moveUp", "moveDown"],
    }


@app.get("/api/pois")
def list_pois() -> dict:
    return {"places": to_frontend_places(POI_CATALOG)}
