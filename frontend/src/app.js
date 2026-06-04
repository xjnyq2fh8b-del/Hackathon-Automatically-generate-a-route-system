const app = document.querySelector("#app");
const API_BASE_URL = "http://127.0.0.1:8000";
const USE_BACKEND_API = true;

const mockRouteData = {
  input: {
    defaultText:
      "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
    examples: [
      "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
      "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，预算人均120",
      "想找适合拍照但不要太网红的咖啡店，晚上顺路吃本地特色",
    ],
    preferenceTags: ["少排队", "少走路", "拍照好看", "本地特色", "安静", "带老人小孩"],
    defaultPreferences: ["少排队"],
  },
  labels: {
    typeText: {
      start: "起点",
      scenic: "景点",
      coffee: "咖啡",
      dinner: "晚餐",
      rest: "休息",
    },
    typeIcon: {
      start: "起",
      scenic: "景",
      coffee: "咖",
      dinner: "食",
      rest: "休",
    },
  },
  constraints: {
    summary: "湖滨银泰｜14:00-18:00｜人均150｜少排队",
    chips: [
      { key: "出发地", value: "湖滨银泰 in77" },
      { key: "时间", value: "14:00-18:00" },
      { key: "预算", value: "人均150" },
      { key: "偏好", value: "少排队" },
    ],
  },
  places: [
    {
      id: "in77",
      type: "start",
      name: "湖滨银泰 in77",
      shortName: "湖滨银泰",
      address: "上城区湖滨商圈",
      openHours: "全天可达",
      rating: "4.7",
      price: "免费",
      tags: ["地铁近", "集合方便", "商圈补给"],
      reason: "作为出发点，减少集合点和线路成本。",
      note: "",
      map: { x: 72, y: 28 },
    },
    {
      id: "brokenBridge",
      type: "scenic",
      name: "断桥残雪",
      shortName: "断桥残雪",
      address: "西湖区北山街",
      openHours: "全天开放",
      rating: "4.6",
      price: "免费",
      tags: ["西湖经典", "拍照友好", "游客友好"],
      reason: "先去断桥，能最快进入西湖氛围，也方便后面顺路去咖啡点。",
      note: "游客较多，但不影响路线执行。",
      map: { x: 42, y: 42 },
    },
    {
      id: "baitacoffee",
      type: "coffee",
      name: "湖畔白塔咖啡",
      shortName: "白塔咖啡",
      address: "湖滨路附近",
      openHours: "10:00-21:30",
      rating: "4.5",
      price: "人均42元",
      tags: ["安静", "低等待估计", "可休息"],
      reason: "安排在中段休息，既不打断游览，也给晚饭前留缓冲。",
      note: "低等待为估计标签，不代表实时排队。",
      map: { x: 55, y: 63 },
    },
    {
      id: "xinbailu",
      type: "dinner",
      name: "新白鹿餐厅湖滨店",
      shortName: "新白鹿",
      address: "上城区延安路附近",
      openHours: "10:30-21:30",
      rating: "4.4",
      price: "人均78元",
      tags: ["杭帮菜", "预算友好", "家庭友好"],
      reason: "最后回到湖滨附近吃晚饭，结束后打车或地铁都方便。",
      note: "晚高峰可能短时等待。",
      map: { x: 76, y: 72 },
    },
    {
      id: "nongtangli",
      type: "dinner",
      name: "弄堂里湖滨店",
      shortName: "弄堂里",
      address: "湖滨商圈附近",
      openHours: "10:30-21:00",
      rating: "4.3",
      price: "人均65元",
      tags: ["杭帮菜", "等待低", "预算更低"],
      reason: "比原餐厅等待风险更低，人均更低，距离路线也更顺。",
      note: "晚餐等待风险更低，适合作为当前替换点。",
      map: { x: 70, y: 70 },
    },
    {
      id: "convenienceRest",
      type: "rest",
      name: "湖滨轻休息点",
      shortName: "轻休息点",
      address: "湖滨步行街附近",
      openHours: "全天可达",
      rating: "4.2",
      price: "免费",
      tags: ["省预算", "少停留", "顺路"],
      reason: "保留休息缓冲，同时把预算留给晚餐。",
      note: "停留时间较短，适合预算收紧时使用。",
      map: { x: 60, y: 58 },
    },
    {
      id: "photoPoint",
      type: "scenic",
      name: "北山街湖景点",
      shortName: "北山街湖景",
      address: "西湖区北山街沿线",
      openHours: "全天开放",
      rating: "4.5",
      price: "免费",
      tags: ["湖景", "拍照好看", "不太网红"],
      reason: "比热门机位更分散，适合想拍照但不想太拥挤的路线。",
      note: "下午光线较柔和，但仍建议避开桥面人流。",
      map: { x: 36, y: 54 },
    },
  ],
  routes: {
    default: {
      id: "westlake-half-day",
      label: "当前推荐",
      name: "轻松西湖半日线",
      explanation: "先从湖滨银泰进入西湖核心景观，再安排咖啡休息，最后顺路吃晚饭。",
      durationMinutes: 166,
      budgetPerPerson: 120,
      walkingKm: 2.3,
      waitRisk: "低-中",
      placeIds: ["in77", "brokenBridge", "baitacoffee", "xinbailu"],
      timeline: [
        { placeId: "in77", arrive: "14:00", leave: "14:05" },
        { placeId: "brokenBridge", arrive: "14:17", leave: "14:52" },
        { placeId: "baitacoffee", arrive: "15:04", leave: "15:39" },
        { placeId: "xinbailu", arrive: "15:51", leave: "16:46" },
      ],
      transportSummary:
        "全程步行优先，单段最长约12分钟；如带老人小孩，可将咖啡到晚餐段改为打车。",
      transportSegments: [
        { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
        { fromId: "brokenBridge", toId: "baitacoffee", method: "步行", duration: "约8分钟" },
        { fromId: "baitacoffee", toId: "xinbailu", method: "步行", duration: "约10分钟" },
      ],
    },
  },
  adjustmentButtons: [
    { type: "restaurantBusy", label: "餐厅排队太久" },
    { type: "budget100", label: "预算降到100" },
    { type: "noCoffee", label: "不要咖啡" },
    { type: "twoHours", label: "只剩2小时" },
    { type: "photo", label: "想更适合拍照" },
  ],
  adjustments: {
    restaurantBusy: {
      route: {
        explanation: "已为你只替换晚餐点，其他安排保持不变。",
        durationMinutes: 152,
        budgetPerPerson: 108,
        walkingKm: 2.1,
        waitRisk: "低",
        placeIds: ["in77", "brokenBridge", "baitacoffee", "nongtangli"],
        timeline: [
          { placeId: "in77", arrive: "14:00", leave: "14:05" },
          { placeId: "brokenBridge", arrive: "14:17", leave: "14:52" },
          { placeId: "baitacoffee", arrive: "15:04", leave: "15:39" },
          { placeId: "nongtangli", arrive: "15:46", leave: "16:32" },
        ],
        transportSegments: [
          { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
          { fromId: "brokenBridge", toId: "baitacoffee", method: "步行", duration: "约8分钟" },
          { fromId: "baitacoffee", toId: "nongtangli", method: "步行", duration: "约7分钟" },
        ],
      },
      diff: {
        title: "已避开排队晚餐",
        action: "晚餐改为弄堂里湖滨店，其他节点保持不变。",
        rows: [
          { label: "晚餐", value: "新白鹿餐厅湖滨店 → 弄堂里湖滨店" },
          { label: "等待风险", value: "低-中 → 低" },
          { label: "预计人均", value: "120元 → 108元" },
          { label: "总时长", value: "2小时46分钟 → 2小时32分钟" },
          { label: "步行距离", value: "2.3km → 2.1km" },
          { label: "保留节点", value: "湖滨银泰 in77、断桥残雪、湖畔白塔咖啡" },
        ],
      },
    },
    budget100: {
      route: {
        explanation: "已把预算压到人均100以内。",
        durationMinutes: 145,
        budgetPerPerson: 95,
        walkingKm: 2.0,
        waitRisk: "低",
        placeIds: ["in77", "brokenBridge", "convenienceRest", "nongtangli"],
        timeline: [
          { placeId: "in77", arrive: "14:00", leave: "14:05" },
          { placeId: "brokenBridge", arrive: "14:17", leave: "14:52" },
          { placeId: "convenienceRest", arrive: "15:00", leave: "15:12" },
          { placeId: "nongtangli", arrive: "15:20", leave: "16:05" },
        ],
        transportSegments: [
          { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
          { fromId: "brokenBridge", toId: "convenienceRest", method: "步行", duration: "约8分钟" },
          { fromId: "convenienceRest", toId: "nongtangli", method: "步行", duration: "约8分钟" },
        ],
      },
      diff: {
        title: "预算已压到 100 内",
        action: "咖啡改为轻休息点，晚餐改为更低预算方案。",
        rows: [
          { label: "预计人均", value: "120元 → 95元" },
          { label: "调整节点", value: "湖畔白塔咖啡 → 湖滨轻休息点；晚餐 → 弄堂里" },
          { label: "总时长", value: "2小时46分钟 → 2小时25分钟" },
          { label: "保留节点", value: "湖滨银泰 in77、断桥残雪" },
        ],
      },
    },
    noCoffee: {
      route: {
        explanation: "已删除咖啡节点，路线更短。",
        durationMinutes: 125,
        budgetPerPerson: 78,
        walkingKm: 2.0,
        waitRisk: "中",
        placeIds: ["in77", "brokenBridge", "xinbailu"],
        timeline: [
          { placeId: "in77", arrive: "14:00", leave: "14:05" },
          { placeId: "brokenBridge", arrive: "14:17", leave: "14:52" },
          { placeId: "xinbailu", arrive: "15:06", leave: "15:53" },
        ],
        transportSegments: [
          { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
          { fromId: "brokenBridge", toId: "xinbailu", method: "步行", duration: "约14分钟" },
        ],
      },
      diff: {
        title: "已删除咖啡点",
        action: "中途少一次停留，直接从景点前往晚餐。",
        rows: [
          { label: "删除节点", value: "湖畔白塔咖啡" },
          { label: "预计人均", value: "120元 → 78元" },
          { label: "总时长", value: "2小时46分钟 → 2小时05分钟" },
          { label: "步行距离", value: "2.3km → 2.0km" },
          { label: "保留节点", value: "湖滨银泰 in77、断桥残雪、新白鹿餐厅湖滨店" },
        ],
      },
    },
    twoHours: {
      route: {
        explanation: "已压缩到约2小时，优先保留核心景点和晚餐。",
        durationMinutes: 118,
        budgetPerPerson: 78,
        walkingKm: 1.8,
        waitRisk: "中",
        placeIds: ["in77", "brokenBridge", "xinbailu"],
        timeline: [
          { placeId: "in77", arrive: "14:00", leave: "14:05" },
          { placeId: "brokenBridge", arrive: "14:17", leave: "14:42" },
          { placeId: "xinbailu", arrive: "14:56", leave: "15:45" },
        ],
        transportSegments: [
          { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
          { fromId: "brokenBridge", toId: "xinbailu", method: "步行", duration: "约14分钟" },
        ],
      },
      diff: {
        title: "已压缩到 2 小时",
        action: "删除或压缩中途停留，牺牲一部分体验完整度。",
        rows: [
          { label: "总时长", value: "2小时46分钟 → 1小时58分钟" },
          { label: "调整方式", value: "只保留起点、断桥和晚餐" },
          { label: "保留节点", value: "湖滨银泰 in77、断桥残雪、新白鹿餐厅湖滨店" },
        ],
      },
    },
    photo: {
      route: {
        explanation: "已增加更适合拍照的湖景停留点。",
        durationMinutes: 175,
        budgetPerPerson: 120,
        walkingKm: 2.6,
        waitRisk: "低-中",
        placeIds: ["in77", "brokenBridge", "photoPoint", "baitacoffee", "xinbailu"],
        timeline: [
          { placeId: "in77", arrive: "14:00", leave: "14:05" },
          { placeId: "brokenBridge", arrive: "14:17", leave: "14:52" },
          { placeId: "photoPoint", arrive: "14:59", leave: "15:20" },
          { placeId: "baitacoffee", arrive: "15:29", leave: "16:04" },
          { placeId: "xinbailu", arrive: "16:14", leave: "17:01" },
        ],
        transportSegments: [
          { fromId: "in77", toId: "brokenBridge", method: "步行", duration: "约12分钟" },
          { fromId: "brokenBridge", toId: "photoPoint", method: "步行", duration: "约7分钟" },
          { fromId: "photoPoint", toId: "baitacoffee", method: "步行", duration: "约9分钟" },
          { fromId: "baitacoffee", toId: "xinbailu", method: "步行", duration: "约10分钟" },
        ],
      },
      diff: {
        title: "已加强拍照体验",
        action: "增加北山街湖景点，同时保留断桥。",
        rows: [
          { label: "新增节点", value: "北山街湖景点" },
          { label: "总时长", value: "2小时46分钟 → 2小时55分钟" },
          { label: "步行距离", value: "2.3km → 2.6km" },
          { label: "保留节点", value: "湖滨银泰 in77、断桥残雪、湖畔白塔咖啡、新白鹿餐厅湖滨店" },
        ],
      },
    },
  },
};

let placeById = Object.fromEntries(mockRouteData.places.map((place) => [place.id, place]));
const typeText = mockRouteData.labels.typeText;
const typeIcon = mockRouteData.labels.typeIcon;

let state = {
  view: "input",
  inputText: mockRouteData.input.defaultText,
  selectedPreferences: [...mockRouteData.input.defaultPreferences],
  micActive: false,
  loadingStep: 0,
  route: null,
  previousRoute: null,
  diff: null,
  selectedNodeId: null,
  activeTab: "route",
  drawerOpen: false,
  transportOpen: false,
  expandedNodes: [],
  activeAdjustment: null,
  toast: "",
  hint: "",
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function getPlace(id) {
  if (placeById[id]) return clone(placeById[id]);
  return {
    id,
    type: "rest",
    name: "地点待确认",
    shortName: "地点待确认",
    address: "",
    openHours: "",
    rating: "",
    price: "",
    tags: [],
    reason: "",
    note: "",
    map: { x: 50, y: 50 },
  };
}

function resolveRoute(routeConfig) {
  const timelineByPlace = Object.fromEntries(routeConfig.timeline.map((item) => [item.placeId, item]));
  const transportSegments = routeConfig.transportSegments.map((segment) => {
    const from = placeById[segment.fromId];
    const to = placeById[segment.toId];
    return {
      ...clone(segment),
      from: from.name,
      to: to.name,
      arriveAt: timelineByPlace[segment.toId]?.arrive || "",
    };
  });

  const nodes = routeConfig.placeIds.map((placeId, index) => {
    const place = getPlace(placeId);
    const time = timelineByPlace[placeId] || {};
    const segment = transportSegments[index];
    const nextPlace = routeConfig.placeIds[index + 1] ? placeById[routeConfig.placeIds[index + 1]] : null;

    return {
      ...place,
      arrive: time.arrive || "",
      leave: time.leave || "",
      next: segment && nextPlace ? `${segment.method}${segment.duration}，前往${nextPlace.name}。` : "",
    };
  });

  return {
    id: routeConfig.id,
    label: routeConfig.label,
    name: routeConfig.name,
    explanation: routeConfig.explanation,
    durationMinutes: routeConfig.durationMinutes,
    budgetPerPerson: routeConfig.budgetPerPerson,
    walkingKm: routeConfig.walkingKm,
    waitRisk: routeConfig.waitRisk,
    transportSummary: routeConfig.transportSummary || mockRouteData.routes.default.transportSummary,
    nodes,
    transportSegments,
    hint: "",
  };
}

function buildDefaultRoute() {
  return resolveRoute(mockRouteData.routes.default);
}

function generateRouteLocal() {
  return buildDefaultRoute();
}

function adjustRouteLocal(adjustmentType, currentRoute, targetNodeId) {
  const adjustment = mockRouteData.adjustments[adjustmentType];
  if (!adjustment || !currentRoute) return null;

  const nextRoute = resolveRoute({
    ...mockRouteData.routes.default,
    ...adjustment.route,
    id: currentRoute.id,
    label: currentRoute.label,
    name: currentRoute.name,
  });

  return {
    route: nextRoute,
    diff: clone(adjustment.diff),
    targetNodeId,
  };
}

async function generateRouteFromApi() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/route/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: state.inputText }),
    });
    const data = await readApiResponse(response);
    return applyRouteData(data.routeData).route;
  } catch (error) {
    console.error(error);
    return null;
  }
}

async function adjustRouteFromApi(adjustmentType, currentRoute, targetNodeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/route/adjust`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        adjustmentType,
        nodeId: targetNodeId,
        route: routeToConfig(currentRoute),
      }),
    });
    const data = await readApiResponse(response);
    return {
      ...applyRouteData(data.routeData),
      targetNodeId,
    };
  } catch (error) {
    console.error(error);
    showToast("Backend API unavailable");
    return null;
  }
}

async function adjustRouteActionFromApi(action, currentRoute, targetNodeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/route/adjust`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        nodeId: targetNodeId,
        route: routeToConfig(currentRoute),
      }),
    });
    const data = await readApiResponse(response);
    return {
      ...applyRouteData(data.routeData),
      targetNodeId,
    };
  } catch (error) {
    console.error(error);
    showToast("Backend API unavailable");
    return null;
  }
}

async function readApiResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.message || data?.detail || `API request failed: ${response.status}`);
  }
  if (!data.routeData) {
    throw new Error("API response is missing routeData");
  }
  return data;
}

function applyRouteData(routeData) {
  if (!routeData?.route || !Array.isArray(routeData.places)) {
    throw new Error("routeData is missing route or places");
  }
  placeById = Object.fromEntries(routeData.places.map((place) => [place.id, place]));
  const route = resolveRoute(routeData.route);
  route.hint = routeData.message || "";
  return {
    route,
    diff: routeData.diff || null,
  };
}

async function generateRouteData() {
  if (USE_BACKEND_API) {
    return generateRouteFromApi();
  }
  return generateRouteLocal();
}

async function adjustRouteData(adjustmentType, currentRoute, targetNodeId) {
  if (USE_BACKEND_API) {
    return adjustRouteFromApi(adjustmentType, currentRoute, targetNodeId);
  }
  return adjustRouteLocal(adjustmentType, currentRoute, targetNodeId);
}

function formatDuration(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value)) return "时长待确认";
  const hours = Math.floor(value / 60);
  const rest = value % 60;
  if (!hours) return `${rest}分钟`;
  return `${hours}小时${String(rest).padStart(2, "0")}分钟`;
}

function hasValue(value) {
  return value !== undefined && value !== null && value !== "" && !Number.isNaN(value);
}

function displayText(value, fallback) {
  return hasValue(value) ? escapeHtml(value) : fallback;
}

function displayBudget(value) {
  return hasValue(value) ? `${escapeHtml(value)}元` : "预算待确认";
}

function displayDistance(value) {
  return hasValue(value) ? `${escapeHtml(value)}km` : "距离待确认";
}

function displayWaitRisk(value) {
  return hasValue(value) ? escapeHtml(value) : "等待待确认";
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function routeToConfig(route) {
  return {
    id: route.id,
    label: route.label,
    name: route.name,
    explanation: route.explanation,
    durationMinutes: route.durationMinutes,
    budgetPerPerson: route.budgetPerPerson,
    walkingKm: route.walkingKm,
    waitRisk: route.waitRisk,
    transportSummary: route.transportSummary,
    placeIds: route.nodes.map((node) => node.id),
    timeline: route.nodes.map((node) => ({ placeId: node.id, arrive: node.arrive, leave: node.leave })),
    transportSegments: route.transportSegments.map((segment) => ({
      fromId: segment.fromId,
      toId: segment.toId,
      method: segment.method,
      duration: segment.duration,
    })),
  };
}

function calculateOrderPenalty(nodes) {
  const naturalOrder = ["in77", "brokenBridge", "photoPoint", "baitacoffee", "convenienceRest", "xinbailu", "nongtangli"];
  let penalty = 0;
  nodes.forEach((node, index) => {
    const previous = nodes[index - 1];
    if (previous && naturalOrder.indexOf(previous.id) > naturalOrder.indexOf(node.id)) penalty += 1;
  });
  return { minutes: penalty * 12, km: penalty * 0.3 };
}

function recalculateAfterManualChange(route, explanation) {
  const config = routeToConfig(route);
  const penalty = calculateOrderPenalty(route.nodes);
  const nextRoute = resolveRoute({
    ...config,
    explanation,
    durationMinutes: route.durationMinutes + penalty.minutes,
    walkingKm: Number((route.walkingKm + penalty.km).toFixed(1)),
  });
  nextRoute.hint = penalty.minutes > 0 ? "这个顺序会略绕路，建议保留原顺序。" : "";
  return nextRoute;
}

function getNextAction(route) {
  const nodes = safeArray(route.nodes);
  const segments = safeArray(route.transportSegments);
  const index = Math.max(0, nodes.findIndex((node) => node.id === state.selectedNodeId));
  const safeIndex = index >= nodes.length - 1 ? 0 : index;
  const current = nodes[safeIndex] || {};
  const next = nodes[safeIndex + 1] || nodes[1] || nodes[0] || {};
  const segment = segments[safeIndex] || segments[0] || { method: "交通方式待确认", duration: "", from: "", to: "" };
  return { current, next, segment };
}

function keptNodes(previousRoute, nextRoute) {
  const nextNames = new Set(nextRoute.nodes.map((node) => node.name));
  return previousRoute.nodes
    .filter((node) => nextNames.has(node.name))
    .map((node) => node.name)
    .join("、");
}

function setState(patch) {
  state = { ...state, ...patch };
  render();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showToast(message) {
  state.toast = message;
  render();
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    state.toast = "";
    render();
  }, 1600);
}

function startGeneration() {
  setState({
    view: "loading",
    loadingStep: 0,
    diff: null,
    previousRoute: null,
    activeAdjustment: null,
    activeTab: "route",
    drawerOpen: false,
  });

  [1, 2, 3].forEach((step, index) => {
    window.setTimeout(async () => {
      if (step < 3) {
        setState({ loadingStep: step });
      } else {
        const route = await generateRouteData();
        if (!route) {
          showToast("路线生成暂时不可用");
          setState({ view: "input", loadingStep: 0 });
          return;
        }
        setState({
          view: "result",
          loadingStep: 3,
          route,
          selectedNodeId: route.nodes[0].id,
          hint: "",
        });
      }
    }, 520 + index * 620);
  });
}

async function applyAdjustment(type, targetNodeId) {
  if (!state.route) return;
  const previousRoute = clone(state.route);
  const result = await adjustRouteData(type, state.route, targetNodeId);
  if (!result) return;

  setState({
    previousRoute,
    route: result.route,
    diff: result.diff,
    selectedNodeId: result.route.nodes[0]?.id,
    activeAdjustment: type,
    drawerOpen: true,
    hint: result.route.hint || "",
  });
}

async function applyNodeAction(action, targetNodeId) {
  if (!state.route) return;
  const previousRoute = clone(state.route);
  const result = await adjustRouteActionFromApi(action, state.route, targetNodeId);
  if (!result) return;

  setState({
    previousRoute,
    route: result.route,
    diff: result.diff,
    selectedNodeId: action === "delete" ? result.route.nodes[0]?.id : targetNodeId,
    activeAdjustment: null,
    drawerOpen: true,
    hint: result.route.hint || "",
  });
}

function moveNode(id, direction) {
  if (!state.route) return;
  if (USE_BACKEND_API) {
    return applyNodeAction(direction < 0 ? "moveUp" : "moveDown", id);
  }
  const previousRoute = clone(state.route);
  const nextRoute = clone(state.route);
  const index = nextRoute.nodes.findIndex((node) => node.id === id);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= nextRoute.nodes.length) {
    showToast("这个节点已经在边界位置");
    return;
  }

  const [node] = nextRoute.nodes.splice(index, 1);
  nextRoute.nodes.splice(target, 0, node);

  nextRoute.transportSegments = nextRoute.nodes.slice(0, -1).map((current, segmentIndex) => {
    const next = nextRoute.nodes[segmentIndex + 1];
    return {
      fromId: current.id,
      toId: next.id,
      from: current.name,
      to: next.name,
      method: "步行",
      duration: "约12分钟",
      arriveAt: next.arrive,
    };
  });

  const recalculated = recalculateAfterManualChange(nextRoute, "已按你的顺序重算路线。");
  setState({
    previousRoute,
    route: recalculated,
    selectedNodeId: id,
    drawerOpen: true,
    hint: recalculated.hint || "",
    diff: {
      title: "顺序已调整",
      action: "已重新计算总时长、步行距离和编号。",
      rows: [
        { label: "路线顺序", value: recalculated.nodes.map((item) => item.name).join(" → ") },
        { label: "总时长", value: `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(recalculated.durationMinutes)}` },
        { label: "步行距离", value: `${previousRoute.walkingKm}km → ${recalculated.walkingKm}km` },
      ],
    },
  });
}

function deleteNode(id) {
  if (!state.route) return;
  if (USE_BACKEND_API) {
    return applyNodeAction("delete", id);
  }
  const previousRoute = clone(state.route);
  const target = previousRoute.nodes.find((node) => node.id === id);
  if (!target) return;
  if (target.type === "start") {
    showToast("起点需要保留，方便继续计算路线");
    return;
  }

  const nextRoute = clone(state.route);
  nextRoute.nodes = nextRoute.nodes.filter((node) => node.id !== id);
  nextRoute.transportSegments = nextRoute.nodes.slice(0, -1).map((current, segmentIndex) => {
    const next = nextRoute.nodes[segmentIndex + 1];
    return {
      fromId: current.id,
      toId: next.id,
      from: current.name,
      to: next.name,
      method: "步行",
      duration: "约12分钟",
      arriveAt: next.arrive,
    };
  });

  const recalculated = recalculateAfterManualChange(nextRoute, "已删除这个目的地，并同步更新后续路线。");
  setState({
    previousRoute,
    route: recalculated,
    selectedNodeId: recalculated.nodes[0]?.id,
    drawerOpen: true,
    hint: recalculated.hint || "",
    diff: {
      title: "已删除节点",
      action: "已移除相关目的地，并重算路线。",
      rows: [
        { label: "删除节点", value: target.name },
        { label: "总时长", value: `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(recalculated.durationMinutes)}` },
        { label: "预计人均", value: `${previousRoute.budgetPerPerson}元 → ${recalculated.budgetPerPerson}元` },
        { label: "保留节点", value: keptNodes(previousRoute, recalculated) },
      ],
    },
  });
}

function replaceNode(id) {
  if (!state.route) return;
  if (USE_BACKEND_API) {
    return applyNodeAction("replace", id);
  }
  const target = state.route.nodes.find((node) => node.id === id);
  if (!target) return;
  if (target.type === "dinner") return applyAdjustment("restaurantBusy", id);
  if (target.type === "coffee") return applyAdjustment("budget100", id);
  if (target.type === "scenic") return applyAdjustment("photo", id);
  showToast("这个节点建议保留为路线起点");
}

function acceptNewRoute() {
  setState({ previousRoute: null, diff: null, activeAdjustment: null, drawerOpen: false });
  showToast("已采用新方案");
}

function restoreRoute() {
  if (!state.previousRoute) return;
  const restored = state.previousRoute;
  setState({
    route: restored,
    previousRoute: null,
    diff: null,
    activeAdjustment: null,
    selectedNodeId: restored.nodes[0]?.id,
    drawerOpen: false,
    hint: "",
  });
  showToast("已恢复原方案");
}

function render() {
  if (state.view === "loading") {
    app.innerHTML = renderLoading();
  } else if (state.view === "result" && state.route) {
    app.innerHTML = renderResult();
  } else {
    app.innerHTML = renderInput();
  }
  bindEvents();
}

function renderInput() {
  const exampleChips = [
    { label: "少排队半日线", value: mockRouteData.input.examples[0] },
    { label: "带老人小孩少走路", value: mockRouteData.input.examples[1] },
    {
      label: "预算100以内",
      value: "我在湖滨银泰，现在出发，想逛西湖和吃晚饭，预算人均100以内，尽量少排队。",
    },
    { label: "想拍照但不想太网红", value: mockRouteData.input.examples[2] },
  ];

  return `
    <section class="screen input-screen">
      <div class="hero">
        <div class="kicker">杭州西湖 · 现在出发</div>
        <h1>一句话，生成现在能走的路线</h1>
        <p>输入你现在的位置、时间、预算和想法，我会自动识别约束并给你一条可执行路线。</p>
      </div>
      <section class="agent-input-panel">
        <div class="agent-input-head">
          <span>告诉我你想怎么走</span>
          <button class="mic ${state.micActive ? "active" : ""}" data-action="toggleMic" aria-label="语音输入">麦</button>
        </div>
        <textarea class="agent-textarea" data-field="intent">${escapeHtml(state.inputText)}</textarea>
        <div class="input-hint">可输入一句话，语音输入下一版接入。</div>
        <div class="mic-state">${state.micActive ? "语音输入演示中，当前请以文字输入为准" : ""}</div>
        <div class="auto-note">系统会从你的自然语言中自动识别时间、预算、同行人和偏好。</div>
        <div class="example-block">
          <div class="section-label">试试这些需求</div>
          <div class="examples example-chips">
            ${exampleChips
              .map(
                (example) =>
                  `<button class="example" data-action="useExample" data-value="${escapeHtml(example.value)}">${escapeHtml(example.label)}</button>`,
              )
              .join("")}
          </div>
        </div>
        <button class="primary input-primary" data-action="generate">生成现在能走的路线</button>
      </section>
    </section>
    ${renderToast()}
  `;
}

function renderLegacyInput() {
  return `
    <section class="screen">
      <div class="hero">
        <div class="kicker">杭州西湖周边 · 现在出发</div>
        <h1>说出你的出行目标，我帮你串成一条能直接走的路线。</h1>
        <p>不生成长攻略，只给你一条现在能走的路线；如果排队、预算或时间变了，可以只调整其中一站。</p>
      </div>
      <section class="panel">
        <div class="input-head">
          <strong>我理解你的需求是</strong>
          <button class="mic ${state.micActive ? "active" : ""}" data-action="toggleMic" aria-label="语音输入">⌁</button>
        </div>
        <div class="mic-state">${state.micActive ? "语音输入演示中" : ""}</div>
        <textarea data-field="intent">${escapeHtml(state.inputText)}</textarea>
        <div class="section-label">试试这些需求</div>
        <div class="examples">
          ${mockRouteData.input.examples
            .map((example) => `<button class="example" data-action="useExample" data-value="${escapeHtml(example)}">${escapeHtml(example)}</button>`)
            .join("")}
        </div>
        <div class="section-label">偏好</div>
        <div class="tag-row">
          ${mockRouteData.input.preferenceTags
            .map((tag) => `<button class="tag ${state.selectedPreferences.includes(tag) ? "selected" : ""}" data-action="togglePreference" data-value="${tag}">${tag}</button>`)
            .join("")}
        </div>
        <button class="primary" data-action="generate">生成可执行路线</button>
      </section>
    </section>
    ${renderToast()}
  `;
}

function renderLoading() {
  const steps = ["正在解析你的出行目标", "正在匹配西湖周边 POI", "正在计算顺路路线和等待风险"];
  return `
    <section class="loading-screen">
      <div class="loading-card panel">
        <div class="pulse-route"><span class="pulse-dot one"></span><span class="pulse-dot two"></span></div>
        <div class="loading-title">正在把需求串成路线</div>
        <div class="steps">
          ${steps
            .map((step, index) => {
              const status = state.loadingStep > index ? "done" : state.loadingStep === index ? "active" : "";
              return `<div class="step ${status}"><span class="step-dot">${state.loadingStep > index ? "✓" : index + 1}</span><span>${step}</span></div>`;
            })
            .join("")}
        </div>
      </div>
    </section>
  `;
}

function renderResult() {
  const route = state.route;
  return `
    <section class="screen result task-screen tab-${state.activeTab}">
      <div class="route-brief">${displayText(mockRouteData.constraints.summary, "当前约束待确认")}</div>
      ${renderSummary(route)}
      ${renderNextAction(route)}
      ${renderTabs()}
      <section class="tab-body">
        ${state.activeTab === "route" ? renderRouteTab(route) : ""}
        ${state.activeTab === "map" ? renderMap(route, "large") : ""}
        ${state.activeTab === "places" ? renderPoiCards(route) : ""}
      </section>
      ${renderBottomBar(route)}
      ${renderDrawer()}
    </section>
    ${renderToast()}
  `;
}

function renderSummary(route) {
  return `
    <section class="card summary-card task-summary">
      <div>
        <span class="summary-label">${displayText(route.label, "当前路线")}</span>
        <h2>${displayText(route.name, "路线名称待确认")}</h2>
        <p>${displayText(route.explanation, "路线理由待确认")}</p>
      </div>
      <div class="task-metrics">
        <div><strong>${formatDuration(route.durationMinutes)}</strong><span>总时长</span></div>
        <div><strong>${displayBudget(route.budgetPerPerson)}</strong><span>人均</span></div>
        <div><strong>${displayDistance(route.walkingKm)}</strong><span>步行</span></div>
        <div><strong>${displayWaitRisk(route.waitRisk)}</strong><span>等待</span></div>
      </div>
    </section>
  `;
}

function renderNextAction(route) {
  const { current, next, segment } = getNextAction(route);
  const currentName = current.shortName || current.name || "当前位置";
  const nextName = next.name || "下一站待确认";
  const method = segment.method || "交通方式待确认";
  const duration = segment.duration || "";
  const arrive = next.arrive || "到达时间待确认";
  return `
    <section class="card next-card">
      <span>下一步行动</span>
      <h3>下一站：${displayText(nextName, "下一站待确认")}</h3>
      <p>从${displayText(currentName, "当前位置")}${displayText(method, "交通方式待确认")}${displayText(duration, "")}，预计${displayText(arrive, "到达时间待确认")}到达。</p>
    </section>
  `;
}

function renderTabs() {
  const tabs = [
    ["route", "路线"],
    ["map", "地图"],
    ["places", "地点"],
  ];
  return `
    <nav class="route-tabs" aria-label="路线视图切换">
      ${tabs
        .map(([id, label]) => `<button class="${state.activeTab === id ? "active" : ""}" data-action="switchTab" data-tab="${id}">${label}</button>`)
        .join("")}
    </nav>
  `;
}

function renderRouteTab(route) {
  return `
    <div class="hint ${state.hint ? "show" : ""}">${state.hint}</div>
    <section class="card transport-compact">
      <button class="transport-toggle" data-action="toggleTransport">
        <span>完整交通方案</span>
        <strong>${state.transportOpen ? "收起" : "展开"}</strong>
      </button>
      ${state.transportOpen ? renderTransportList(route) : `<p>${displayText(route.transportSummary, "交通方案待确认")}</p>`}
    </section>
    ${renderTimeline(route)}
  `;
}

function renderTransportList(route) {
  const segments = safeArray(route.transportSegments);
  if (!segments.length) {
    return `<p class="empty-note">交通分段待确认，路线节点仍可按顺序查看。</p>`;
  }
  return `
    <div class="segments">
      ${segments
        .map((segment) => `
          <div class="segment">
            <span class="walk-icon">步</span>
            <div><strong>${displayText(segment.from, "出发地待确认")} → ${displayText(segment.to, "目的地待确认")}</strong><span>${displayText(segment.method, "交通方式待确认")}${displayText(segment.duration, "")}</span></div>
          </div>
        `)
        .join("")}
    </div>
  `;
}

function renderMap(route, mode) {
  const nodes = safeArray(route.nodes);
  const points = nodes.map((node) => `${node.map?.x ?? 50},${node.map?.y ?? 50}`).join(" ");
  const activeNode = nodes.find((node) => node.id === state.selectedNodeId) || nodes[0] || {};
  return `
    <section class="card map-card ${mode === "preview" ? "map-preview-card" : "map-large-card"}">
      ${mode === "large" ? `<div class="section-head"><h3>路线地图</h3><span class="summary-label">${nodes.length}站</span></div>` : ""}
      <div class="map ${mode === "preview" ? "map-preview" : "map-large"}">
        <span class="lake-label">西湖水域</span>
        <span class="district-label">湖滨商圈</span>
        <svg class="route-line" viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points="${points}"></polyline></svg>
        ${nodes
          .map((node, index) => `
            <button class="marker ${node.id === state.selectedNodeId ? "active" : ""}"
              style="left:${node.map?.x ?? 50}%;top:${node.map?.y ?? 50}%"
              data-action="selectNode"
              data-id="${node.id}"
              aria-label="${displayText(node.name, "地点待确认")}">${index + 1}</button>
          `)
          .join("")}
        ${mode === "large" ? `<div class="map-active-place"><strong>${displayText(activeNode.name, "地点待确认")}</strong><span>${displayText(typeText[activeNode.type], "类型待确认")}｜${displayText(activeNode.arrive, "到达时间待确认")} 到达</span></div>` : ""}
      </div>
      ${mode === "large" ? `<div class="map-caption"><span>点击编号同步查看节点</span><span>${displayText(nodes.find((node) => node.id === state.selectedNodeId)?.name, "")}</span></div>` : ""}
    </section>
  `;
}

function renderTimeline(route) {
  const nodes = safeArray(route.nodes);
  return `
    <section class="card">
      <div class="section-head"><h3>今天怎么走</h3><span class="summary-label">行动指令</span></div>
      <div class="timeline compact-timeline">
        ${nodes
          .map((node, index) => {
            const expanded = state.expandedNodes.includes(node.id);
            return `
              <article class="timeline-item ${node.id === state.selectedNodeId ? "active" : ""}">
                <div class="timebox"><strong>${displayText(node.arrive, "--:--")}</strong><span>${displayText(node.leave, "--:--")} 离开</span><div class="node-dot">${index + 1}</div></div>
                <div class="timeline-body">
                  <h4>${displayText(node.name, "地点待确认")}</h4>
                  <div class="type-line">${displayText(typeIcon[node.type], "点")} · ${displayText(typeText[node.type], "类型待确认")}</div>
                  ${node.next ? `<div class="next-step">下一段：${displayText(node.next, "交通信息待确认")}</div>` : `<div class="next-step">路线结束，湖滨商圈方便离开。</div>`}
                  <button class="detail-toggle" data-action="toggleNodeDetail" data-id="${node.id}">${expanded ? "收起说明" : "查看理由"}</button>
                  ${expanded ? `<p>${displayText(node.reason, "推荐理由待确认")}</p>${node.note ? `<div class="notice">${displayText(node.note, "")}</div>` : ""}` : ""}
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderPoiCards(route) {
  const nodes = safeArray(route.nodes);
  return `
    <section class="card">
      <div class="section-head"><h3>目的地</h3><span class="summary-label">可局部调整</span></div>
      <div class="poi-list">
        ${nodes
          .map((node, index) => `
            <article class="poi-card card ${node.id === state.selectedNodeId ? "active" : ""}" data-id="${node.id}">
              ${renderPoiVisual(node, index)}
              <div class="poi-content">
                <div class="poi-meta"><span class="poi-type">${displayText(typeText[node.type], "类型待确认")}</span><span class="poi-score">评分 ${displayText(node.rating, "暂无评分")}</span></div>
                <h4>${displayText(node.name, "地点待确认")}</h4>
                <p>${displayText(node.address, "地址待确认")}</p>
                <div class="mini-grid"><div class="mini"><strong>开放时间</strong>${displayText(node.openHours, "营业时间待确认")}</div><div class="mini"><strong>价格</strong>${displayText(node.price, "价格待确认")}</div></div>
                <div class="small-tags">${safeArray(node.tags).map((tag) => `<span>${displayText(tag, "")}</span>`).join("")}</div>
                <p class="why">为什么推荐：${displayText(node.reason, "推荐理由待确认")}</p>
                <div class="poi-actions">
                  <button class="small-btn primary-mini" data-action="replaceNode" data-id="${node.id}">替换</button>
                  <button class="small-btn" data-action="deleteNode" data-id="${node.id}">删除</button>
                  <button class="small-btn" data-action="moveNodeUp" data-id="${node.id}">上移</button>
                  <button class="small-btn" data-action="moveNodeDown" data-id="${node.id}">下移</button>
                </div>
              </div>
            </article>
          `)
          .join("")}
      </div>
    </section>
  `;
}

function renderPoiVisual(node, index) {
  const imageUrl = hasValue(node.imageUrl) ? String(node.imageUrl) : "";
  return `
    <div class="poi-visual ${displayText(node.type, "rest")} ${imageUrl ? "has-image" : ""}">
      ${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="${displayText(node.name, "地点图片")}" loading="lazy" onerror="this.closest('.poi-visual')?.classList.add('image-failed'); this.remove();">` : ""}
      <span class="poi-index">${index + 1}</span>
    </div>
  `;
}

function renderBottomBar(route) {
  const { next, segment } = getNextAction(route);
  const nextName = next.name || "下一站待确认";
  const method = segment.method || "交通方式待确认";
  const duration = segment.duration ? segment.duration.replace("约", "") : "";
  return `
    <div class="bottom-action-bar">
      <div><span>下一站</span><strong>${displayText(nextName, "下一站待确认")}｜${displayText(method, "交通方式待确认")}${displayText(duration, "")}</strong></div>
      <button class="secondary" data-action="openDrawer">调整</button>
      <button class="primary" data-action="followRoute">出发</button>
    </div>
  `;
}

function renderDrawer() {
  if (!state.drawerOpen) return "";
  const hasDiffRows = state.diff && safeArray(state.diff.rows).length;
  return `
    <div class="drawer-backdrop" data-action="closeDrawer"></div>
    <aside class="bottom-drawer" role="dialog" aria-label="调整路线">
      <div class="drawer-handle"></div>
      <div class="section-head">
        <h3>想怎么改？直接说一句</h3>
        <button class="drawer-close" data-action="closeDrawer">关闭</button>
      </div>
      <p class="transport-note">我会尽量只改相关节点，不重生成整篇攻略。</p>
      <section class="nl-adjust-box" aria-label="自然语言调整入口">
        <textarea class="nl-adjust-input" data-field="naturalAdjust" placeholder="例如：我想少排队一点 / 不要咖啡 / 现在只剩2小时"></textarea>
        <button class="primary nl-adjust-submit" data-action="submitNaturalAdjust">提交调整</button>
      </section>
      <div class="quick-grid drawer-grid">
        ${mockRouteData.adjustmentButtons
          .map((button) => `<button class="quick-btn ${state.activeAdjustment === button.type ? "active" : ""}" data-action="adjust" data-type="${button.type}">${button.label}</button>`)
          .join("")}
      </div>
      ${hasDiffRows ? renderDiffCard(state.diff) : ""}
    </aside>
  `;
}

function renderDiffCard(diff) {
  const rows = safeArray(diff?.rows);
  if (!rows.length) return "";
  return `
    <section class="diff-card drawer-diff">
      <h3>${displayText(diff.title, "调整结果")}</h3>
      <p class="diff-subtitle">${displayText(diff.action, "已完成局部调整。")}</p>
      <div class="diff-list">
        ${rows.map((row) => `<div class="diff-row"><span>${displayText(row.label, "")}</span><span>${displayText(row.value, "")}</span></div>`).join("")}
      </div>
      <div class="diff-actions">
        <button class="primary" data-action="acceptRoute">采用新方案</button>
        <button class="text-btn" data-action="restoreRoute">恢复原方案</button>
      </div>
    </section>
  `;
}

function renderToast() {
  return `<div class="toast ${state.toast ? "show" : ""}">${state.toast}</div>`;
}

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((element) => {
    element.addEventListener("click", handleAction);
  });
  document.querySelectorAll(".poi-card").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("[data-action]")) return;
      setState({ selectedNodeId: card.dataset.id });
    });
  });
  const textarea = document.querySelector("[data-field='intent']");
  if (textarea) {
    textarea.addEventListener("input", (event) => {
      state.inputText = event.target.value;
    });
  }
}

function handleAction(event) {
  const target = event.currentTarget;
  const action = target.dataset.action;
  const id = target.dataset.id;

  if (action === "toggleMic") setState({ micActive: !state.micActive });
  if (action === "useExample") setState({ inputText: target.dataset.value || mockRouteData.input.defaultText });
  if (action === "submitNaturalAdjust") {
    showToast("自然语言调整入口已预留，真实接入将在 /api/chat-route 契约确认后完成");
  }
  if (action === "togglePreference") {
    const value = target.dataset.value;
    const exists = state.selectedPreferences.includes(value);
    setState({
      selectedPreferences: exists
        ? state.selectedPreferences.filter((item) => item !== value)
        : [...state.selectedPreferences, value],
    });
  }
  if (action === "generate") startGeneration();
  if (action === "switchTab") setState({ activeTab: target.dataset.tab });
  if (action === "toggleTransport") setState({ transportOpen: !state.transportOpen });
  if (action === "toggleNodeDetail") {
    event.stopPropagation();
    const exists = state.expandedNodes.includes(id);
    setState({
      expandedNodes: exists
        ? state.expandedNodes.filter((item) => item !== id)
        : [...state.expandedNodes, id],
    });
  }
  if (action === "selectNode") {
    setState({ selectedNodeId: id });
  }
  if (action === "openDrawer") setState({ drawerOpen: true });
  if (action === "closeDrawer") setState({ drawerOpen: false });
  if (action === "adjust") applyAdjustment(target.dataset.type, state.selectedNodeId);
  if (action === "followRoute") showToast("已进入路线执行视图");
  if (action === "moveNodeUp") moveNode(id, -1);
  if (action === "moveNodeDown") moveNode(id, 1);
  if (action === "deleteNode") deleteNode(id);
  if (action === "replaceNode") replaceNode(id);
  if (action === "acceptRoute") acceptNewRoute();
  if (action === "restoreRoute") restoreRoute();
}

render();
