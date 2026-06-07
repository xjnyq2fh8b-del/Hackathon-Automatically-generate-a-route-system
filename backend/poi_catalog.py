from __future__ import annotations

import csv
import json
import re
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"scenic", "photo", "coffee", "dinner", "rest", "snack", "mall", "start"}
ALLOWED_RISKS = {"low", "medium", "high"}
ALLOWED_OPEN_HOURS_CONFIDENCE = {"high", "medium", "low", "unknown"}
SCORE_FIELDS = [
    "photoScore",
    "quietScore",
    "restScore",
    "familyScore",
    "chatScore",
    "classicScore",
    "localFlavorScore",
    "budgetScore",
    "walkFriendlyScore",
]
NUMERIC_FIELDS = ["avgCost", "stayMinutes", "rating"]
REQUIRED_FIELDS = [
    "id",
    "amapId",
    "name",
    "type",
    "address",
    "location",
    "openHoursText",
    "openingHours",
    "openHoursConfidence",
    "avgCost",
    "rating",
    "source",
    "tags",
    "experienceTags",
    "stayMinutes",
    "waitRisk",
    "crowdRisk",
    "note",
    *SCORE_FIELDS,
]
FRONTEND_PLACE_FIELDS = {
    "id",
    "type",
    "name",
    "shortName",
    "address",
    "openHours",
    "openHoursText",
    "rating",
    "price",
    "tags",
    "reason",
    "note",
    "map",
    "location",
    "imageUrl",
}

TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
SIMPLE_HOURS_PATTERN = re.compile(r"^\s*((?:[01]\d|2[0-3]):[0-5]\d)\s*-\s*((?:[01]\d|2[0-3]):[0-5]\d)\s*$")
ALWAYS_OPEN_PATTERN = re.compile(r"(24\s*小时|全天)")
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]


@dataclass
class CatalogValidation:
    errors: list[str]
    warnings: list[str]


class PoiCatalogError(ValueError):
    pass


def load_poi_catalog(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    result = validate_poi_catalog_with_warnings(data)
    if result.errors:
        raise PoiCatalogError("\n".join(result.errors))
    return data


def load_poi_catalog_or_fallback(path: Path, fallback_places: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool, list[str]]:
    try:
        return load_poi_catalog(path), True, []
    except (OSError, json.JSONDecodeError, PoiCatalogError) as error:
        return deepcopy(fallback_places), False, [str(error)]


def validate_poi_catalog(data: Any) -> list[str]:
    return validate_poi_catalog_with_warnings(data).errors


def validate_poi_catalog_with_warnings(data: Any) -> CatalogValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, list):
        return CatalogValidation(["poiCatalog must be a JSON array."], [])

    ids: list[str] = []
    type_counter: Counter[str] = Counter()

    for index, poi in enumerate(data):
        label = _poi_label(poi, index)
        if not isinstance(poi, dict):
            errors.append(f"{label}: item must be an object.")
            continue

        for field in REQUIRED_FIELDS:
            if field not in poi:
                errors.append(f"{label}: missing required field `{field}`.")
            elif field not in {"openHoursText", "openingHours", "note"} and _is_blank(poi[field]):
                errors.append(f"{label}: `{field}` cannot be empty.")

        poi_id = poi.get("id")
        if isinstance(poi_id, str) and poi_id:
            ids.append(poi_id)

        poi_type = poi.get("type")
        if poi_type not in ALLOWED_TYPES:
            errors.append(f"{label}: `type` must be one of {sorted(ALLOWED_TYPES)}.")
        elif isinstance(poi_type, str):
            type_counter[poi_type] += 1

        if poi.get("waitRisk") not in ALLOWED_RISKS:
            errors.append(f"{label}: `waitRisk` must be one of {sorted(ALLOWED_RISKS)}.")
        if poi.get("crowdRisk") not in ALLOWED_RISKS:
            errors.append(f"{label}: `crowdRisk` must be one of {sorted(ALLOWED_RISKS)}.")

        for field in SCORE_FIELDS:
            if field in poi and not _is_int_between(poi[field], 1, 5):
                errors.append(f"{label}: `{field}` must be an integer from 1 to 5.")

        for field in NUMERIC_FIELDS:
            if field in poi and not _is_number(poi[field]):
                errors.append(f"{label}: `{field}` must be a number.")

        _validate_location(poi, label, errors)
        _validate_tags(poi, label, errors)
        _validate_opening_hours(poi, label, errors, warnings)

    duplicate_ids = sorted({poi_id for poi_id in ids if ids.count(poi_id) > 1})
    for poi_id in duplicate_ids:
        errors.append(f"id `{poi_id}` is duplicated.")

    _validate_candidate_counts(data, type_counter, errors)
    return CatalogValidation(errors, warnings)


def csv_to_catalog(csv_path: Path) -> tuple[list[dict[str, Any]], CatalogValidation]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    catalog = [_row_to_poi(row, index) for index, row in enumerate(rows)]
    return catalog, validate_poi_catalog_with_warnings(catalog)


def write_catalog_json(catalog: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(catalog, file, ensure_ascii=False, indent=2)
        file.write("\n")


def to_frontend_places(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    places: list[dict[str, Any]] = []
    for poi in pois:
        place = {key: deepcopy(value) for key, value in poi.items() if key in FRONTEND_PLACE_FIELDS}
        image_url = _place_image_url(poi)
        if image_url:
            place["imageUrl"] = image_url
        if "openHoursText" in poi:
            place["openHoursText"] = poi.get("openHoursText", "")
            place.setdefault("openHours", poi.get("openHoursText", ""))
        if "avgCost" in poi and "price" not in place:
            place["price"] = "免费" if poi["avgCost"] == 0 else f"人均{int(poi['avgCost'])}元"
        if "rating" in poi:
            place["rating"] = str(poi["rating"])
        place.setdefault("shortName", poi.get("name", ""))
        place.setdefault("reason", poi.get("note", ""))
        places.append(place)
    return places


def _place_image_url(poi: dict[str, Any]) -> str:
    image_url = poi.get("imageUrl")
    if isinstance(image_url, str) and image_url.strip():
        return image_url.strip()

    photos = poi.get("photos")
    if not isinstance(photos, list) or not photos:
        return ""
    first_photo = photos[0]
    if not isinstance(first_photo, dict):
        return ""
    photo_url = first_photo.get("url")
    return photo_url.strip() if isinstance(photo_url, str) and photo_url.strip() else ""


def is_open_at(poi: dict[str, Any], day: int, time_text: str) -> bool | None:
    opening_hours = poi.get("openingHours")
    confidence = poi.get("openHoursConfidence")
    if not opening_hours or confidence == "unknown":
        return None
    if day < 0 or day > 6 or not TIME_PATTERN.match(time_text):
        raise ValueError("day must be 0-6 and time_text must use HH:mm format.")

    current_minutes = _minutes(time_text)
    previous_day = (day - 1) % 7
    for group in opening_hours:
        days = group.get("days", [])
        for period in group.get("periods", []):
            open_minutes = _minutes(period["open"])
            close_minutes = _minutes(period["close"])
            if period["crossDay"]:
                if day in days and current_minutes >= open_minutes:
                    return True
                if previous_day in days and current_minutes <= close_minutes:
                    return True
            elif day in days and open_minutes <= current_minutes < close_minutes:
                return True
    return False


def get_pois_by_type(pois: list[dict[str, Any]], poi_type: str) -> list[dict[str, Any]]:
    return [poi for poi in pois if poi.get("type") == poi_type]


def get_buffer_candidates(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        poi
        for poi in pois
        if poi.get("type") in {"coffee", "rest", "snack", "mall"}
        or _score_at_least(poi, "restScore", 4)
        or "rest-friendly" in poi.get("experienceTags", [])
    ]


def get_non_coffee_buffer_candidates(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        poi
        for poi in get_buffer_candidates(pois)
        if poi.get("type") != "coffee"
    ]


def get_dinner_candidates(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return get_pois_by_type(pois, "dinner")


def get_scenic_candidates(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return get_pois_by_type(pois, "scenic")


def get_photo_candidates(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return get_pois_by_type(pois, "photo")


def calculate_route_budget(route_nodes: list[dict[str, Any]], poi_catalog: list[dict[str, Any]]) -> int | float:
    poi_by_id = {poi["id"]: poi for poi in poi_catalog if "id" in poi}
    total: int | float = 0
    for node in route_nodes:
        poi = poi_by_id.get(node.get("placeId") or node.get("id"), {})
        role = node.get("role")
        node_type = node.get("type") or poi.get("type")
        if not _should_include_cost(role, node_type, node, poi):
            continue
        avg_cost = poi.get("avgCost", 0)
        if _is_number(avg_cost):
            total += avg_cost
    return total


# Compatibility aliases for task wording and quick scripts.
loadPoiCatalog = load_poi_catalog_or_fallback
getPoisByType = get_pois_by_type
getBufferCandidates = get_buffer_candidates
getNonCoffeeBufferCandidates = get_non_coffee_buffer_candidates
getDinnerCandidates = get_dinner_candidates
getScenicCandidates = get_scenic_candidates
getPhotoCandidates = get_photo_candidates
calculateRouteBudget = calculate_route_budget


def _row_to_poi(row: dict[str, str], index: int) -> dict[str, Any]:
    lng = _to_number(row.get("location.lng"))
    lat = _to_number(row.get("location.lat"))
    open_hours_text = _clean(row.get("openHoursText")) or _clean(row.get("openHours"))
    opening_hours = _opening_hours_from_row(row, open_hours_text, index)
    confidence = _clean(row.get("openHoursConfidence")) or "medium"
    return {
        "id": _clean(row.get("id")),
        "amapId": _clean(row.get("amapId")),
        "name": _clean(row.get("name")),
        "type": _clean(row.get("type")),
        "address": _clean(row.get("address")),
        "location": {"lng": lng, "lat": lat},
        "openHoursText": open_hours_text,
        "openingHours": opening_hours,
        "openHoursConfidence": confidence,
        "avgCost": _to_number(row.get("avgCost")),
        "rating": _to_number(row.get("rating")),
        "source": _clean(row.get("source")),
        "tags": _split_list(row.get("tags")),
        "experienceTags": _split_list(row.get("experienceTags")),
        "stayMinutes": _to_number(row.get("stayMinutes")),
        "waitRisk": _clean(row.get("waitRisk")),
        "crowdRisk": _clean(row.get("crowdRisk")),
        "photoScore": _to_int(row.get("photoScore")),
        "quietScore": _to_int(row.get("quietScore")),
        "restScore": _to_int(row.get("restScore")),
        "familyScore": _to_int(row.get("familyScore")),
        "chatScore": _to_int(row.get("chatScore")),
        "classicScore": _to_int(row.get("classicScore")),
        "localFlavorScore": _to_int(row.get("localFlavorScore")),
        "budgetScore": _to_int(row.get("budgetScore")),
        "walkFriendlyScore": _to_int(row.get("walkFriendlyScore")),
        "note": _clean(row.get("note")),
    }


def _validate_location(poi: dict[str, Any], label: str, errors: list[str]) -> None:
    location = poi.get("location")
    if not isinstance(location, dict):
        errors.append(f"{label}: `location` must be an object.")
        return
    if not _is_number(location.get("lng")):
        errors.append(f"{label}: `location.lng` must be a number.")
    if not _is_number(location.get("lat")):
        errors.append(f"{label}: `location.lat` must be a number.")


def _validate_tags(poi: dict[str, Any], label: str, errors: list[str]) -> None:
    for field in ("tags", "experienceTags"):
        value = poi.get(field)
        if not isinstance(value, list):
            errors.append(f"{label}: `{field}` must be an array.")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"{label}: `{field}` must contain non-empty strings.")


def _validate_opening_hours(poi: dict[str, Any], label: str, errors: list[str], warnings: list[str]) -> None:
    confidence = poi.get("openHoursConfidence")
    if confidence not in ALLOWED_OPEN_HOURS_CONFIDENCE:
        errors.append(f"{label}: `openHoursConfidence` must be one of {sorted(ALLOWED_OPEN_HOURS_CONFIDENCE)}.")

    opening_hours = poi.get("openingHours")
    if not isinstance(opening_hours, list):
        errors.append(f"{label}: `openingHours` must be an array.")
        return

    if not opening_hours:
        text = poi.get("openHoursText", "")
        suffix = f" from `{text}`" if text else ""
        warnings.append(f"{label}: `openingHours` is empty{suffix}; backend cannot judge open status yet.")

    for group_index, group in enumerate(opening_hours):
        group_label = f"{label}.openingHours[{group_index}]"
        if not isinstance(group, dict):
            errors.append(f"{group_label}: item must be an object.")
            continue
        days = group.get("days")
        if not isinstance(days, list) or not days:
            errors.append(f"{group_label}: `days` must be a non-empty array.")
        elif not all(isinstance(day, int) and 0 <= day <= 6 for day in days):
            errors.append(f"{group_label}: `days` can only contain integers from 0 to 6.")

        periods = group.get("periods")
        if not isinstance(periods, list) or not periods:
            errors.append(f"{group_label}: `periods` must be a non-empty array.")
            continue
        for period_index, period in enumerate(periods):
            _validate_period(period, f"{group_label}.periods[{period_index}]", errors)


def _validate_period(period: Any, label: str, errors: list[str]) -> None:
    if not isinstance(period, dict):
        errors.append(f"{label}: period must be an object.")
        return
    for field in ("open", "close", "crossDay"):
        if field not in period:
            errors.append(f"{label}: missing `{field}`.")
    open_time = period.get("open")
    close_time = period.get("close")
    cross_day = period.get("crossDay")
    if not isinstance(open_time, str) or not TIME_PATTERN.match(open_time):
        errors.append(f"{label}: `open` must use HH:mm format.")
    if not isinstance(close_time, str) or not TIME_PATTERN.match(close_time):
        errors.append(f"{label}: `close` must use HH:mm format.")
    if not isinstance(cross_day, bool):
        errors.append(f"{label}: `crossDay` must be boolean.")
    if (
        isinstance(open_time, str)
        and isinstance(close_time, str)
        and TIME_PATTERN.match(open_time)
        and TIME_PATTERN.match(close_time)
        and cross_day is False
        and _minutes(close_time) <= _minutes(open_time)
    ):
        errors.append(f"{label}: `close` must be later than `open` when `crossDay` is false.")


def _validate_candidate_counts(data: list[Any], type_counter: Counter[str], errors: list[str]) -> None:
    required = {
        "scenic": type_counter["scenic"],
        "photo": type_counter["photo"],
        "coffee": type_counter["coffee"],
        "dinner": type_counter["dinner"],
        "bufferCandidates": len(get_buffer_candidates([poi for poi in data if isinstance(poi, dict)])),
        "nonCoffeeBufferCandidates": len(get_non_coffee_buffer_candidates([poi for poi in data if isinstance(poi, dict)])),
    }
    minimums = {
        "scenic": 3,
        "photo": 3,
        "coffee": 3,
        "dinner": 3,
        "bufferCandidates": 6,
        "nonCoffeeBufferCandidates": 3,
    }
    for group, count in required.items():
        minimum = minimums[group]
        if count < minimum:
            errors.append(f"type group `{group}` needs at least {minimum} candidates, got {count}.")


def _opening_hours_from_row(row: dict[str, str], open_hours_text: str, index: int) -> list[Any]:
    opening_hours_text = _clean(row.get("openingHours"))
    if opening_hours_text:
        parsed = _parse_json_array(opening_hours_text, f"row {index + 1} openingHours")
        if parsed:
            return parsed
    return parse_opening_hours_text(open_hours_text)


def parse_opening_hours_text(open_hours_text: str) -> list[dict[str, Any]]:
    text = open_hours_text.strip()
    if not text:
        return []
    if ALWAYS_OPEN_PATTERN.search(text):
        return [
            {
                "days": ALL_DAYS,
                "periods": [{"open": "00:00", "close": "23:59", "crossDay": False}],
            }
        ]
    match = SIMPLE_HOURS_PATTERN.match(text)
    if not match:
        return []
    open_time, close_time = match.groups()
    cross_day = _minutes(close_time) <= _minutes(open_time)
    return [
        {
            "days": ALL_DAYS,
            "periods": [{"open": open_time, "close": close_time, "crossDay": cross_day}],
        }
    ]


def _score_at_least(poi: dict[str, Any], field: str, minimum: int) -> bool:
    value = poi.get(field)
    return _is_number(value) and value >= minimum


def _should_include_cost(role: Any, node_type: Any, node: dict[str, Any], poi: dict[str, Any]) -> bool:
    if role == "start" or node_type == "start":
        return False
    if node.get("costIncludedByDefault") is True or poi.get("costIncludedByDefault") is True:
        return True
    if node_type in {"scenic", "photo", "mall", "rest"}:
        return False
    return node_type in {"coffee", "dinner", "snack"}


def catalog_summary(pois: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts = Counter(poi.get("type") for poi in pois)
    validation = validate_poi_catalog_with_warnings(pois)
    return {
        "total": len(pois),
        "typeCounts": dict(sorted(type_counts.items())),
        "bufferCandidates": len(get_buffer_candidates(pois)),
        "nonCoffeeBufferCandidates": len(get_non_coffee_buffer_candidates(pois)),
        "errors": len(validation.errors),
        "warnings": len(validation.warnings),
    }


def format_validation_report(result: CatalogValidation) -> str:
    lines: list[str] = []
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines)


def _poi_label(poi: Any, index: int) -> str:
    if isinstance(poi, dict) and poi.get("id"):
        return f"poi `{poi['id']}`"
    return f"poi at index {index}"


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == []


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int_between(value: Any, minimum: int, maximum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def _minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _split_list(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_array(value: str | None, label: str) -> list[Any]:
    if value is None or not value.strip():
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise PoiCatalogError(f"{label}: must be a JSON array.")
    return parsed


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _to_number(value: str | None) -> float | int | str:
    value = _clean(value)
    if value == "":
        return ""
    number = float(value)
    return int(number) if number.is_integer() else number


def _to_int(value: str | None) -> int | str:
    value = _clean(value)
    if value == "":
        return ""
    return int(value)
