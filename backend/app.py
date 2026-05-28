from copy import deepcopy
from pathlib import Path
import csv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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


class AdjustRequest(BaseModel):
    adjustmentId: str


ADJUSTMENT_OPTIONS = [
    {"adjustmentId": "queueTooLong", "label": "餐厅排队太久"},
    {"adjustmentId": "budgetTo100", "label": "预算降到100"},
    {"adjustmentId": "noCoffee", "label": "不要咖啡"},
    {"adjustmentId": "onlyTwoHours", "label": "只剩2小时"},
    {"adjustmentId": "morePhotoFriendly", "label": "想更适合拍照"},
]


BASE_CONSTRAINTS = {
    "rawText": "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队。",
    "startLocation": "湖滨银泰 in77",
    "timeRange": {"start": "14:00", "end": "18:00"},
    "budgetPerPerson": 150,
    "preferences": ["西湖", "咖啡", "晚餐", "少排队"],
    "pace": "轻松",
}


POIS = {
    "start_in77": {
        "poiId": "start_in77",
        "name": "湖滨银泰 in77",
        "type": "起点",
        "area": "湖滨",
        "arrivalTime": "14:00",
        "leaveTime": "14:05",
        "stayMinutes": 5,
        "pricePerPerson": 0,
        "waitRisk": "低",
        "rating": "4.7",
        "tags": ["出发点", "商圈", "地铁可达"],
        "riskTip": "商圈人流较多，建议按导航从最近出口出发。",
        "recommendReason": "作为湖滨核心商圈，适合作为西湖半日路线的集合与出发点。",
        "location": {"lat": 30.2572, "lng": 120.1648},
    },
    "scenic_broken_bridge": {
        "poiId": "scenic_broken_bridge",
        "name": "断桥残雪",
        "type": "景点",
        "area": "西湖",
        "arrivalTime": "14:20",
        "leaveTime": "15:05",
        "stayMinutes": 45,
        "pricePerPerson": 0,
        "waitRisk": "中",
        "rating": "4.6",
        "tags": ["西湖经典", "拍照", "步行友好"],
        "riskTip": "热门点位游客较多，拍照需要避开桥面拥挤区域。",
        "recommendReason": "离湖滨出发点较近，是西湖经典景观点，适合第一站快速进入游览状态。",
        "location": {"lat": 30.2614, "lng": 120.1536},
    },
    "cafe_lakeside_baita": {
        "poiId": "cafe_lakeside_baita",
        "name": "湖畔白塔咖啡",
        "type": "咖啡",
        "area": "西湖",
        "arrivalTime": "15:20",
        "leaveTime": "15:55",
        "stayMinutes": 35,
        "pricePerPerson": 38,
        "waitRisk": "低",
        "rating": "4.5",
        "tags": ["休息", "湖景", "轻松"],
        "riskTip": "临窗座位可能需要等待，非临窗座更稳定。",
        "recommendReason": "安排在景点之后作为中途休息点，能降低路线疲劳感。",
        "location": {"lat": 30.2595, "lng": 120.1568},
    },
    "dinner_xinbailu_hubin": {
        "poiId": "dinner_xinbailu_hubin",
        "name": "新白鹿餐厅湖滨店",
        "type": "餐厅",
        "area": "湖滨",
        "arrivalTime": "16:25",
        "leaveTime": "17:10",
        "stayMinutes": 45,
        "pricePerPerson": 82,
        "waitRisk": "低-中",
        "rating": "4.4",
        "tags": ["杭帮菜", "晚餐", "预算适中"],
        "riskTip": "晚餐高峰可能排队，建议提前到店或保留备选餐厅。",
        "recommendReason": "回到湖滨商圈收尾，方便晚餐后继续逛街或返程。",
        "location": {"lat": 30.2565, "lng": 120.1642},
    },
    "dinner_zhiweiguan_hubin": {
        "poiId": "dinner_zhiweiguan_hubin",
        "name": "知味观湖滨店",
        "type": "餐厅",
        "area": "湖滨",
        "arrivalTime": "16:25",
        "leaveTime": "17:05",
        "stayMinutes": 40,
        "pricePerPerson": 58,
        "waitRisk": "低",
        "rating": "4.3",
        "tags": ["平价", "杭州小吃", "晚餐"],
        "riskTip": "热门时段仍可能人多，但预算压力更低。",
        "recommendReason": "预算降到100以内后，替换为人均更低且仍在湖滨附近的餐厅。",
        "location": {"lat": 30.2559, "lng": 120.1637},
    },
    "dinner_waipojia_hubin": {
        "poiId": "dinner_waipojia_hubin",
        "name": "外婆家湖滨店",
        "type": "餐厅",
        "area": "湖滨",
        "arrivalTime": "16:25",
        "leaveTime": "17:10",
        "stayMinutes": 45,
        "pricePerPerson": 75,
        "waitRisk": "低",
        "rating": "4.4",
        "tags": ["杭帮菜", "低等待", "商圈"],
        "riskTip": "热门时段可能等位，建议作为低等待优先备选。",
        "recommendReason": "餐厅排队风险升高时，用距离相近且等待风险更低的餐厅替换。",
        "location": {"lat": 30.2576, "lng": 120.1653},
    },
    "rest_lakeside_light": {
        "poiId": "rest_lakeside_light",
        "name": "湖滨轻休息点",
        "type": "轻休息",
        "area": "湖滨",
        "arrivalTime": "15:20",
        "leaveTime": "15:45",
        "stayMinutes": 25,
        "pricePerPerson": 22,
        "waitRisk": "低",
        "rating": "4.2",
        "tags": ["轻休息", "低消费", "少排队"],
        "riskTip": "体验感弱于咖啡馆，但更轻量稳定。",
        "recommendReason": "用户不要咖啡时，保留中途休息节奏并降低消费。",
        "location": {"lat": 30.2582, "lng": 120.1602},
    },
    "photo_beishan_view": {
        "poiId": "photo_beishan_view",
        "name": "北山街湖景拍照点",
        "type": "拍照点",
        "area": "西湖",
        "arrivalTime": "14:20",
        "leaveTime": "15:05",
        "stayMinutes": 45,
        "pricePerPerson": 0,
        "waitRisk": "中",
        "rating": "4.6",
        "tags": ["拍照", "湖景", "更出片"],
        "riskTip": "拍照体验受天气和人流影响。",
        "recommendReason": "用户希望更适合拍照时，替换为更强调湖景和出片效果的点位。",
        "location": {"lat": 30.2632, "lng": 120.1518},
    },
}


def _timeline_for(poi_ids: list[str]) -> list[dict]:
    title_by_id = {
        "start_in77": "湖滨银泰 in77 出发",
        "scenic_broken_bridge": "到达断桥残雪",
        "photo_beishan_view": "到达北山街湖景拍照点",
        "cafe_lakeside_baita": "到达湖畔白塔咖啡",
        "rest_lakeside_light": "到达湖滨轻休息点",
        "dinner_xinbailu_hubin": "到达新白鹿餐厅湖滨店",
        "dinner_zhiweiguan_hubin": "到达知味观湖滨店",
        "dinner_waipojia_hubin": "到达外婆家湖滨店",
    }
    return [
        {
            "itemId": f"tl_{poi_id}",
            "time": POIS[poi_id]["arrivalTime"],
            "title": title_by_id.get(poi_id, f"到达{POIS[poi_id]['name']}"),
            "description": POIS[poi_id]["recommendReason"],
            "poiId": poi_id,
        }
        for poi_id in poi_ids
    ]


def _transport_for(poi_ids: list[str]) -> list[dict]:
    segments = []
    for index in range(len(poi_ids) - 1):
        from_id = poi_ids[index]
        to_id = poi_ids[index + 1]
        segments.append(
            {
                "fromPoiId": from_id,
                "toPoiId": to_id,
                "mode": "walk",
                "durationText": "步行约12分钟" if index == 0 else "步行约10分钟",
                "distanceText": "约700m",
            }
        )
    return segments


def _build_route(
    route_id: str,
    title: str,
    poi_ids: list[str],
    duration_text: str,
    budget_text: str,
    walk_text: str,
    wait_risk_text: str,
    reason: str,
    diff: dict | None = None,
) -> dict:
    return {
        "routeId": route_id,
        "scenario": "westlake_now_go",
        "constraints": deepcopy(BASE_CONSTRAINTS),
        "routeSummary": {
            "title": title,
            "durationText": duration_text,
            "budgetText": budget_text,
            "walkText": walk_text,
            "waitRiskText": wait_risk_text,
            "reason": reason,
        },
        "pois": [deepcopy(POIS[poi_id]) for poi_id in poi_ids],
        "timeline": _timeline_for(poi_ids),
        "transportSegments": _transport_for(poi_ids),
        "adjustmentOptions": deepcopy(ADJUSTMENT_OPTIONS),
        "diff": diff,
    }


def default_route() -> dict:
    return _build_route(
        "route_default_westlake_halfday",
        "轻松西湖半日线",
        ["start_in77", "scenic_broken_bridge", "cafe_lakeside_baita", "dinner_xinbailu_hubin"],
        "2小时46分钟",
        "人均120元",
        "步行2.3km",
        "等待低-中",
        "从湖滨银泰出发，先进入西湖经典景观点，中途安排咖啡休息，最后回到湖滨商圈吃晚饭，整体少绕路且预算可控。",
    )


ADJUSTED_ROUTES = {
    "queueTooLong": _build_route(
        "route_queue_too_long",
        "低等待西湖半日线",
        ["start_in77", "scenic_broken_bridge", "cafe_lakeside_baita", "dinner_waipojia_hubin"],
        "2小时42分钟",
        "人均113元",
        "步行2.4km",
        "等待低",
        "已保留西湖游览和咖啡休息，只把晚餐换成等待风险更低的餐厅。",
        {
            "summary": "已保留西湖核心游览和咖啡休息，只把晚餐换成低等待餐厅。",
            "changedPoiIds": ["dinner_xinbailu_hubin", "dinner_waipojia_hubin"],
            "keptPoiIds": ["start_in77", "scenic_broken_bridge", "cafe_lakeside_baita"],
        },
    ),
    "budgetTo100": _build_route(
        "route_budget_to_100",
        "百元内西湖半日线",
        ["start_in77", "scenic_broken_bridge", "cafe_lakeside_baita", "dinner_zhiweiguan_hubin"],
        "2小时38分钟",
        "人均96元",
        "步行2.3km",
        "等待低",
        "预算降到100以内后，保留咖啡休息，把晚餐替换为更平价的湖滨餐厅。",
        {
            "summary": "已将晚餐替换为人均更低的知味观湖滨店，路线结构保持不变。",
            "changedPoiIds": ["dinner_xinbailu_hubin", "dinner_zhiweiguan_hubin"],
            "keptPoiIds": ["start_in77", "scenic_broken_bridge", "cafe_lakeside_baita"],
        },
    ),
    "noCoffee": _build_route(
        "route_no_coffee",
        "无咖啡轻松西湖线",
        ["start_in77", "scenic_broken_bridge", "rest_lakeside_light", "dinner_xinbailu_hubin"],
        "2小时30分钟",
        "人均104元",
        "步行2.1km",
        "等待低-中",
        "用户不想去咖啡店，因此替换为低消费轻休息点，仍保留中途休息节奏。",
        {
            "summary": "已把咖啡站替换成轻休息点，保留中途休息但降低消费。",
            "changedPoiIds": ["cafe_lakeside_baita", "rest_lakeside_light"],
            "keptPoiIds": ["start_in77", "scenic_broken_bridge", "dinner_xinbailu_hubin"],
        },
    ),
    "onlyTwoHours": _build_route(
        "route_only_two_hours",
        "2小时压缩西湖线",
        ["start_in77", "scenic_broken_bridge", "dinner_xinbailu_hubin"],
        "1小时58分钟",
        "人均82元",
        "步行1.6km",
        "等待低-中",
        "时间只剩2小时，已删除咖啡站，保留西湖核心游览和晚餐收尾。",
        {
            "summary": "已删除咖啡站并压缩停留时间，保留西湖游览和晚餐。",
            "changedPoiIds": ["cafe_lakeside_baita"],
            "keptPoiIds": ["start_in77", "scenic_broken_bridge", "dinner_xinbailu_hubin"],
        },
    ),
    "morePhotoFriendly": _build_route(
        "route_more_photo_friendly",
        "更出片西湖半日线",
        ["start_in77", "photo_beishan_view", "cafe_lakeside_baita", "dinner_xinbailu_hubin"],
        "2小时50分钟",
        "人均120元",
        "步行2.5km",
        "等待低-中",
        "用户希望更适合拍照，因此把经典景点替换为更强调湖景和出片效果的点位。",
        {
            "summary": "已把断桥残雪替换成更适合拍照的北山街湖景点，其他安排保持不变。",
            "changedPoiIds": ["scenic_broken_bridge", "photo_beishan_view"],
            "keptPoiIds": ["start_in77", "cafe_lakeside_baita", "dinner_xinbailu_hubin"],
        },
    ),
}


@app.get("/api/health")
def health() -> dict:
    return {"message": "服务正常"}


@app.post("/api/parse")
def parse_text(request: TextRequest) -> dict:
    parsed = deepcopy(BASE_CONSTRAINTS)
    if request.text:
        parsed["rawText"] = request.text
    return {"parsed": parsed}


@app.post("/api/route/generate")
def generate_route(_: TextRequest) -> dict:
    return {"routeData": default_route()}


@app.post("/api/route/adjust")
def adjust_route(request: AdjustRequest) -> dict:
    route = ADJUSTED_ROUTES.get(request.adjustmentId)
    if route is None:
        return {"error": "这个调整暂时不支持", "supportedAdjustmentIds": list(ADJUSTED_ROUTES)}
    return {"routeData": deepcopy(route)}


@app.get("/api/pois")
def list_pois() -> dict:
    csv_path = Path(__file__).resolve().parents[1] / "data" / "pois.csv"
    if not csv_path.exists():
        return {"pois": list(POIS.values())}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    return {"pois": rows}
