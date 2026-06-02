from __future__ import annotations

import math
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from backend.poi_catalog import (
    calculate_route_budget,
    get_buffer_candidates,
    get_dinner_candidates,
    get_non_coffee_buffer_candidates,
    get_photo_candidates,
    get_scenic_candidates,
    to_frontend_places,
)


WALK_METERS_PER_MINUTE = 80
DEFAULT_START_TIME = "14:00"
FALLBACK_MAP = {"x": 50, "y": 50}
RISK_SCORE = {"low": 0, "medium": 1, "high": 3}
RISK_TEXT = {"low": "低", "medium": "中", "high": "高"}


class RoutePlannerError(ValueError):
    pass


def calculate_distance_meters(from_poi: dict[str, Any], to_poi: dict[str, Any]) -> float:
    """V1 uses straight-line distance; replace with Amap walking paths later."""
    from_location = from_poi.get("location") or {}
    to_location = to_poi.get("location") or {}
    lng1 = float(from_location["lng"])
    lat1 = float(from_location["lat"])
    lng2 = float(to_location["lng"])
    lat2 = float(to_location["lat"])
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_walk_minutes(distance_meters: float) -> int:
    return max(1, math.ceil(distance_meters / WALK_METERS_PER_MINUTE))


def generate_default_route(poi_catalog: list[dict[str, Any]]) -> dict[str, Any]:
    start = _choose_start(poi_catalog)
    scenic = _choose_scenic(poi_catalog, start)
    dinner = _choose_dinner(poi_catalog, scenic, budget_limit=None)
    buffer = _choose_buffer(poi_catalog, scenic, dinner, prefer_coffee=True)
    return _build_result(
        [start, scenic, buffer, dinner],
        roles=["start", "scenic", "buffer", "dinner"],
        route_name="轻松西湖半日线",
        explanation="基于本地 poiCatalog 选择一条包含核心西湖体验、缓冲休息和晚餐的路线。",
        diff=None,
    )


def generate_adjusted_route(adjustment_type: str, poi_catalog: list[dict[str, Any]]) -> dict[str, Any]:
    default = generate_default_route(poi_catalog)
    default_pois = default["selectedPois"]
    start, scenic, buffer, dinner = default_pois

    if adjustment_type == "restaurantBusy":
        new_dinner = _choose_dinner(
            poi_catalog,
            buffer,
            budget_limit=dinner.get("avgCost"),
            exclude_ids={dinner["id"]},
            low_wait=True,
        )
        result = _build_result(
            [start, scenic, buffer, new_dinner],
            roles=["start", "scenic", "buffer", "dinner"],
            route_name="低等待晚餐方案",
            explanation="已优先替换等待风险更低的晚餐点，其他节点保持不变。",
            diff=None,
        )
        result["diff"] = _diff(
            "已避开排队晚餐",
            "只替换晚餐节点，核心景点和中段缓冲保持不变。",
            [
                ("晚餐", f"{dinner['name']} → {new_dinner['name']}"),
                ("等待风险", f"{_risk_label(dinner)} → {_risk_label(new_dinner)}"),
                ("预计人均", f"{default['route']['budgetPerPerson']}元 → {result['route']['budgetPerPerson']}元"),
                ("总时长", f"{default['route']['durationMinutes']}分钟 → {result['route']['durationMinutes']}分钟"),
                ("步行距离", f"{default['route']['walkingKm']}km → {result['route']['walkingKm']}km"),
                ("保留节点", f"{start['name']}、{scenic['name']}、{buffer['name']}"),
            ],
        )
        return result

    if adjustment_type == "budget100":
        new_buffer = _choose_budget_buffer(poi_catalog, scenic)
        new_dinner = _choose_dinner(poi_catalog, new_buffer, budget_limit=100, low_budget=True)
        result = _build_result(
            [start, scenic, new_buffer, new_dinner],
            roles=["start", "scenic", "buffer", "dinner"],
            route_name="百元内轻量方案",
            explanation="已优先选择低消费缓冲点和更预算友好的餐饮点。",
            diff=None,
        )
        before_budget = default["route"]["budgetPerPerson"]
        after_budget = result["route"]["budgetPerPerson"]
        result["diff"] = _diff(
            "预算已压到 100 附近",
            "优先替换消费节点，免费景点和出发点不计入预算。",
            [
                ("预计人均", f"{before_budget}元 → {after_budget}元"),
                ("总时长", f"{default['route']['durationMinutes']}分钟 → {result['route']['durationMinutes']}分钟"),
                ("步行距离", f"{default['route']['walkingKm']}km → {result['route']['walkingKm']}km"),
                ("缓冲点", f"{buffer['name']} → {new_buffer['name']}"),
                ("晚餐", f"{dinner['name']} → {new_dinner['name']}"),
                ("说明", "start、scenic、photo 不计入预算；mall/rest 默认不计入预算。"),
            ],
        )
        return result

    if adjustment_type == "noCoffee":
        selected = [start, scenic]
        roles = ["start", "scenic"]
        replacement = _choose_non_coffee_buffer(poi_catalog, scenic, dinner)
        if replacement:
            selected.append(replacement)
            roles.append("buffer")
        selected.append(dinner)
        roles.append("dinner")
        result = _build_result(
            selected,
            roles=roles,
            route_name="无咖啡路线",
            explanation="已排除咖啡类节点，并用非咖啡缓冲点补足休息节奏。",
            diff=None,
        )
        result["diff"] = _diff(
            "已删除或替换咖啡点",
            "路线中不再包含 type=coffee 的节点。",
            [
                ("原缓冲点", buffer["name"]),
                ("新缓冲点", replacement["name"] if replacement else "已删除中段缓冲点"),
                ("预计人均", f"{default['route']['budgetPerPerson']}元 → {result['route']['budgetPerPerson']}元"),
                ("总时长", f"{default['route']['durationMinutes']}分钟 → {result['route']['durationMinutes']}分钟"),
                ("步行距离", f"{default['route']['walkingKm']}km → {result['route']['walkingKm']}km"),
            ],
        )
        return result

    if adjustment_type == "twoHours":
        quick_dinner = _choose_dinner(poi_catalog, scenic, budget_limit=100, low_budget=True)
        selected = [start, scenic, quick_dinner]
        result = _build_result(
            selected,
            roles=["start", "scenic", "dinner"],
            route_name="两小时压缩路线",
            explanation="已优先删除中段缓冲点，并压缩核心体验点停留时间。",
            stay_overrides={scenic["id"]: min(25, int(scenic.get("stayMinutes", 25)))},
            diff=None,
        )
        result["diff"] = _diff(
            "已压缩到 2 小时附近",
            "优先删除 buffer 节点，保留出发点、核心西湖体验和餐饮点。",
            [
                ("总时长", f"{default['route']['durationMinutes']}分钟 → {result['route']['durationMinutes']}分钟"),
                ("删除节点", buffer["name"]),
                ("餐饮点", f"{dinner['name']} → {quick_dinner['name']}"),
                ("预计人均", f"{default['route']['budgetPerPerson']}元 → {result['route']['budgetPerPerson']}元"),
                ("步行距离", f"{default['route']['walkingKm']}km → {result['route']['walkingKm']}km"),
            ],
        )
        return result

    if adjustment_type == "photo":
        photo_point = _choose_photo_point(poi_catalog, scenic)
        selected = [start, scenic, photo_point, dinner]
        result = _build_result(
            selected,
            roles=["start", "scenic", "photo", "dinner"],
            route_name="拍照增强路线",
            explanation="已提高湖景和拍照友好节点优先级，用拍照点替代中段缓冲。",
            diff=None,
        )
        result["diff"] = _diff(
            "已增强拍照体验",
            "用 photoScore 更高的湖景拍照点增强路线，同时避免明显增加节点数量。",
            [
                ("拍照点", f"{buffer['name']} → {photo_point['name']}"),
                ("预计人均", f"{default['route']['budgetPerPerson']}元 → {result['route']['budgetPerPerson']}元"),
                ("总时长", f"{default['route']['durationMinutes']}分钟 → {result['route']['durationMinutes']}分钟"),
                ("步行距离", f"{default['route']['walkingKm']}km → {result['route']['walkingKm']}km"),
            ],
        )
        return result

    raise RoutePlannerError(f"unsupported adjustmentType: {adjustment_type}")


def _choose_start(pois: list[dict[str, Any]]) -> dict[str, Any]:
    starts = [poi for poi in pois if poi.get("type") == "start"]
    if not starts:
        raise RoutePlannerError("poiCatalog has no start candidate.")
    return starts[0]


def _choose_scenic(pois: list[dict[str, Any]], start: dict[str, Any]) -> dict[str, Any]:
    candidates = get_scenic_candidates(pois)
    return _best(candidates, lambda poi: _score_scenic(poi, start), "scenic")


def _choose_buffer(
    pois: list[dict[str, Any]],
    previous: dict[str, Any],
    next_poi: dict[str, Any],
    prefer_coffee: bool,
    exclude_coffee: bool = False,
) -> dict[str, Any]:
    candidates = get_buffer_candidates(pois)
    if exclude_coffee:
        candidates = [poi for poi in candidates if poi.get("type") != "coffee"]
    return _best(candidates, lambda poi: _score_buffer(poi, previous, next_poi, prefer_coffee), "buffer")


def _choose_non_coffee_buffer(
    pois: list[dict[str, Any]],
    previous: dict[str, Any],
    next_poi: dict[str, Any],
) -> dict[str, Any] | None:
    candidates = get_non_coffee_buffer_candidates(pois)
    if not candidates:
        return None
    return _best(candidates, lambda poi: _score_buffer(poi, previous, next_poi, prefer_coffee=False), "non-coffee buffer")


def _choose_budget_buffer(pois: list[dict[str, Any]], previous: dict[str, Any]) -> dict[str, Any]:
    candidates = [poi for poi in get_non_coffee_buffer_candidates(pois) if poi.get("type") in {"snack", "rest", "mall"}]
    return _best(candidates, lambda poi: _score_budget_buffer(poi, previous), "budget buffer")


def _choose_dinner(
    pois: list[dict[str, Any]],
    previous: dict[str, Any],
    budget_limit: int | float | None,
    exclude_ids: set[str] | None = None,
    low_wait: bool = False,
    low_budget: bool = False,
) -> dict[str, Any]:
    candidates = get_dinner_candidates(pois)
    if exclude_ids:
        candidates = [poi for poi in candidates if poi.get("id") not in exclude_ids]
    if low_wait:
        candidates = [poi for poi in candidates if poi.get("waitRisk") != "high"] or candidates
    if budget_limit is not None:
        candidates = [poi for poi in candidates if _number(poi.get("avgCost")) <= budget_limit + 15] or candidates
    return _best(candidates, lambda poi: _score_dinner(poi, previous, low_wait, low_budget), "dinner")


def _choose_photo_point(pois: list[dict[str, Any]], scenic: dict[str, Any]) -> dict[str, Any]:
    candidates = get_photo_candidates(pois) + get_scenic_candidates(pois)
    candidates = [poi for poi in candidates if poi.get("id") != scenic.get("id")]
    return _best(candidates, lambda poi: _score_photo(poi, scenic), "photo")


def _build_result(
    selected_pois: list[dict[str, Any]],
    roles: list[str],
    route_name: str,
    explanation: str,
    diff: dict[str, Any] | None,
    stay_overrides: dict[str, int] | None = None,
) -> dict[str, Any]:
    if len(selected_pois) != len(roles):
        raise RoutePlannerError("selected_pois and roles length mismatch.")
    stay_overrides = stay_overrides or {}
    route_nodes = [
        {"placeId": poi["id"], "role": role, "type": poi["type"]}
        for poi, role in zip(selected_pois, roles)
    ]
    budget = calculate_route_budget(route_nodes, selected_pois)
    timeline, transport_segments, walking_meters = _build_timeline_and_transport(selected_pois, stay_overrides)
    stay_total = sum(stay_overrides.get(poi["id"], int(poi.get("stayMinutes", 25))) for poi in selected_pois)
    walk_total = sum(int(segment["_minutes"]) for segment in transport_segments)
    clean_segments = [
        {key: value for key, value in segment.items() if key != "_minutes"}
        for segment in transport_segments
    ]
    route = {
        "id": "westlake-poi-catalog-v1",
        "label": "当前推荐",
        "name": route_name,
        "explanation": explanation,
        "durationMinutes": stay_total + walk_total + 5,
        "budgetPerPerson": budget,
        "walkingKm": round(walking_meters / 1000, 1),
        "waitRisk": _route_wait_risk(selected_pois),
        "placeIds": [poi["id"] for poi in selected_pois],
        "timeline": timeline,
        "transportSummary": "V1 使用经纬度直线距离估算步行时间，后续可替换为高德步行路径。",
        "transportSegments": clean_segments,
    }
    return {
        "places": _frontend_selected_places(selected_pois),
        "route": route,
        "diff": diff,
        "selectedPois": selected_pois,
    }


def _build_timeline_and_transport(
    selected_pois: list[dict[str, Any]],
    stay_overrides: dict[str, int],
) -> tuple[list[dict[str, str]], list[dict[str, Any]], float]:
    current = datetime.strptime(DEFAULT_START_TIME, "%H:%M")
    timeline: list[dict[str, str]] = []
    segments: list[dict[str, Any]] = []
    walking_meters = 0.0
    for index, poi in enumerate(selected_pois):
        arrive = current
        stay = stay_overrides.get(poi["id"], int(poi.get("stayMinutes", 25)))
        leave = arrive + timedelta(minutes=stay)
        timeline.append({"placeId": poi["id"], "arrive": arrive.strftime("%H:%M"), "leave": leave.strftime("%H:%M")})
        current = leave
        if index < len(selected_pois) - 1:
            next_poi = selected_pois[index + 1]
            distance = calculate_distance_meters(poi, next_poi)
            minutes = estimate_walk_minutes(distance)
            walking_meters += distance
            segments.append(
                {
                    "fromId": poi["id"],
                    "toId": next_poi["id"],
                    "method": "步行",
                    "duration": f"约{minutes}分钟",
                    "_minutes": minutes,
                }
            )
            current = current + timedelta(minutes=minutes)
    return timeline, segments, walking_meters


def _frontend_selected_places(selected_pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    places = to_frontend_places(selected_pois)
    for place, poi in zip(places, selected_pois):
        place["map"] = _map_from_location(poi)
    return places


def _map_from_location(poi: dict[str, Any]) -> dict[str, int]:
    location = poi.get("location") or {}
    lng = _number(location.get("lng"))
    lat = _number(location.get("lat"))
    if not lng or not lat:
        return deepcopy(FALLBACK_MAP)
    x = round((lng - 120.145) / (120.166 - 120.145) * 70 + 15)
    y = round((30.263 - lat) / (30.263 - 30.250) * 60 + 20)
    return {"x": min(88, max(12, x)), "y": min(82, max(18, y))}


def _score_scenic(poi: dict[str, Any], start: dict[str, Any]) -> float:
    return (
        _number(poi.get("classicScore")) * 2
        + _number(poi.get("photoScore"))
        + _number(poi.get("walkFriendlyScore"))
        - _risk_penalty(poi.get("crowdRisk"))
        - calculate_distance_meters(start, poi) / 500
        + _open_status_bonus(poi)
    )


def _score_buffer(poi: dict[str, Any], previous: dict[str, Any], next_poi: dict[str, Any], prefer_coffee: bool) -> float:
    return (
        _number(poi.get("restScore")) * 2
        + _number(poi.get("chatScore"))
        + _number(poi.get("budgetScore")) * 0.5
        + (3 if prefer_coffee and poi.get("type") == "coffee" else 0)
        - _risk_penalty(poi.get("waitRisk"))
        - (calculate_distance_meters(previous, poi) + calculate_distance_meters(poi, next_poi)) / 700
        + _open_status_bonus(poi)
    )


def _score_budget_buffer(poi: dict[str, Any], previous: dict[str, Any]) -> float:
    return (
        _number(poi.get("budgetScore")) * 2
        + _number(poi.get("restScore"))
        - _number(poi.get("avgCost")) / 10
        - calculate_distance_meters(previous, poi) / 700
        + _open_status_bonus(poi)
    )


def _score_dinner(poi: dict[str, Any], previous: dict[str, Any], low_wait: bool, low_budget: bool) -> float:
    return (
        _number(poi.get("localFlavorScore")) * 1.5
        + _number(poi.get("familyScore"))
        + _number(poi.get("budgetScore")) * (2 if low_budget else 1)
        - _risk_penalty(poi.get("waitRisk")) * (2 if low_wait else 1)
        - _number(poi.get("avgCost")) / (12 if low_budget else 30)
        - calculate_distance_meters(previous, poi) / 700
        + _open_status_bonus(poi)
    )


def _score_photo(poi: dict[str, Any], previous: dict[str, Any]) -> float:
    tags = set(poi.get("experienceTags", []))
    return (
        _number(poi.get("photoScore")) * 2
        + _number(poi.get("classicScore"))
        + (2 if "photo" in tags else 0)
        + (1.5 if "lake-view" in tags else 0)
        - _risk_penalty(poi.get("crowdRisk")) * 0.5
        - calculate_distance_meters(previous, poi) / 700
        + _open_status_bonus(poi)
    )


def _best(candidates: list[dict[str, Any]], score_fn, label: str) -> dict[str, Any]:
    if not candidates:
        raise RoutePlannerError(f"no {label} candidates.")
    return max(candidates, key=score_fn)


def _risk_penalty(value: Any) -> float:
    return RISK_SCORE.get(value, 1)


def _open_status_bonus(poi: dict[str, Any]) -> float:
    # Unknown structured hours are allowed in V1, but slightly lower confidence.
    if not poi.get("openingHours") and poi.get("openHoursText"):
        return -0.5
    return 0


def _route_wait_risk(pois: list[dict[str, Any]]) -> str:
    worst = "low"
    for poi in pois:
        if RISK_SCORE.get(poi.get("waitRisk"), 0) > RISK_SCORE[worst]:
            worst = poi.get("waitRisk")
    return RISK_TEXT.get(worst, "中")


def _risk_label(poi: dict[str, Any]) -> str:
    return RISK_TEXT.get(poi.get("waitRisk"), "中")


def _route_budget(pois: list[dict[str, Any]]) -> int | float:
    return calculate_route_budget([{"placeId": poi["id"], "type": poi["type"]} for poi in pois], pois)


def _diff(title: str, action: str, rows: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "title": title,
        "action": action,
        "rows": [{"label": label, "value": value} for label, value in rows],
    }


def _number(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0
