# poiCatalog 字段说明

本文件说明 `data/poiCatalog.sample.csv` 与 `data/poiCatalog.sample.json` 的字段含义。该候选池用于后端规则引擎筛选、评分和路线组合，不是前端展示契约。

## 数据来源边界

- 当前样例数据来自高德开放平台 POI 检索与详情接口，范围限定在湖滨银泰 in77、断桥、白堤、北山街、西湖音乐喷泉、湖滨步行街、少年宫、嘉里中心 / 武林路边缘附近。
- 高德未返回的真实字段不补编；`avgCost` 或 `rating` 使用 `0` 表示待人工补充。
- `waitRisk`、`crowdRisk` 和各类 score 是后端规则初始标签，不代表实时排队、人流或用户满意度，需要人工复核。
- 后端返回前端时必须转换为 `constraints / places / route / diff`，不得直接把算法字段透传到前端展示结构。

## 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 本地唯一 ID，后端规则引擎使用 |
| `amapId` | string | 是 | 高德 POI ID，用于追溯来源 |
| `name` | string | 是 | POI 名称 |
| `type` | enum | 是 | 只允许 `scenic`、`photo`、`coffee`、`dinner`、`rest`、`snack`、`mall`、`start` |
| `address` | string | 是 | 高德返回地址 |
| `location.lng` | number | 是 | CSV 中的经度字段 |
| `location.lat` / `location.lat` | number | 是 | CSV 中的纬度字段 |
| `location` | object | 是 | JSON 中使用 `{ "lng": number, "lat": number }` |
| `openHoursText` | string | 否 | 原始营业时间文本，用于人工查看和前端展示；不确定时可为空 |
| `openingHours` | array | 是 | 后端算法使用的结构化营业时段；未知时填空数组 `[]` |
| `openHoursConfidence` | enum | 是 | 营业时间置信度，只允许 `high`、`medium`、`low`、`unknown` |
| `avgCost` | number | 是 | 高德返回人均；`0` 表示未返回，待人工补充 |
| `rating` | number | 是 | 高德返回评分；`0` 表示未返回，待人工补充 |
| `source` | string | 是 | 当前为 `amap` |
| `tags` | string[] | 是 | 前端可展示的中文标签，例如“湖景”“低预算” |
| `experienceTags` | string[] | 是 | 后端规则引擎使用的英文标签，例如 `lake-view`、`budget` |
| `stayMinutes` | number | 是 | 规则引擎使用的建议停留时长 |
| `waitRisk` | enum | 是 | 只允许 `low`、`medium`、`high`，当前为规则初始估计 |
| `crowdRisk` | enum | 是 | 只允许 `low`、`medium`、`high`，当前为规则初始估计 |
| `photoScore` | integer | 是 | 拍照友好度，1-5 |
| `quietScore` | integer | 是 | 安静程度，1-5 |
| `restScore` | integer | 是 | 可休息程度，1-5 |
| `familyScore` | integer | 是 | 家庭友好度，1-5 |
| `chatScore` | integer | 是 | 适合聊天程度，1-5 |
| `classicScore` | integer | 是 | 西湖经典程度，1-5 |
| `localFlavorScore` | integer | 是 | 本地特色程度，1-5 |
| `budgetScore` | integer | 是 | 预算友好度，1-5 |
| `walkFriendlyScore` | integer | 是 | 少走路友好度，1-5 |
| `note` | string | 否 | 数据缺口、人工复核说明或规则备注 |

## 类型与候选池数量要求

当前样例共 25 个 POI：

| 类型 | 数量 | 用途 |
| --- | ---: | --- |
| `start` | 1 | 默认出发点 |
| `scenic` | 4 | 核心西湖体验 |
| `photo` | 4 | 拍照增强 |
| `coffee` | 4 | 中段缓冲 |
| `dinner` | 6 | 餐饮替换 |
| `mall` / `rest` / `snack` | 6 | 低预算、不要咖啡、时间压缩时兜底 |

校验口径：

1. `scenic` 至少 3 个。
2. `photo` 至少 3 个。
3. `coffee` 至少 3 个。
4. `dinner` 至少 3 个。
5. `bufferCandidates` 至少 6 个。
6. `nonCoffeeBufferCandidates` 至少 3 个。

`type=rest` 表示 POI 地点类型是轻休息点，和 `scenic`、`coffee`、`dinner` 同级；不要新增独立 `rest` 字段，也不要要求 `type=rest` 至少 3 个。

`restScore` 表示可休息程度，`coffee`、`mall`、`snack`、`scenic` 等类型也可以有较高 `restScore`。`restScore` 是后端算法字段，不直接返回给前端。

`bufferCandidates` 定义：

```text
type in ["coffee", "rest", "snack", "mall"]
或 restScore >= 4
或 experienceTags 包含 "rest-friendly"
```

`nonCoffeeBufferCandidates` 定义：

```text
属于 bufferCandidates
且 type != "coffee"
```

## CSV 填写规则

- `tags` 和 `experienceTags` 在 CSV 中用英文逗号分隔，例如 `"湖景,拍照,低预算"`。
- `location.lng` 和 `location.lat` 转换到 JSON 时合并为 `location: { "lng": ..., "lat": ... }`。
- `openingHours` 在 CSV 中填写 JSON 数组字符串，例如 `"[{""days"":[1,2,3,4,5],""periods"":[{""open"":""10:00"",""close"":""22:00"",""crossDay"":false}]}]"`。
- 所有 score 字段必须是 1-5 的整数。
- 不确定的真实数据不要猜，优先写 `0` 或在 `note` 中标注“待人工补充”。
- CSV 可以保留旧字段 `openHours`，转换脚本会原样迁移为 `openHoursText`。
- 简单 `HH:mm-HH:mm` 和 `24小时营业` 可以自动转换为 `openingHours`。
- 工作日 / 周末不同、多时段、节假日、异常跨日文本如果无法可靠解析，不要猜；转换脚本会保留 `openHoursText`，`openingHours` 为空数组，并输出 warning。
- `openHoursConfidence` 默认 `medium`；如果人工确认不可靠，可改成 `low` 或 `unknown`。

## 营业时间结构

`openHoursText` 保存原始文本，适合人工核对和前端展示。例如：

```text
周一至周五 10:00-22:00；周六至周日 09:00-23:00
```

`openingHours` 用于后端判断 POI 在某个时间是否营业。结构如下：

```json
[
  {
    "days": [1, 2, 3, 4, 5],
    "periods": [
      { "open": "10:00", "close": "22:00", "crossDay": false }
    ]
  },
  {
    "days": [6, 0],
    "periods": [
      { "open": "09:00", "close": "23:00", "crossDay": false }
    ]
  }
]
```

规则：

1. `days` 使用 0-6 表示星期，`0=周日`，`1=周一`，以此类推。
2. `periods` 支持多个时段，适合午市 / 晚市分段营业。
3. `open` 和 `close` 必须是 `HH:mm` 格式。
4. `crossDay=true` 表示跨日营业，例如 `18:00-02:00`。
5. `crossDay=false` 时，`close` 必须晚于 `open`。
6. `openingHours` 为空数组时，校验会输出 warning，但不会阻止 JSON 生成。
7. 全天开放可以用 `00:00-23:59` 表示，并在 `note` 中说明，或后续增加 `openType=always_open`。

## 预算计算规则

预算计算不能直接累加所有 POI 的 `avgCost`，必须结合 route node 的 `role` / `type` 判断：

1. `role=start` 或 `type=start` 不计入预算。
2. `scenic`、`photo` 默认不计入预算。
3. `coffee`、`dinner`、`snack` 默认计入预算。
4. `mall`、`rest` 默认不计入预算，除非节点或 POI 显式设置 `costIncludedByDefault=true`。
5. 如果同一个地点未来既可以作为起点，也可以作为消费点，优先通过 route node `role` 判断，不修改 POI 本身。
6. V1 中 `start` 类型只作为出发锚点，不参与预算累加。
