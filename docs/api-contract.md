# 路线 Agent 第一版 API 契约

本契约用于 P0 前后端联调。第一版所有接口先返回 mock 数据，不接真实 LLM、高德、数据库或推荐算法。

## 通用约定

- 请求和返回均使用 JSON。
- 字段名使用英文 `camelCase`。
- 后端统一返回 `{ "routeData": ... }`。
- P0 只定义成功态，错误态可先简单返回 `{ "error": "..." }`。
- P0 调整接口无状态：前端传 `adjustmentId`，后端返回对应 mock 新路线。

## GET /api/health

用于确认后端服务是否正常。

### Response

```json
{
  "message": "服务正常"
}
```

## POST /api/parse

第一版假装解析用户输入，返回结构化约束。后续这里替换为 LLM 解析。

### Request

```json
{
  "text": "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队。"
}
```

### Response

```json
{
  "parsed": {
    "rawText": "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队。",
    "startLocation": "湖滨银泰 in77",
    "timeRange": {
      "start": "14:00",
      "end": "18:00"
    },
    "budgetPerPerson": 150,
    "preferences": ["西湖", "咖啡", "晚餐", "少排队"],
    "pace": "轻松"
  }
}
```

## POST /api/route/generate

前端点击“生成路线”时调用。P0 先固定返回默认路线。

### Request

```json
{
  "text": "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队。"
}
```

### Response

```json
{
  "routeData": {
    "routeId": "route_default_westlake_halfday",
    "routeSummary": {},
    "pois": [],
    "timeline": [],
    "transportSegments": [],
    "adjustmentOptions": [],
    "diff": null
  }
}
```

完整样例见 `docs/routeData.sample.json`。

## POST /api/route/adjust

前端点击调整按钮时调用。P0 先支持固定的 5 个 `adjustmentId`。

### Request

```json
{
  "adjustmentId": "noCoffee"
}
```

### adjustmentId

| adjustmentId | 用户按钮 | P0 返回变化 |
|---|---|---|
| `queueTooLong` | 餐厅排队太久 | 新白鹿餐厅湖滨店 -> 外婆家湖滨店 |
| `budgetTo100` | 预算降到100 | 新白鹿餐厅湖滨店 -> 知味观湖滨店 |
| `noCoffee` | 不要咖啡 | 删除湖畔白塔咖啡 |
| `onlyTwoHours` | 只剩2小时 | 删除咖啡并压缩路线 |
| `morePhotoFriendly` | 想更适合拍照 | 断桥残雪 -> 北山街湖景拍照点 |

### Response

```json
{
  "routeData": {
    "routeId": "route_no_coffee",
    "routeSummary": {},
    "pois": [],
    "timeline": [],
    "transportSegments": [],
    "adjustmentOptions": [],
    "diff": {
      "summary": "已删除咖啡站，保留西湖游览和晚餐安排。",
      "changedPoiIds": ["cafe_lakeside_baita"],
      "keptPoiIds": ["start_in77", "scenic_broken_bridge", "dinner_xinbailu_hubin"]
    }
  }
}
```

## GET /api/pois

返回 P0 可用的 mock POI 列表。

### Response

```json
{
  "pois": [
    {
      "poiId": "scenic_broken_bridge",
      "name": "断桥残雪",
      "type": "景点",
      "tags": ["西湖经典", "拍照", "步行友好"]
    }
  ]
}
```

完整数据来源见 `data/pois.csv`。
