const app = document.querySelector("#app");

const defaultInput =
  "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队";

const examples = [
  defaultInput,
  "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，预算人均120",
  "想找适合拍照但不要太网红的咖啡店，晚上顺路吃本地特色",
];

const preferenceTags = ["少排队", "少走路", "拍照好看", "本地特色", "安静", "带老人小孩"];

const typeText = {
  start: "起点",
  scenic: "景点",
  coffee: "咖啡",
  dinner: "晚餐",
  rest: "休息",
};

const typeIcon = {
  start: "起",
  scenic: "景",
  coffee: "咖",
  dinner: "食",
  rest: "休",
};

const basePois = {
  in77: {
    id: "in77",
    type: "start",
    name: "湖滨银泰 in77",
    address: "上城区湖滨商圈",
    openHours: "全天可达",
    rating: "4.7",
    price: "免费",
    priceValue: 0,
    tags: ["地铁近", "集合方便", "商圈补给"],
    reason: "离西湖东线近，适合作为路线起点。",
    arrive: "14:00",
    leave: "14:05",
    note: "",
    next: "步行约12分钟，从湖滨进入西湖东线。",
    map: { x: 72, y: 28 },
  },
  brokenBridge: {
    id: "brokenBridge",
    type: "scenic",
    name: "断桥残雪",
    address: "西湖区北山街",
    openHours: "全天开放",
    rating: "4.6",
    price: "免费",
    priceValue: 0,
    tags: ["西湖经典", "拍照友好", "游客友好"],
    reason: "能快速进入西湖氛围，适合下午轻松游览。",
    arrive: "14:17",
    leave: "14:52",
    note: "游客较多，但不影响路线执行。",
    next: "步行约8分钟，沿湖边向南移动。",
    map: { x: 42, y: 42 },
  },
  baitacoffee: {
    id: "baitacoffee",
    type: "coffee",
    name: "湖畔白塔咖啡",
    address: "湖滨路附近",
    openHours: "10:00-21:30",
    rating: "4.5",
    price: "人均42元",
    priceValue: 42,
    tags: ["安静", "低等待估计", "可休息"],
    reason: "距离上一站约8分钟，适合中途休息。",
    arrive: "15:04",
    leave: "15:39",
    note: "低等待为样例风险标签，不代表实时排队。",
    next: "步行约10分钟，返回湖滨商圈。",
    map: { x: 55, y: 63 },
  },
  xinbailu: {
    id: "xinbailu",
    type: "dinner",
    name: "新白鹿餐厅湖滨店",
    address: "上城区延安路附近",
    openHours: "10:30-21:30",
    rating: "4.4",
    price: "人均78元",
    priceValue: 78,
    tags: ["杭帮菜", "预算友好", "家庭友好"],
    reason: "在预算内，离湖滨近，适合晚餐收尾。",
    arrive: "15:51",
    leave: "16:46",
    note: "晚高峰可能短时等待。",
    next: "",
    map: { x: 76, y: 72 },
  },
};

const alternativePois = {
  nongtangli: {
    id: "nongtangli",
    type: "dinner",
    name: "弄堂里湖滨店",
    address: "湖滨商圈附近",
    openHours: "10:30-21:00",
    rating: "4.3",
    price: "人均65元",
    priceValue: 65,
    tags: ["杭帮菜", "等待低", "预算更低"],
    reason: "比原餐厅等待风险更低，人均更低，距离路线也更顺。",
    arrive: "15:45",
    leave: "16:32",
    note: "晚餐等待风险更低，适合作为当前替换点。",
    next: "",
    map: { x: 70, y: 70 },
  },
  convenienceRest: {
    id: "convenienceRest",
    type: "rest",
    name: "湖滨轻休息点",
    address: "湖滨步行街附近",
    openHours: "全天可达",
    rating: "4.2",
    price: "免费",
    priceValue: 0,
    tags: ["省预算", "少停留", "顺路"],
    reason: "保留休息缓冲，同时把预算留给晚餐。",
    arrive: "15:00",
    leave: "15:12",
    note: "停留时间较短，适合预算收紧时使用。",
    next: "步行约8分钟，回到湖滨商圈。",
    map: { x: 60, y: 58 },
  },
  photoPoint: {
    id: "photoPoint",
    type: "scenic",
    name: "北山街湖景点",
    address: "西湖区北山街沿线",
    openHours: "全天开放",
    rating: "4.5",
    price: "免费",
    priceValue: 0,
    tags: ["湖景", "拍照好看", "不太网红"],
    reason: "比热门机位更分散，适合想拍照但不想太拥挤的路线。",
    arrive: "14:56",
    leave: "15:20",
    note: "下午光线较柔和，但仍建议避开桥面人流。",
    next: "步行约9分钟，前往咖啡点休息。",
    map: { x: 36, y: 54 },
  },
};

let state = {
  view: "input",
  inputText: defaultInput,
  selectedPreferences: ["少排队"],
  micActive: false,
  loadingStep: 0,
  route: null,
  previousRoute: null,
  diff: null,
  selectedNodeId: null,
  activeAdjustment: null,
  toast: "",
  hint: "",
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function buildDefaultRoute() {
  const nodes = [
    clone(basePois.in77),
    clone(basePois.brokenBridge),
    clone(basePois.baitacoffee),
    clone(basePois.xinbailu),
  ];

  return {
    id: "westlake-half-day",
    label: "当前推荐",
    name: "轻松西湖半日线",
    explanation:
      "这条路线适合下午轻松逛西湖：先从湖滨银泰进入西湖核心景观，再安排咖啡休息，最后顺路吃晚饭。",
    durationMinutes: 166,
    budgetPerPerson: 120,
    walkingKm: 2.3,
    waitRisk: "低-中",
    constraints: buildConstraintsFromInput(),
    transportSummary:
      "全程步行优先，单段最长约12分钟；如带老人小孩，可将咖啡到晚餐段改为打车。",
    transportSegments: [
      { from: "湖滨银泰 in77", to: "断桥残雪", method: "步行", duration: "约12分钟" },
      { from: "断桥残雪", to: "湖畔白塔咖啡", method: "步行", duration: "约8分钟" },
      { from: "湖畔白塔咖啡", to: "新白鹿餐厅湖滨店", method: "步行", duration: "约10分钟" },
    ],
    nodes,
  };
}

function buildConstraintsFromInput() {
  const preferences = state.selectedPreferences.length ? state.selectedPreferences.join(" / ") : "少排队";
  return [
    { key: "出发地", value: "湖滨银泰 in77" },
    { key: "时间", value: "14:00-18:00" },
    { key: "预算", value: "人均150" },
    { key: "目标", value: "西湖 / 咖啡 / 晚饭" },
    { key: "偏好", value: preferences },
    { key: "交通", value: "步行优先" },
  ];
}

function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest}分钟`;
  return `${hours}小时${String(rest).padStart(2, "0")}分钟`;
}

function recalculateRoute(route, reason = "") {
  const updated = clone(route);
  const nodeIds = updated.nodes.map((node) => node.id);
  const hasCoffee = nodeIds.includes("baitacoffee");
  const hasNongtangli = nodeIds.includes("nongtangli");
  const hasPhoto = nodeIds.includes("photoPoint");
  const hasRest = nodeIds.includes("convenienceRest");

  if (!hasCoffee && nodeIds.length === 3) {
    updated.durationMinutes = 125;
    updated.budgetPerPerson = hasNongtangli ? 65 : 78;
    updated.walkingKm = hasNongtangli ? 1.9 : 2.0;
    updated.waitRisk = hasNongtangli ? "低" : "中";
  } else if (hasNongtangli) {
    updated.durationMinutes = 152;
    updated.budgetPerPerson = hasRest ? 95 : 108;
    updated.walkingKm = 2.1;
    updated.waitRisk = "低";
  } else if (hasRest) {
    updated.durationMinutes = 145;
    updated.budgetPerPerson = 95;
    updated.walkingKm = 2.0;
    updated.waitRisk = "低";
  } else if (hasPhoto) {
    updated.durationMinutes = 175;
    updated.budgetPerPerson = 120;
    updated.walkingKm = 2.6;
    updated.waitRisk = "低-中";
  } else {
    updated.durationMinutes = 166;
    updated.budgetPerPerson = 120;
    updated.walkingKm = 2.3;
    updated.waitRisk = "低-中";
  }

  const routeOrderPenalty = calculateOrderPenalty(updated.nodes);
  updated.durationMinutes += routeOrderPenalty.minutes;
  updated.walkingKm = Number((updated.walkingKm + routeOrderPenalty.km).toFixed(1));
  updated.hint = routeOrderPenalty.minutes > 0 ? "这个顺序会略绕路，建议保留原顺序。" : "";

  updated.transportSegments = buildTransportSegments(updated.nodes);
  updated.nodes = refreshTimes(updated.nodes, updated.durationMinutes);

  if (reason) {
    updated.explanation = reason;
  }

  return updated;
}

function calculateOrderPenalty(nodes) {
  const naturalOrder = ["in77", "brokenBridge", "photoPoint", "baitacoffee", "convenienceRest", "xinbailu", "nongtangli"];
  let penalty = 0;
  nodes.forEach((node, index) => {
    const previous = nodes[index - 1];
    if (!previous) return;
    if (naturalOrder.indexOf(previous.id) > naturalOrder.indexOf(node.id)) penalty += 1;
  });
  return { minutes: penalty * 12, km: penalty * 0.3 };
}

function buildTransportSegments(nodes) {
  const segmentText = {
    "in77-brokenBridge": "约12分钟",
    "brokenBridge-baitacoffee": "约8分钟",
    "baitacoffee-xinbailu": "约10分钟",
    "baitacoffee-nongtangli": "约7分钟",
    "brokenBridge-xinbailu": "约14分钟",
    "brokenBridge-nongtangli": "约12分钟",
    "brokenBridge-photoPoint": "约7分钟",
    "photoPoint-baitacoffee": "约9分钟",
    "convenienceRest-nongtangli": "约8分钟",
    "brokenBridge-convenienceRest": "约8分钟",
    "in77-xinbailu": "约8分钟",
    "in77-nongtangli": "约9分钟",
  };

  return nodes.slice(0, -1).map((node, index) => {
    const next = nodes[index + 1];
    const key = `${node.id}-${next.id}`;
    const reverseKey = `${next.id}-${node.id}`;
    return {
      from: node.name,
      to: next.name,
      method: "步行",
      duration: segmentText[key] || segmentText[reverseKey] || "约12分钟",
    };
  });
}

function refreshTimes(nodes) {
  const startMinutes = 14 * 60;
  const stayByType = {
    start: 5,
    scenic: 35,
    coffee: 35,
    rest: 12,
    dinner: 47,
  };
  let cursor = startMinutes;
  return nodes.map((node, index) => {
    const updated = clone(node);
    const stay = stayByType[updated.type] || 25;
    updated.arrive = toClock(cursor);
    updated.leave = toClock(cursor + stay);
    const segment = index < nodes.length - 1 ? buildTransportSegments(nodes)[index] : null;
    updated.next = segment
      ? `${segment.method}${segment.duration}，前往${nodes[index + 1].name}。`
      : "";
    cursor += stay + (segment ? Number(segment.duration.match(/\d+/)?.[0] || 10) : 0);
    return updated;
  });
}

function toClock(totalMinutes) {
  const hour = Math.floor(totalMinutes / 60);
  const minute = totalMinutes % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
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
  }, 1800);
}

function startGeneration() {
  setState({ view: "loading", loadingStep: 0, diff: null, previousRoute: null, activeAdjustment: null });
  const steps = [1, 2, 3];
  steps.forEach((step, index) => {
    window.setTimeout(() => {
      if (step < 3) {
        setState({ loadingStep: step });
      } else {
        const route = buildDefaultRoute();
        setState({
          view: "result",
          loadingStep: 3,
          route,
          selectedNodeId: route.nodes[0].id,
          hint: "",
        });
      }
    }, 650 + index * 760);
  });
}

function applyAdjustment(type) {
  if (!state.route) return;
  const previousRoute = clone(state.route);
  let nextRoute = clone(state.route);
  let diff = null;

  if (type === "restaurantBusy") {
    nextRoute.nodes = nextRoute.nodes.map((node) =>
      node.type === "dinner" ? clone(alternativePois.nongtangli) : node,
    );
    nextRoute = recalculateRoute(
      nextRoute,
      "已为你只替换晚餐点，其他安排保持不变，整体等待风险更低。",
    );
    diff = {
      title: "餐厅排队太久",
      action: "已为你只替换晚餐点，其他安排保持不变。",
      rows: [
        ["晚餐", `${getDinner(previousRoute).name} → ${getDinner(nextRoute).name}`],
        ["等待风险", `${previousRoute.waitRisk} → ${nextRoute.waitRisk}`],
        ["预计人均", `${previousRoute.budgetPerPerson}元 → ${nextRoute.budgetPerPerson}元`],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(nextRoute.durationMinutes)}`],
        ["步行距离", `${previousRoute.walkingKm}km → ${nextRoute.walkingKm}km`],
        ["保留节点", keptNodes(previousRoute, nextRoute)],
      ],
    };
  }

  if (type === "budget100") {
    nextRoute.nodes = nextRoute.nodes.map((node) => {
      if (node.id === "baitacoffee") return clone(alternativePois.convenienceRest);
      if (node.type === "dinner") return clone(alternativePois.nongtangli);
      return node;
    });
    nextRoute = recalculateRoute(
      nextRoute,
      "已把预算压到人均100以内：保留西湖游览，降低休息和晚餐成本。",
    );
    diff = {
      title: "预算降到 100",
      action: "已降低晚餐预算，并把咖啡改为轻休息点。",
      rows: [
        ["预计人均", `${previousRoute.budgetPerPerson}元 → ${nextRoute.budgetPerPerson}元`],
        ["调整节点", "湖畔白塔咖啡 → 湖滨轻休息点；晚餐改为弄堂里湖滨店"],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(nextRoute.durationMinutes)}`],
        ["保留节点", keptNodes(previousRoute, nextRoute)],
      ],
    };
  }

  if (type === "noCoffee") {
    const removed = nextRoute.nodes.find((node) => node.id === "baitacoffee" || node.type === "coffee");
    nextRoute.nodes = nextRoute.nodes.filter((node) => node.id !== "baitacoffee" && node.type !== "coffee");
    nextRoute = recalculateRoute(nextRoute, "已删除咖啡节点，路线更短，晚餐前少一次停留。");
    diff = {
      title: "不要咖啡",
      action: "已删除咖啡节点，其他节点尽量保持顺路。",
      rows: [
        ["删除节点", removed ? removed.name : "咖啡点"],
        ["预计人均", `${previousRoute.budgetPerPerson}元 → ${nextRoute.budgetPerPerson}元`],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(nextRoute.durationMinutes)}`],
        ["步行距离", `${previousRoute.walkingKm}km → ${nextRoute.walkingKm}km`],
        ["保留节点", keptNodes(previousRoute, nextRoute)],
      ],
    };
  }

  if (type === "twoHours") {
    const dinner = getDinner(nextRoute);
    nextRoute.nodes = [clone(basePois.in77), clone(basePois.brokenBridge), clone(dinner)];
    nextRoute.durationMinutes = 118;
    nextRoute.budgetPerPerson = dinner.id === "nongtangli" ? 65 : 78;
    nextRoute.walkingKm = 1.8;
    nextRoute.waitRisk = dinner.id === "nongtangli" ? "低" : "中";
    nextRoute.transportSummary = "压缩为两小时路线：只保留西湖核心景观点和晚餐收尾。";
    nextRoute = recalculateRoute(nextRoute, "已压缩到约2小时，牺牲了咖啡休息和部分停留时间。");
    diff = {
      title: "只剩 2 小时",
      action: "已压缩停留，只保留最关键的顺路节点。",
      rows: [
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(nextRoute.durationMinutes)}`],
        ["调整方式", "删除或压缩中途停留，优先保证能走完"],
        ["体验取舍", "路线更紧凑，休息时间减少"],
        ["保留节点", keptNodes(previousRoute, nextRoute)],
      ],
    };
  }

  if (type === "photo") {
    const hasPhoto = nextRoute.nodes.some((node) => node.id === "photoPoint");
    if (!hasPhoto) {
      const scenicIndex = nextRoute.nodes.findIndex((node) => node.id === "brokenBridge");
      nextRoute.nodes.splice(scenicIndex + 1, 0, clone(alternativePois.photoPoint));
    }
    nextRoute = recalculateRoute(
      nextRoute,
      "已增加更适合拍照的湖景停留点，同时保留断桥这类高识别度节点。",
    );
    diff = {
      title: "想更适合拍照",
      action: "已增加一个更分散的湖景拍照点。",
      rows: [
        ["新增节点", "北山街湖景点"],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(nextRoute.durationMinutes)}`],
        ["步行距离", `${previousRoute.walkingKm}km → ${nextRoute.walkingKm}km`],
        ["保留节点", keptNodes(previousRoute, nextRoute)],
      ],
    };
  }

  setState({
    previousRoute,
    route: nextRoute,
    diff,
    selectedNodeId: nextRoute.nodes[0]?.id,
    activeAdjustment: type,
    hint: nextRoute.hint || "",
  });
}

function getDinner(route) {
  return route.nodes.find((node) => node.type === "dinner") || clone(basePois.xinbailu);
}

function keptNodes(previousRoute, nextRoute) {
  const nextNames = new Set(nextRoute.nodes.map((node) => node.name));
  return previousRoute.nodes
    .filter((node) => nextNames.has(node.name))
    .map((node) => node.name)
    .join("、");
}

function moveNode(id, direction) {
  if (!state.route) return;
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
  const recalculated = recalculateRoute(nextRoute, "已按你的顺序重算路线，时间和步行距离同步更新。");
  setState({
    previousRoute,
    route: recalculated,
    selectedNodeId: id,
    hint: recalculated.hint || "",
    diff: {
      title: "顺序已调整",
      action: "已重新计算总时长、步行距离和编号。",
      rows: [
        ["路线顺序", recalculated.nodes.map((item) => item.name).join(" → ")],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(recalculated.durationMinutes)}`],
        ["步行距离", `${previousRoute.walkingKm}km → ${recalculated.walkingKm}km`],
      ],
    },
  });
}

function deleteNode(id) {
  if (!state.route) return;
  const previousRoute = clone(state.route);
  const target = previousRoute.nodes.find((node) => node.id === id);
  if (!target) return;
  if (target.type === "start") {
    showToast("起点需要保留，方便继续计算路线");
    return;
  }
  const nextRoute = clone(state.route);
  nextRoute.nodes = nextRoute.nodes.filter((node) => node.id !== id);
  const recalculated = recalculateRoute(nextRoute, "已删除这个目的地，并同步更新后续路线。");
  setState({
    previousRoute,
    route: recalculated,
    selectedNodeId: recalculated.nodes[0]?.id,
    hint: recalculated.hint || "",
    diff: {
      title: "已删除节点",
      action: "已移除相关目的地，并重算路线。",
      rows: [
        ["删除节点", target.name],
        ["总时长", `${formatDuration(previousRoute.durationMinutes)} → ${formatDuration(recalculated.durationMinutes)}`],
        ["预计人均", `${previousRoute.budgetPerPerson}元 → ${recalculated.budgetPerPerson}元`],
        ["保留节点", keptNodes(previousRoute, recalculated)],
      ],
    },
  });
}

function replaceNode(id) {
  if (!state.route) return;
  const target = state.route.nodes.find((node) => node.id === id);
  if (!target) return;
  if (target.type === "dinner") {
    applyAdjustment("restaurantBusy");
    return;
  }
  if (target.type === "coffee") {
    applyAdjustment("budget100");
    return;
  }
  if (target.type === "scenic") {
    applyAdjustment("photo");
    return;
  }
  showToast("这个节点建议保留为路线起点");
}

function acceptNewRoute() {
  setState({ previousRoute: null, diff: null, activeAdjustment: null });
  showToast("已采用新方案");
}

function restoreRoute() {
  if (!state.previousRoute) return;
  setState({
    route: state.previousRoute,
    previousRoute: null,
    diff: null,
    activeAdjustment: null,
    selectedNodeId: state.previousRoute.nodes[0]?.id,
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
          ${examples
            .map(
              (example) => `
                <button class="example" data-action="useExample" data-value="${escapeHtml(example)}">${escapeHtml(example)}</button>
              `,
            )
            .join("")}
        </div>

        <div class="section-label">偏好</div>
        <div class="tag-row">
          ${preferenceTags
            .map(
              (tag) => `
                <button class="tag ${state.selectedPreferences.includes(tag) ? "selected" : ""}" data-action="togglePreference" data-value="${tag}">
                  ${tag}
                </button>
              `,
            )
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
        <div class="pulse-route">
          <span class="pulse-dot one"></span>
          <span class="pulse-dot two"></span>
        </div>
        <div class="loading-title">正在把需求串成路线</div>
        <div class="steps">
          ${steps
            .map((step, index) => {
              const status = state.loadingStep > index ? "done" : state.loadingStep === index ? "active" : "";
              return `
                <div class="step ${status}">
                  <span class="step-dot">${state.loadingStep > index ? "✓" : index + 1}</span>
                  <span>${step}</span>
                </div>
              `;
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
    <section class="screen result">
      <div class="compact-top">
        <div class="compact-title">
          <h2>推荐你这样走</h2>
          <span class="status-pill">现在出发</span>
        </div>
        <div class="chip-row">
          ${route.constraints
            .map(
              (chip) => `
                <button class="chip" data-action="chipTip">${chip.key}：${chip.value}</button>
              `,
            )
            .join("")}
        </div>
      </div>

      ${renderSummary(route)}
      ${renderTransport(route)}
      ${renderMap(route)}
      ${renderTimeline(route)}
      ${renderPoiCards(route)}
      ${renderAdjustmentPanel()}
      ${state.diff ? renderDiffCard(state.diff) : ""}
      <div class="hint ${state.hint ? "show" : ""}">${state.hint}</div>
      <div class="footer-note">当前为黑客松演示版本，排队风险与体验标签由样例数据模拟。</div>
    </section>
    ${renderToast()}
  `;
}

function renderSummary(route) {
  return `
    <section class="card summary-card">
      <span class="summary-label">${route.label}</span>
      <h2>${route.name}</h2>
      <p>${route.explanation}</p>
      <div class="metric-grid">
        <div class="metric"><span>总时长</span><strong>${formatDuration(route.durationMinutes)}</strong></div>
        <div class="metric"><span>预计人均</span><strong>${route.budgetPerPerson}元</strong></div>
        <div class="metric"><span>步行距离</span><strong>${route.walkingKm}km</strong></div>
        <div class="metric"><span>等待风险</span><strong>${route.waitRisk}</strong></div>
      </div>
      <div class="summary-actions">
        <button class="primary" data-action="followRoute">按这条走</button>
        <button class="secondary" data-action="scrollAdjust">调整路线</button>
      </div>
    </section>
  `;
}

function renderTransport(route) {
  return `
    <section class="card">
      <div class="transport-head">
        <h3>交通方案</h3>
        <span class="summary-label">步行优先</span>
      </div>
      <p class="transport-note">${route.transportSummary}</p>
      <div class="segments">
        ${route.transportSegments
          .map(
            (segment) => `
              <div class="segment">
                <span class="walk-icon">步</span>
                <div>
                  <strong>${segment.from} → ${segment.to}</strong>
                  <span>${segment.method}${segment.duration}</span>
                </div>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderMap(route) {
  const points = route.nodes.map((node) => `${node.map.x},${node.map.y}`).join(" ");
  return `
    <section class="card map-card">
      <div class="section-head">
        <h3>路线地图</h3>
        <span class="summary-label">${route.nodes.length}站</span>
      </div>
      <div class="map" aria-label="路线地图">
        <span class="lake-label">西湖水域</span>
        <span class="district-label">湖滨商圈</span>
        <svg class="route-line" viewBox="0 0 100 100" preserveAspectRatio="none">
          <polyline points="${points}"></polyline>
        </svg>
        ${route.nodes
          .map(
            (node, index) => `
              <button
                class="marker ${node.id === state.selectedNodeId ? "active" : ""}"
                style="left:${node.map.x}%;top:${node.map.y}%"
                data-action="selectNode"
                data-id="${node.id}"
                aria-label="${node.name}"
              >${index + 1}</button>
            `,
          )
          .join("")}
      </div>
      <div class="map-caption">
        <span>点击编号查看对应安排</span>
        <span>${route.nodes.find((node) => node.id === state.selectedNodeId)?.name || ""}</span>
      </div>
    </section>
  `;
}

function renderTimeline(route) {
  return `
    <section class="card">
      <div class="section-head">
        <h3>今天怎么走</h3>
        <span class="summary-label">行动指令</span>
      </div>
      <div class="timeline">
        ${route.nodes
          .map(
            (node, index) => `
              <article class="timeline-item ${node.id === state.selectedNodeId ? "active" : ""}" data-action="selectNode" data-id="${node.id}">
                <div class="timebox">
                  <strong>${node.arrive}</strong>
                  <span>${node.leave} 离开</span>
                  <div class="node-dot">${index + 1}</div>
                </div>
                <div class="timeline-body">
                  <h4>${node.name}</h4>
                  <div class="type-line">${typeIcon[node.type]} · ${typeText[node.type]}</div>
                  <p>${node.reason}</p>
                  ${node.note ? `<div class="notice">${node.note}</div>` : ""}
                  ${node.next ? `<div class="next-step">下一步：${node.next}</div>` : ""}
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPoiCards(route) {
  return `
    <section class="card">
      <div class="section-head">
        <h3>目的地</h3>
        <span class="summary-label">可局部调整</span>
      </div>
      <div class="poi-list">
        ${route.nodes
          .map(
            (node, index) => `
              <article class="poi-card card ${node.id === state.selectedNodeId ? "active" : ""}" data-id="${node.id}">
                <div class="poi-visual ${node.type}">
                  <span class="poi-index">${index + 1}</span>
                </div>
                <div class="poi-content">
                  <div class="poi-meta">
                    <span class="poi-type">${typeText[node.type]}</span>
                    <span class="poi-score">评分 ${node.rating}</span>
                  </div>
                  <h4>${node.name}</h4>
                  <p>${node.address}</p>
                  <div class="mini-grid">
                    <div class="mini"><strong>开放时间</strong>${node.openHours}</div>
                    <div class="mini"><strong>价格</strong>${node.price}</div>
                  </div>
                  <div class="small-tags">
                    ${node.tags.map((tag) => `<span>${tag}</span>`).join("")}
                  </div>
                  <p class="why">为什么推荐：${node.reason}</p>
                  <div class="poi-actions">
                    <button class="small-btn primary-mini" data-action="replaceNode" data-id="${node.id}">替换</button>
                    <button class="small-btn" data-action="deleteNode" data-id="${node.id}">删除</button>
                    <button class="small-btn" data-action="moveNodeUp" data-id="${node.id}">上移</button>
                    <button class="small-btn" data-action="moveNodeDown" data-id="${node.id}">下移</button>
                  </div>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderAdjustmentPanel() {
  const buttons = [
    ["restaurantBusy", "餐厅排队太久"],
    ["budget100", "预算降到 100"],
    ["noCoffee", "不要咖啡"],
    ["twoHours", "只剩 2 小时"],
    ["photo", "想更适合拍照"],
  ];
  return `
    <section class="card" id="adjustment-panel">
      <div class="section-head">
        <h3>现场变了，就局部调整</h3>
      </div>
      <p class="transport-note">不重新生成攻略，只替换、删除或调整相关节点，并告诉你变化在哪里。</p>
      <div class="quick-grid">
        ${buttons
          .map(
            ([type, label]) => `
              <button class="quick-btn ${state.activeAdjustment === type ? "active" : ""}" data-action="adjust" data-type="${type}">
                ${label}
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderDiffCard(diff) {
  return `
    <section class="card diff-card">
      <h3>${diff.title}</h3>
      <p class="diff-subtitle">${diff.action}</p>
      <div class="diff-list">
        ${diff.rows
          .map(
            ([label, value]) => `
              <div class="diff-row">
                <span>${label}</span>
                <span>${value}</span>
              </div>
            `,
          )
          .join("")}
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

  if (action === "toggleMic") {
    setState({ micActive: !state.micActive });
  }
  if (action === "useExample") {
    setState({ inputText: target.dataset.value || defaultInput });
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
  if (action === "chipTip") showToast("当前阶段先展示识别结果，稍后可直接编辑");
  if (action === "followRoute") showToast("已进入路线执行视图");
  if (action === "scrollAdjust") {
    document.querySelector("#adjustment-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (action === "selectNode") {
    setState({ selectedNodeId: id });
    window.setTimeout(() => {
      document.querySelector(`.poi-card[data-id="${id}"]`)?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }, 40);
  }
  if (action === "adjust") applyAdjustment(target.dataset.type);
  if (action === "moveNodeUp") moveNode(id, -1);
  if (action === "moveNodeDown") moveNode(id, 1);
  if (action === "deleteNode") deleteNode(id);
  if (action === "replaceNode") replaceNode(id);
  if (action === "acceptRoute") acceptNewRoute();
  if (action === "restoreRoute") restoreRoute();
}

render();
