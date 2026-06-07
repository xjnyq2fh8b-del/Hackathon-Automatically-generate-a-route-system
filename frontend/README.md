# 西湖即时路线决策 Agent

一个原生 HTML、CSS、JavaScript 实现的移动端静态前端 Demo。当前版本用于黑客松演示，不依赖 npm、不使用框架，默认请求 Render 线上后端。

## 启动方式

在本目录运行：

```bash
node server.mjs
```

然后按终端输出的端口在浏览器里打开本地预览页。

也可以直接双击打开 `index.html` 预览。

## 当前可点击功能：

- 自然语言输入与示例需求填充
- 偏好标签选择
- 麦克风演示状态切换
- 生成路线三步加载
- 路线总览、交通方案、地图、时间轴、目的地卡片展示
- 地图 marker、时间轴、目的地卡片联动高亮
- “餐厅排队太久”局部替换晚餐并展示新旧方案对比
- “不要咖啡”删除咖啡节点并更新路线指标
- “预算降到 100”“只剩 2 小时”“想更适合拍照”策略调整
- 目的地卡片上移、下移、删除、替换
- 采用新方案、恢复原方案

## 线上接口配置

- 公开后端地址配置在 `src/config.js`。
- 当前核心接口是 `POST /api/chat-route`。
- 请求体只发送 `{ "message": "用户输入内容" }`。

## 后续接入位置

- LLM 意图解析：替换 `src/app.js` 中的 `buildConstraintsFromInput`
- 真实 POI 数据：替换 `basePois`、`alternativePois` 和路线生成逻辑
- 高德地图 API：替换 `renderMap` 对应的静态仿地图
- 后端服务：将 `applyAdjustment`、`recalculateRoute` 等逻辑迁移为接口调用
