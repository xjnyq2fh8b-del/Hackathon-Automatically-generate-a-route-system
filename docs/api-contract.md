# 路线 Agent 第一版后端 mock API 契约

本契约用于 P0 前后端 mock 联调。第一版不接真实 LLM、高德、数据库或推荐算法。

## 通用约定

- 请求和返回均使用 JSON。
- 字段名使用英文 `camelCase`。
- 路线接口统一返回 `{ "routeData": ... }`。
- 第一版调整接口每次返回完整新 `route` 和 `diff`，不返回 `routePatch`。
- `routeData` 顶层展示结构固定为 `constraints + places + optimizedPlaces + route + adjustmentButtons + diff + debug + message`。
- 后端内部算法字段不得直接出现在 `routeData.places` 或 `routeData.route` 中；路线顺序诊断信息统一放在 `routeData.debug`。

## 前后端数据边界

第一版先稳定接口结构，后端不能一边做算法一边随意改返回字段。前端只关心最终选中的路线，后端可以维护更丰富的候选池和评分字段，但返回前必须转换为展示结构。

### 前端展示字段

`routeData` 只包含以下顶层字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `constraints` | object | 用户约束摘要，用于页面展示系统理解到的出发地、时间、预算、偏好等 |
| `places` | array | 本次路线展示所需地点列表，只放被前端渲染需要的字段；应与最终路线顺序一致 |
| `optimizedPlaces` | array | 已按路线顺序优化后的地点列表，前端编号、地图连线、下一站优先使用这个顺序 |
| `route` | object | 当前推荐路线，包含顺序、时间轴、交通段和路线总指标 |
| `adjustmentButtons` | array | 当前可用快捷调整按钮 |
| `diff` | object 或 null | 调整后的新旧方案对比；默认路线为 `null` |
| `debug` | object | 路线优化诊断字段，只用于排查顺路逻辑，不作为页面主展示 |
| `message` | string | 后端给前端展示的轻提示；默认空字符串 |

`places` 是展示层地点结构，允许字段为：

```text
id
type
name
shortName
address
openHours
rating
price
tags
reason
note
map
location
```

`route` 是展示层路线结构，允许字段为：

```text
id
label
name
explanation
durationMinutes
budgetPerPerson
walkingKm
waitRisk
placeIds
order
timeline
transportSummary
transportSegments
```

`debug` 固定包含以下字段：

```text
beforeOrder
afterOrder
routeOptimized
fallbackUsed
optimizeMethod
routeTotalDistance
routeTotalDuration
```

`diff.rows` 固定为对象数组：

```json
[
  { "label": "晚餐", "value": "新白鹿餐厅湖滨店 -> 弄堂里湖滨店" }
]
```

### 后端内部算法字段

以下字段属于后端内部候选池和评分逻辑，不得直接返回给前端：

```text
poiCatalog
avgCost
stayMinutes
waitRisk
crowdRisk
photoScore
quietScore
restScore
familyScore
chatScore
classicScore
budgetScore
walkFriendlyScore
localFlavorScore
```

注意：`route.waitRisk` 是路线级展示摘要，可以保留；`poiCatalog.waitRisk` 是 POI 算法字段，不应透传到 `places`。

## GET /api/health

用于确认后端服务是否正常。

```json
{
  "message": "服务正常"
}
```

## POST /api/parse

第一版只返回 mock 约束。后续这里替换为 LLM 解析。

### Request

```json
{
  "text": "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队。"
}
```

### Response

```json
{
  "constraints": {
    "summary": "湖滨银泰｜14:00-18:00｜人均150｜少排队",
    "chips": [
      { "key": "出发地", "value": "湖滨银泰 in77" },
      { "key": "时间", "value": "14:00-18:00" },
      { "key": "预算", "value": "人均150" },
      { "key": "偏好", "value": "少排队" }
    ]
  }
}
```

## POST /api/route/generate

前端点击“生成可执行路线”时调用。P0 固定返回默认路线。

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
    "constraints": {},
    "places": [],
    "route": {},
    "adjustmentButtons": [],
    "diff": null,
    "message": ""
  }
}
```

完整样例见 `docs/routeData.sample.json`。

## POST /api/route/adjust

前端触发快捷调整或地点卡片单节点调整时调用。P0 根据请求返回完整新路线和 diff。

### 快捷调整 Request

```json
{
  "adjustmentType": "restaurantBusy"
}
```

### adjustmentType

| adjustmentType | 用户按钮 | P0 返回变化 |
|---|---|---|
| `restaurantBusy` | 餐厅排队太久 | 新白鹿餐厅湖滨店 -> 弄堂里湖滨店 |
| `budget100` | 预算降到100 | 咖啡改轻休息点，晚餐改弄堂里 |
| `noCoffee` | 不要咖啡 | 删除湖畔白塔咖啡 |
| `twoHours` | 只剩2小时 | 只保留起点、断桥和晚餐 |
| `photo` | 想更适合拍照 | 新增北山街湖景点 |

### 地点卡片单节点调整 Request

```json
{
  "action": "delete",
  "nodeId": "baitacoffee",
  "route": {}
}
```

### action

| action | 含义 | P0 规则 |
|---|---|---|
| `replace` | 替换当前节点 | 晚餐触发 `restaurantBusy`，咖啡触发 `budget100`，景点触发 `photo` |
| `delete` | 删除当前节点 | 起点不能删除 |
| `moveUp` | 节点上移 | 到边界时返回提示 |
| `moveDown` | 节点下移 | 到边界时返回提示 |

### Response

```json
{
  "routeData": {
    "constraints": {},
    "places": [],
    "route": {
      "id": "westlake-half-day",
      "label": "当前推荐",
      "name": "轻松西湖半日线",
      "explanation": "已删除咖啡节点，路线更短。",
      "durationMinutes": 125,
      "budgetPerPerson": 78,
      "walkingKm": 2.0,
      "waitRisk": "中",
      "placeIds": ["in77", "brokenBridge", "xinbailu"],
      "timeline": [],
      "transportSummary": "",
      "transportSegments": []
    },
    "adjustmentButtons": [],
    "diff": {
      "title": "已删除咖啡点",
      "action": "中途少一次停留，直接从景点前往晚餐。",
      "rows": [
        { "label": "删除节点", "value": "湖畔白塔咖啡" }
      ]
    },
    "message": ""
  }
}
```

## GET /api/pois

返回 P0 可用的 mock 地点列表。为兼容旧入口保留该接口，但返回字段为新契约的 `places`。

```json
{
  "places": []
}
```
