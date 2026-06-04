# Docs

本目录存放路线规划 Agent 的长期维护文档。文档按用途拆分，避免同一信息散落在多个文件中。

## 文档索引

| 文件 | 用途 | 维护规则 |
| --- | --- | --- |
| `api-contract.md` | 第一版前后端 mock API 契约 | 接口字段、请求格式、响应格式变化时更新 |
| `routing-rules.md` | 产品边界、路线生成、POI 筛选、调整策略和评分规则 | 只沉淀路线规划相关的产品和算法规则 |
| `poiCatalog字段说明.md` | 后端 POI 候选池字段说明 | POI 数据源、字段、校验口径变化时更新 |
| `routeData.sample.json` | `routeData` 完整返回样例 | 与 `api-contract.md` 和后端 mock 返回保持一致 |

## 归属规则

- 项目总览、启动方式和当前能力放在根目录 `README.md`。
- 协作规则、红线操作和分支流程放在根目录 `AGENTS.md`。
- 接口契约只放在 `docs/api-contract.md`，不要散写到前端或后端 README。
- 路线规划规则只放在 `docs/routing-rules.md`。
- POI 候选池字段只放在 `docs/poiCatalog字段说明.md`。

## 清理规则

- 过期说明应合并到对应主文档后删除。
- 临时草稿不放入 `docs/`；确认进入项目规则后再沉淀为正式文档。
- 与路线规划 Agent 无关的资料不放入本目录。
- 同一主题只保留一份主文档，历史版本如需保留，后续统一放入 `docs/archive/`。
