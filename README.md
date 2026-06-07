# Westlake Now

面向杭州西湖湖滨“现在就出发”场景的 AI 本地路线规划产品。

Westlake Now 不是一个让 LLM 直接生成旅游攻略的工具，而是一个将用户自然语言需求转化为可执行路线的本地路线规划系统。它通过 LLM / intent parser 理解用户意图，再由后端 `routePlanner` 基于真实 POI 候选池生成路线，前端负责展示时间轴、地点卡片、地图和导航入口，帮助用户从“一句话需求”快速进入“现在能走的路线”。

## Online Demo

- Frontend Demo: [https://cityroutemate.netlify.app](https://cityroutemate.netlify.app/)
- Backend Service: [https://route-backend-amyh.onrender.com](https://route-backend-amyh.onrender.com/)
- Health Check: [https://route-backend-amyh.onrender.com/health](https://route-backend-amyh.onrender.com/health)

## Product Design

完整产品设计方案见：[docs/product-design.md](docs/product-design.md)

## What Is Westlake Now?

在西湖湖滨这样的即时出行场景中，用户往往不是提前完整规划，而是临时决定：

- 我现在在哪里？
- 接下来 2-4 小时怎么走？
- 想逛西湖、拍照、喝咖啡、吃饭，怎么串起来？
- 预算有限怎么办？
- 餐厅排队太久怎么办？
- 只剩 2 小时怎么办？
- 不想喝咖啡了怎么办？

传统攻略内容丰富，但无法直接根据现场变化调整路线。纯 LLM 生成攻略又容易出现地点不可控、路线不顺、距离不准确、调整原因不透明等问题。

Westlake Now 的设计思路是：

> LLM 负责理解用户自然语言，routePlanner 负责路线决策，poiCatalog 提供真实 POI 候选池，前端地图和导航完成执行闭环。

## Core Features

### Natural Language Route Generation

用户可以输入一句自然语言需求，例如：

```text
我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队
```

系统会识别其中的出发地、时间、预算和偏好，并生成一条当前可执行路线。

### Local POI-based Route Planning

路线不是由 LLM 直接编写，而是由后端 `routePlanner` 基于本地 POI 数据生成。

当前 POI 候选池包含基于高德来源信息整理的真实地点，包含经纬度、地址、类型、人均成本、停留时间、等待风险、体验标签和评分字段。

### Route + Diff

系统不仅返回当前路线，还会返回本次调整的变化说明。

例如用户输入：

```text
不想喝咖啡了
```

系统会将咖啡节点替换为非咖啡缓冲点，并通过 `diff` 告诉用户：

- 原节点是什么
- 新节点是什么
- 人均预算如何变化
- 总时长如何变化
- 步行距离如何变化

### Five High-frequency Adjustment Scenarios

当前版本优先覆盖五个现场高频路线调整场景：

- 餐厅排队太久
- 不要咖啡
- 预算降到 100
- 只剩 2 小时
- 想更适合拍照

### Mobile-first Experience

产品按照移动端即时出行场景设计，支持：

- 首页自然语言输入
- 使用当前位置
- 路线概览
- 下一步行动卡片
- 路线时间轴
- 地点卡片
- 地图 Tab
- 底部操作栏
- “出发”跳转高德导航

### AMap Map and Navigation

当前高德能力用于：

- POI 数据来源追溯
- 前端真实高德地图展示
- 高德定位
- 高德导航跳转
- 前端距离判断

当前版本没有将高德实时路径规划 Web 服务作为后端路线决策主链路。后端 V1 使用经纬度直线距离估算步行时间，后续可以替换为高德步行路径规划。

## Screenshots

![首页自然语言输入](docs/assets/product-design/01-home-input.png)

![路线时间轴](docs/assets/product-design/02-route-timeline.png)

![地图路线展示](docs/assets/product-design/03-route-map.png)

## System Architecture

```text
User Natural Language Input
  ↓
Frontend Mobile Web App
  ↓
POST /api/chat-route
  ↓
LLM / Intent Parser
  ↓
Rule-based Fallback
  ↓
routePlanner
  ↓
POI Catalog
  ↓
routeData
  ↓
Frontend Route Timeline / Place Cards / Map / Navigation
```

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `frontend/` | Mobile-first route experience, route cards, timeline, map, navigation entry |
| `backend/` | API service, intent parsing, route planning, route adjustment |
| `data/` | POI source data |
| `docs/` | API contract, route rules, product design documentation |

## Why Not Let LLM Generate the Route Directly?

Westlake Now does not ask LLM to directly generate a full travel route. Instead, LLM is only used to parse user intent into structured route constraints, such as:

- `intent`
- `constraints`
- `avoidTypes`
- `budgetMax`
- `durationMinutes`
- `preferPhoto`
- `preferLowWait`

This avoids common LLM risks:

- hallucinated places
- unstable route order
- inaccurate distance or budget
- hard-to-explain changes
- frontend-unfriendly response structures

The actual route decision is handled by `routePlanner`, which selects POIs from the local candidate pool and outputs stable `routeData`.

## API Overview

Current main endpoint:

```http
POST /api/chat-route
```

Request example:

```json
{
  "message": "我想现在出发逛西湖"
}
```

Response format:

```json
{
  "routeData": {
    "constraints": {},
    "places": [],
    "optimizedPlaces": [],
    "route": {},
    "diff": null,
    "debug": {},
    "message": "",
    "adjustmentButtons": []
  }
}
```

Core frontend fields:

- `places`: POI detail list
- `optimizedPlaces`: route-ordered POI list for frontend rendering
- `route.placeIds` / `route.order`: stable route order
- `diff`: route adjustment explanation
- `debug`: route planning and adjustment debug information

## Data

The route planner uses local POI data:

```text
data/pois.csv
```

POI types include:

```json
{
  "start": 1,
  "scenic": 4,
  "photo": 4,
  "coffee": 4,
  "dinner": 6,
  "mall": 3,
  "rest": 1,
  "snack": 2
}
```

Each POI contains fields such as:

- `id`
- `amapId`
- `name`
- `type`
- `address`
- `location`
- `openHoursText`
- `avgCost`
- `rating`
- `tags`
- `experienceTags`
- `stayMinutes`
- `waitRisk`
- `crowdRisk`
- `photoScore`
- `restScore`
- `chatScore`
- `classicScore`
- `localFlavorScore`
- `budgetScore`
- `walkFriendlyScore`

Risk fields and score fields are used for route ranking and fallback decisions. They are estimates, not real-time guarantees.

## Project Structure

```text
.
├── backend/                 # Backend API and route planning logic
├── data/                    # Local POI data
│   └── pois.csv
├── docs/                    # Product and project documentation
│   ├── assets/
│   │   └── product-design/
│   └── product-design.md
├── frontend/                # Mobile-first frontend app
├── README.md
└── netlify.toml
```

## Local Development

### Frontend

The frontend is a native HTML / CSS / JavaScript demo and does not require `npm install`.

```bash
cd frontend
node server.mjs
```

Then open the local URL printed in the terminal. You can also open `frontend/index.html` directly for a static preview.

### Backend

Run from the repository root:

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

### Environment Variables

Frontend AMap configuration and backend API base URL should be configured according to the project environment files.

If running locally, please check:

- `frontend/src/config.js`
- backend environment variables for LLM and API configuration

## Current Version Boundary

Current version is intentionally scoped to a small and controllable MVP.

It does not claim to support:

- full-city route planning
- multi-day travel planning
- real-time queue prediction
- real-time crowd prediction
- guaranteed open hours
- full natural language understanding
- complex machine learning ranking
- hotel, ticket, booking or transaction flows
- AMap real-time route planning as the backend decision-making core

Current walking time is estimated mainly based on straight-line distance between coordinates. Future versions can replace this with AMap walking route planning.

## Roadmap

### Data Layer

- Expand POI coverage
- Add more POI types
- Improve open-hour reliability
- Add real-time crowd or queue signals
- Build POI quality validation

### Route Planning Layer

- Integrate AMap walking route planning
- Replace straight-line distance estimation
- Support more complex time-window constraints
- Improve multi-objective scoring
- Add route conflict explanation

### LLM Layer

- Improve multi-turn context handling
- Support more natural language adjustment expressions
- Add clarification questions
- Strengthen structured output validation

### Frontend Experience

- Add route history
- Add route sharing
- Add route comparison
- Improve map interactions
- Improve error and fallback explanations

## Hackathon Review Focus

### Completeness

The project has completed a full route experience loop:

```text
Natural language input
→ Intent parsing
→ Route generation
→ Route adjustment
→ Timeline and cards
→ Map display
→ Navigation jump
```

### Innovation

The key innovation is not simply using LLM, but using LLM in a controlled position:

```text
LLM for intent understanding
routePlanner for route decision
POI Catalog for trusted local data
route + diff for explainable adjustment
```

### Practical Value

The product is designed for a concrete scenario: immediate local travel around Westlake Hubin. It focuses on producing a route that users can actually view, adjust and start navigating.

### Boundary Control

The project clearly separates completed capabilities from future work and avoids overclaiming real-time queue, real-time crowd, full-city planning or full natural language understanding.

## Team

This project was completed by a two-person team.

- Product and frontend: product definition, MVP scope, mobile interaction design, frontend implementation, routeData contract alignment, demo flow, deployment validation and submission materials.
- Backend: backend service, routePlanner, POI data integration, LLM / fallback intent parsing, route APIs and deployment support.

## License

This project is submitted as a hackathon project. License information can be added later if needed.
