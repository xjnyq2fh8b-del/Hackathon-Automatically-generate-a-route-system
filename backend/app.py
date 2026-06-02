from copy import deepcopy
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.intent_parser import parse_intent
from backend.poi_catalog import load_poi_catalog_or_fallback, to_frontend_places
from backend.route_planner import RoutePlannerError, generate_adjusted_route, generate_default_route


app = FastAPI(title="Westlake Route Agent Mock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str = ""
    message: str = ""

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


def _route_data(route: dict | None = None, diff: dict | None = None) -> dict:
    route_payload = deepcopy(route or DEFAULT_ROUTE)
    return {
        "constraints": deepcopy(CONSTRAINTS),
        "places": _places_for_route(route_payload),
        "route": route_payload,
        "diff": deepcopy(diff),
    }


def _catalog_route_data(planned: dict) -> dict:
    return {
        "constraints": deepcopy(CONSTRAINTS),
        "places": deepcopy(planned["places"]),
        "route": deepcopy(planned["route"]),
        "diff": deepcopy(planned.get("diff")),
    }


def _try_catalog_default_route() -> dict | None:
    if not POI_CATALOG_LOADED:
        return None
    try:
        return _catalog_route_data(generate_default_route(POI_CATALOG))
    except (RoutePlannerError, KeyError, TypeError, ValueError):
        return None


def _try_catalog_adjusted_route(adjustment_type: str) -> dict | None:
    if not POI_CATALOG_LOADED:
        return None
    try:
        return _catalog_route_data(generate_adjusted_route(adjustment_type, POI_CATALOG))
    except (RoutePlannerError, KeyError, TypeError, ValueError):
        return None


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


@app.get("/api/health")
def health() -> dict:
    return {"message": "服务正常"}


@app.post("/api/parse")
def parse_text(request: TextRequest) -> dict:
    parse_intent(request.input_text())
    return {"constraints": deepcopy(CONSTRAINTS)}


def _default_route_response() -> dict:
    catalog_route_data = _try_catalog_default_route()
    if catalog_route_data:
        return {"routeData": catalog_route_data}
    return {"routeData": _route_data(diff=None)}


@app.post("/api/route/generate")
def generate_route(request: TextRequest) -> dict:
    parse_intent(request.input_text())
    return _default_route_response()


@app.post("/api/chat-route")
def chat_route(request: TextRequest) -> dict:
    intent = parse_intent(request.input_text())
    adjustment_type = intent.get("adjustmentType") if intent.get("intent") == "adjustRoute" else None
    if adjustment_type in ADJUSTMENTS:
        return adjust_route(AdjustRequest(adjustmentType=adjustment_type))
    return _default_route_response()


@app.post("/api/route/adjust")
def adjust_route(request: AdjustRequest) -> dict:
    adjustment_type = request.adjustmentType or request.adjustmentId or ""
    adjustment_type = LEGACY_ADJUSTMENT_ALIASES.get(adjustment_type, adjustment_type)

    if adjustment_type in ADJUSTMENTS:
        catalog_route_data = _try_catalog_adjusted_route(adjustment_type)
        if catalog_route_data:
            return {"routeData": catalog_route_data}
        route, diff = _shortcut_adjustment(adjustment_type)
        return {"routeData": _route_data(route=route, diff=diff)}

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
