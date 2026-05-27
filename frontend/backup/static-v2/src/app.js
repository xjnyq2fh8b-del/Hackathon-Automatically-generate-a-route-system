"use strict";

const voiceText = "我在湖滨银泰，下午2点到6点，想轻松逛西湖，喝杯安静一点的咖啡，晚上吃杭帮菜，人均150，不想排队太久";

const examples = [
  "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
  "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，预算人均120",
];

const routeOptions = {
  relaxed: {
    id: "relaxed",
    name: "轻松西湖半日线",
    summary: "这条路线适合下午轻松逛西湖：先看景，再喝咖啡，最后顺路吃晚饭。",
    tag: "当前推荐",
  },
  lowWait: {
    id: "lowWait",
    name: "少排队西湖线",
    summary: "把晚餐换到低等待风险的湖滨附近，减少现场排队的不确定性。",
    tag: "更稳妥",
  },
  budget: {
    id: "budget",
    name: "低预算湖滨线",
    summary: "保留西湖核心游览和本地晚餐，把咖啡与高价餐厅先放下。",
    tag: "省预算",
  },
  photo: {
    id: "photo",
    name: "拍照友好线",
    summary: "增加湖边步道和更有画面感的咖啡点，适合想慢慢拍照的人。",
    tag: "更出片",
  },
};

const poiLibrary = {
  origin: {
    id: "origin",
    name: "湖滨银泰 in77",
    type: "起点",
    icon: "起",
    address: "上城区湖滨商圈",
    hours: "全天可达",
    rating: "4.7",
    price: "免费",
    imageClass: "img-origin",
    tags: ["地铁近", "集合方便"],
    x: 22,
    y: 61,
    stay: 5,
    evidence: ["从湖滨出发，进入西湖东线最顺", "商圈补给方便"],
    reason: "默认从湖滨银泰出发，减少找集合点和绕路成本。",
    risk: null,
  },
  bridge: {
    id: "bridge",
    name: "断桥残雪",
    type: "景点",
    icon: "景",
    address: "西湖区北山街",
    hours: "全天开放",
    rating: "4.6",
    price: "免费",
    imageClass: "img-bridge",
    tags: ["西湖经典", "拍照友好", "游客友好"],
    x: 42,
    y: 34,
    stay: 35,
    evidence: ["离起点不远", "下午光线适合拍湖面", "免费开放"],
    reason: "先去断桥，能最快进入西湖氛围，也方便后面顺路去咖啡点。",
    risk: "游客较多，但不影响路线执行。",
  },
  beishan: {
    id: "beishan",
    name: "北山街湖边步道",
    type: "散步",
    icon: "景",
    address: "西湖区北山街沿线",
    hours: "全天开放",
    rating: "4.8",
    price: "免费",
    imageClass: "img-beishan",
    tags: ["湖景", "慢节奏", "顺路"],
    x: 55,
    y: 28,
    stay: 28,
    evidence: ["顺着湖边走，不需要折返", "比热门点更松弛"],
    reason: "这段适合把景点体验拉开，不会像打卡一样赶。",
    risk: "步行时间会增加，老人小孩场景可跳过。",
  },
  quietCafe: {
    id: "quietCafe",
    name: "湖畔白塔咖啡",
    type: "咖啡",
    icon: "咖",
    address: "湖滨路附近",
    hours: "10:00-21:30",
    rating: "4.5",
    price: "人均42元",
    imageClass: "img-cafe",
    tags: ["安静", "低等待估计", "可休息"],
    x: 47,
    y: 58,
    stay: 35,
    evidence: ["距离上一站约8分钟", "人均在预算内", "历史热度估计等待低"],
    reason: "安排在中段休息，既不打断游览，也给晚饭前留缓冲。",
    risk: "低等待为估计标签，不代表实时排队。",
  },
  photoCafe: {
    id: "photoCafe",
    name: "湖边胶片咖啡",
    type: "咖啡",
    icon: "咖",
    address: "北山街附近",
    hours: "09:30-22:00",
    rating: "4.6",
    price: "人均58元",
    imageClass: "img-photo-cafe",
    tags: ["拍照", "小众感", "顺路估计"],
    x: 62,
    y: 32,
    stay: 42,
    evidence: ["更适合拍照", "靠近湖边步道", "预算略高但仍可控"],
    reason: "如果想要更有城市漫游感，这家咖啡比普通休息点更有记忆点。",
    risk: "会增加约0.6km步行和一点等待风险。",
  },
  xinbailu: {
    id: "xinbailu",
    name: "新白鹿餐厅湖滨店",
    type: "晚餐",
    icon: "餐",
    address: "上城区延安路附近",
    hours: "10:30-21:30",
    rating: "4.4",
    price: "人均78元",
    imageClass: "img-food",
    tags: ["杭帮菜", "预算友好", "家庭友好"],
    x: 26,
    y: 72,
    stay: 55,
    evidence: ["晚餐预算内", "离湖滨近", "适合多人"],
    reason: "最后回到湖滨附近吃晚饭，结束后打车或地铁都方便。",
    risk: "晚高峰可能短时等待。",
  },
  nongtangli: {
    id: "nongtangli",
    name: "弄堂里湖滨店",
    type: "晚餐",
    icon: "餐",
    address: "上城区平海路附近",
    hours: "11:00-21:00",
    rating: "4.3",
    price: "人均88元",
    imageClass: "img-food-2",
    tags: ["杭帮菜", "低等待估计", "离湖滨近"],
    x: 31,
    y: 68,
    stay: 55,
    evidence: ["比原晚餐点更靠近路线末段", "等待风险估计更低", "仍保留杭帮菜"],
    reason: "当用户说排队太久时，优先局部替换晚餐，不重做整条路线。",
    risk: "低等待为估计标签，建议出发前确认。",
  },
  zhiweiguan: {
    id: "zhiweiguan",
    name: "知味观仁和路店",
    type: "晚餐",
    icon: "餐",
    address: "上城区仁和路",
    hours: "07:00-21:00",
    rating: "4.2",
    price: "人均48元",
    imageClass: "img-budget",
    tags: ["本地特色", "低预算", "游客友好"],
    x: 24,
    y: 67,
    stay: 45,
    evidence: ["人均更低", "保留本地特色", "离湖滨近"],
    reason: "预算降到50时，保留晚餐体验，但把咖啡和更高价餐厅拿掉。",
    risk: "正餐峰值仍可能排队。",
  },
};

const routeRecipes = {
  relaxed: ["origin", "bridge", "quietCafe", "xinbailu"],
  lowWait: ["origin", "bridge", "quietCafe", "nongtangli"],
  budget: ["origin", "bridge", "zhiweiguan"],
  photo: ["origin", "bridge", "beishan", "photoCafe", "xinbailu"],
};

const state = {
  view: "input",
  input: examples[0],
  preferences: ["少排队", "拍照好看"],
  listening: false,
  constraints: null,
  selectedRoute: "relaxed",
  route: null,
  selectedPoiId: null,
  diff: null,
  replanInput: "",
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function icon(name) {
  const icons = {
    mic: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14a4 4 0 0 0 4-4V6a4 4 0 1 0-8 0v4a4 4 0 0 0 4 4Z"/><path d="M19 10a7 7 0 0 1-14 0"/><path d="M12 17v4"/><path d="M8 21h8"/></svg>`,
    send: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></svg>`,
    map: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18-6 3V6l6-3 6 3 6-3v15l-6 3-6-3Z"/><path d="M9 3v15"/><path d="M15 6v15"/></svg>`,
    clock: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`,
    alert: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5"/><path d="M12 17h.01"/></svg>`,
    swap: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h11l-3-3"/><path d="M17 17H6l3 3"/><path d="M18 7l-3 3"/><path d="M6 17l3-3"/></svg>`,
    up: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 15 6-6 6 6"/></svg>`,
    down: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>`,
    close: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
  };
  return icons[name] || "";
}

function parseIntent(text, preferences) {
  const source = text || "";
  const budgetMatch = source.match(/人均\s*(\d+)|预算.*?(\d+)/);
  const timeMatch = source.match(/(\d{1,2})\s*点.*?(\d{1,2})\s*点/);
  const preferenceSet = new Set(preferences);

  if (/不想排队|不排队|少排队|排队太久/.test(source)) preferenceSet.add("少排队");
  if (/少走|不想走|老人|小孩|轻松/.test(source)) preferenceSet.add("少走路");
  if (/拍照|出片|好看|小众|不要太网红/.test(source)) preferenceSet.add("拍照好看");
  if (/杭帮菜|本地|知味观/.test(source)) preferenceSet.add("本地特色");

  return {
    origin: source.includes("湖滨银泰") ? "湖滨银泰 in77" : "西湖湖滨附近",
    area: "杭州西湖周边",
    timeWindow: {
      start: timeMatch ? `${timeMatch[1].padStart(2, "0")}:00` : "14:00",
      end: timeMatch ? `${timeMatch[2].padStart(2, "0")}:00` : "18:00",
    },
    budget: budgetMatch ? Number(budgetMatch[1] || budgetMatch[2]) : 150,
    companions: /老人|小孩|孩子/.test(source) ? "老人小孩同行" : "朋友/个人出行",
    goals: [
      "西湖景点",
      ...(!/不要咖啡|不喝咖啡/.test(source) && /咖啡/.test(source) ? ["咖啡休息"] : []),
      ...(/晚饭|晚餐|吃饭|杭帮菜/.test(source) ? ["晚餐"] : []),
    ],
    preferences: Array.from(preferenceSet),
    waitTolerance: /不想排队|少排队/.test(source) ? "低：不想长时间等待" : "中：可接受短时间等待",
    rawInput: source,
  };
}

function chooseRoute(constraints) {
  if (constraints.budget <= 60) return "budget";
  if (constraints.preferences.includes("拍照好看") && constraints.rawInput.includes("小众")) return "photo";
  return "relaxed";
}

function getPoi(id) {
  return clone(poiLibrary[id]);
}

function makeRoute(routeId, constraints, customNodes) {
  const option = routeOptions[routeId];
  const nodes = customNodes ? clone(customNodes) : routeRecipes[routeId].map(getPoi);
  const travelMinutes = Math.max(18, (nodes.length - 1) * (routeId === "photo" ? 15 : routeId === "budget" ? 10 : 12));
  const stayMinutes = nodes.reduce((sum, node) => sum + node.stay, 0);
  const paid = nodes.reduce((sum, node) => sum + extractPrice(node.price), 0);
  const walking = routeId === "photo" ? 3.6 : routeId === "budget" ? 1.6 : routeId === "lowWait" ? 2.1 : 2.3;
  const waitRisk = nodes.some((node) => node.tags.includes("低等待估计")) ? "低-中" : "中";

  return {
    ...option,
    constraints,
    nodes,
    metrics: {
      minutes: stayMinutes + travelMinutes,
      cost: paid,
      walking,
      waitRisk,
    },
    transport: buildTransport(nodes, routeId),
    notices: buildNotices(nodes, constraints, walking),
  };
}

function extractPrice(priceText) {
  const match = String(priceText).match(/(\d+)/);
  return match ? Number(match[1]) : 0;
}

function buildTransport(nodes, routeId) {
  return nodes.slice(1).map((node, index) => {
    const minutes = routeId === "photo" ? 15 : routeId === "budget" ? 10 : 12;
    return {
      from: nodes[index].name,
      to: node.name,
      mode: "步行",
      minutes,
      note: index === 0 ? "从湖滨进入西湖东线" : "顺着湖边或湖滨商圈移动",
    };
  });
}

function buildNotices(nodes, constraints, walking) {
  const notices = ["排队、拍照、安静等为 Demo 估计标签，不代表实时官方数据。"];
  if (walking > 3) notices.push("这条线更有漫游感，但步行距离会明显增加。");
  if (constraints.budget < nodes.reduce((sum, node) => sum + extractPrice(node.price), 0)) notices.push("预计消费可能超过当前预算，建议切换低预算湖滨线。");
  const risky = nodes.find((node) => node.risk);
  if (risky) notices.push(`${risky.name}：${risky.risk}`);
  return notices;
}

function generateRoute() {
  const constraints = parseIntent(state.input, state.preferences);
  const routeId = chooseRoute(constraints);
  state.constraints = constraints;
  state.selectedRoute = routeId;
  state.route = makeRoute(routeId, constraints);
  state.selectedPoiId = state.route.nodes[1]?.id || state.route.nodes[0]?.id;
  state.diff = null;
  state.view = "result";
}

function switchRoute(routeId) {
  state.selectedRoute = routeId;
  state.route = makeRoute(routeId, state.constraints);
  state.selectedPoiId = state.route.nodes[1]?.id || state.route.nodes[0]?.id;
  state.diff = null;
}

function replaceDinner() {
  const previous = clone(state.route);
  const nodes = state.route.nodes.map((node) => (node.type === "晚餐" ? getPoi("nongtangli") : node));
  state.route = makeRoute("lowWait", state.constraints, nodes);
  state.selectedRoute = "lowWait";
  state.selectedPoiId = "nongtangli";
  state.diff = makeDiff({
    title: "已把晚餐换成更稳妥的一家",
    intent: "识别到：餐厅排队太久，优先替换晚餐点，其他节点保持不变。",
    previous,
    current: state.route,
    changed: "新白鹿餐厅湖滨店 → 弄堂里湖滨店",
    reason: "新餐厅仍在湖滨附近，保留杭帮菜和晚餐需求，同时降低等待风险估计。",
  });
}

function removeCoffeeForBudget() {
  const previous = clone(state.route);
  const nodes = [getPoi("origin"), getPoi("bridge"), getPoi("zhiweiguan")];
  state.route = makeRoute("budget", { ...state.constraints, budget: 50 }, nodes);
  state.selectedRoute = "budget";
  state.selectedPoiId = "zhiweiguan";
  state.diff = makeDiff({
    title: "已压低预算，咖啡先拿掉",
    intent: "识别到：预算降到50，不要咖啡，但晚饭保留。",
    previous,
    current: state.route,
    changed: "删除咖啡节点，晚餐改为知味观仁和路店",
    reason: "保留西湖核心游览和本地特色晚餐，牺牲中途休息与拍照咖啡体验。",
  });
}

function shortenRoute() {
  const previous = clone(state.route);
  const dinner = state.route.nodes.find((node) => node.type === "晚餐") || getPoi("nongtangli");
  const nodes = [getPoi("origin"), getPoi("bridge"), dinner];
  state.route = makeRoute("relaxed", state.constraints, nodes);
  state.selectedPoiId = dinner.id;
  state.diff = makeDiff({
    title: "已压缩到更适合2小时的版本",
    intent: "识别到：现场时间变短，优先保留一个景点和晚餐。",
    previous,
    current: state.route,
    changed: "删去中途咖啡/散步节点",
    reason: "减少停留点后更容易按时完成，代价是城市漫游感变弱。",
  });
}

function addPhotoCafe() {
  const previous = clone(state.route);
  const nodes = clone(state.route.nodes);
  const hasCafe = nodes.some((node) => node.id === "photoCafe");
  if (!hasCafe) {
    const dinnerIndex = nodes.findIndex((node) => node.type === "晚餐");
    nodes.splice(Math.max(1, dinnerIndex), 0, getPoi("photoCafe"));
  }
  state.route = makeRoute("photo", state.constraints, nodes);
  state.selectedRoute = "photo";
  state.selectedPoiId = "photoCafe";
  state.diff = makeDiff({
    title: "已加入更适合拍照的咖啡点",
    intent: "识别到：想要更出片，但不要完全重做路线。",
    previous,
    current: state.route,
    changed: "新增湖边胶片咖啡",
    reason: "咖啡点靠近湖边步道，拍照体验更强，但会增加时间和步行。",
  });
}

function makeDiff({ title, intent, previous, current, changed, reason }) {
  return {
    title,
    intent,
    changed,
    reason,
    delta: {
      cost: [previous.metrics.cost, current.metrics.cost],
      walking: [previous.metrics.walking, current.metrics.walking],
      minutes: [previous.metrics.minutes, current.metrics.minutes],
      waitRisk: [previous.metrics.waitRisk, current.metrics.waitRisk],
    },
    kept: current.nodes.filter((node) => previous.nodes.some((oldNode) => oldNode.id === node.id)).map((node) => node.name),
  };
}

function deletePoi(id) {
  if (id === "origin") return;
  const previous = clone(state.route);
  const nodes = state.route.nodes.filter((node) => node.id !== id);
  state.route = makeRoute(state.selectedRoute, state.constraints, nodes);
  state.selectedPoiId = state.route.nodes[1]?.id || state.route.nodes[0]?.id;
  state.diff = makeDiff({
    title: "已删除该节点并重新检查顺路性",
    intent: "识别到：用户手动删除目的地。",
    previous,
    current: state.route,
    changed: `删除 ${previous.nodes.find((node) => node.id === id)?.name || "一个节点"}`,
    reason: "删除后路线会保持原顺序，后续接入高德距离计算后可重新排序。",
  });
}

function movePoi(id, direction) {
  const index = state.route.nodes.findIndex((node) => node.id === id);
  const target = index + direction;
  if (index <= 0 || target <= 0 || target >= state.route.nodes.length) return;
  const previous = clone(state.route);
  const nodes = clone(state.route.nodes);
  const [item] = nodes.splice(index, 1);
  nodes.splice(target, 0, item);
  state.route = makeRoute(state.selectedRoute, state.constraints, nodes);
  state.selectedPoiId = id;
  state.diff = makeDiff({
    title: "已调整顺序，并重新提示顺路性",
    intent: "识别到：用户手动调整目的地顺序。",
    previous,
    current: state.route,
    changed: `${item.name} 顺序已调整`,
    reason: "当前先按前端顺序更新，后续会接入高德路径计算判断是否明显绕路。",
  });
}

function handleReplanText() {
  const text = state.replanInput;
  if (/排队|换.*餐|餐厅/.test(text)) replaceDinner();
  else if (/预算|50|不要咖啡|不喝咖啡/.test(text)) removeCoffeeForBudget();
  else if (/2小时|两小时|时间不够|只剩/.test(text)) shortenRoute();
  else if (/拍照|出片|咖啡/.test(text)) addPhotoCafe();
  else replaceDinner();
}

function mapAdapter(route) {
  const points = route.nodes.map((node, index) => ({
    id: node.id,
    label: index + 1,
    name: node.name,
    x: node.x,
    y: node.y,
  }));
  return { points, line: points.map((point) => `${point.x},${point.y}`).join(" ") };
}

function render() {
  const app = document.querySelector("#app");
  app.innerHTML = `
    <main>
      ${renderHero()}
      ${state.view === "result" && state.route ? renderResult() : ""}
    </main>
  `;
  bindEvents();
}

function renderHero() {
  const generated = state.view === "result";
  return `
    <section class="hero ${generated ? "hero-compact" : ""}">
      <div class="hero-copy">
        <p class="eyebrow">杭州西湖周边 · 现在出发</p>
        <h1>说出你的出行目标，我帮你串成一条能直接走的路线。</h1>
        <p class="hero-subtitle">先给最推荐的走法，地图、时间轴和目的地卡片再逐步展开。排队与体验信息当前为 Demo 估计标签。</p>
      </div>
      <div class="input-card">
        <div class="input-shell">
          <button class="mic-button ${state.listening ? "listening" : ""}" id="micButton" aria-label="模拟语音输入">${icon("mic")}</button>
          <textarea id="intentInput" rows="3" placeholder="例如：我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队">${state.input}</textarea>
          <button class="send-button" id="generateButton">${icon("send")} 生成路线</button>
        </div>
        <div class="microcopy">${state.listening ? "正在模拟语音输入，会自动整理成一句完整需求..." : "后续可接入语音转文字和 LLM 约束解析；现在点击麦克风可看演示态。"}</div>
        <div class="example-row">
          ${examples.map((example, index) => `<button data-example="${index}">${example}</button>`).join("")}
        </div>
        <div class="preference-row">
          <span>补充偏好</span>
          ${["少排队", "少走路", "拍照好看", "本地特色"].map((preference) => {
            const active = state.preferences.includes(preference);
            return `<button class="${active ? "active" : ""}" data-preference="${preference}">${preference}</button>`;
          }).join("")}
        </div>
      </div>
    </section>
  `;
}

function renderResult() {
  return `
    <section class="result-shell">
      ${renderRouteLead()}
      <div class="content-grid">
        ${renderMap()}
        ${renderTimeline()}
      </div>
      ${renderDestinationCards()}
      ${renderReplanPanel()}
    </section>
  `;
}

function renderRouteLead() {
  const route = state.route;
  return `
    <section class="route-lead">
      <div class="route-title">
        <span>${route.tag}</span>
        <h2>${route.name}</h2>
        <p>${route.summary}</p>
      </div>
      <div class="route-metrics">
        <div><b>${minutesToText(route.metrics.minutes)}</b><span>预计总时长</span></div>
        <div><b>${route.metrics.cost}元</b><span>预计人均</span></div>
        <div><b>${route.metrics.walking.toFixed(1)}km</b><span>步行距离</span></div>
        <div><b>${route.metrics.waitRisk}</b><span>等待风险</span></div>
      </div>
      <button class="go-button">按这条走</button>
    </section>
    <section class="route-switcher" aria-label="路线方案切换">
      ${Object.values(routeOptions).map((option) => `
        <button class="${state.selectedRoute === option.id ? "active" : ""}" data-route="${option.id}">
          <span>${option.tag}</span>
          <b>${option.name}</b>
        </button>
      `).join("")}
    </section>
  `;
}

function renderMap() {
  const map = mapAdapter(state.route);
  return `
    <section class="map-card">
      <div class="section-head">
        <div>
          <h3>${icon("map")} 路线地图</h3>
          <p>静态高德风格底图占位，后续用高德 JS API 替换底图层。</p>
        </div>
        <span>西湖东线</span>
      </div>
      <div class="amap-mock">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
          <path class="water" d="M38 5 C66 0 91 21 88 50 C85 82 54 99 29 82 C7 67 10 19 38 5Z"></path>
          <path class="park" d="M10 40 C25 32 37 36 43 52 C49 69 37 86 19 82 C6 78 2 54 10 40Z"></path>
          <path class="road main-road" d="M7 67 C24 61 39 62 54 70 C67 77 78 78 93 70"></path>
          <path class="road" d="M18 20 C31 28 43 33 62 30 C74 28 83 35 91 46"></path>
          <path class="road" d="M20 88 C31 76 38 64 47 51 C55 39 64 31 78 23"></path>
          <polyline class="route-polyline" points="${map.line}"></polyline>
        </svg>
        <div class="map-place lake-label">西湖</div>
        <div class="map-place hubin-label">湖滨商圈</div>
        ${map.points.map((point) => `
          <button class="route-marker ${state.selectedPoiId === point.id ? "active" : ""}" style="left:${point.x}%;top:${point.y}%;" data-poi="${point.id}">
            <i>${point.label}</i><span>${point.name}</span>
          </button>
        `).join("")}
      </div>
    </section>
  `;
}

function renderTimeline() {
  let cursor = toMinutes(state.constraints.timeWindow.start);
  return `
    <section class="timeline-card">
      <div class="section-head">
        <div>
          <h3>${icon("clock")} 今天怎么走</h3>
          <p>只突出关键动作，详细信息放在目的地卡片里。</p>
        </div>
      </div>
      <div class="timeline">
        ${state.route.nodes.map((node, index) => {
          const arrive = fromMinutes(cursor);
          cursor += node.stay;
          const leave = fromMinutes(cursor);
          const transport = state.route.transport[index];
          if (transport) cursor += transport.minutes;
          return `
            <article class="timeline-node ${state.selectedPoiId === node.id ? "featured" : ""}" data-poi="${node.id}">
              <div class="node-time"><b>${arrive}</b><span>${leave}离开</span></div>
              <div class="node-main">
                <div class="type-icon">${node.icon}</div>
                <div>
                  <h4>${node.name}</h4>
                  <p>${node.reason}</p>
                  ${node.risk ? `<div class="inline-risk">${icon("alert")} ${node.risk}</div>` : ""}
                  ${transport ? `<div class="transport-line">${transport.mode}约${transport.minutes}分钟 · ${transport.note}</div>` : ""}
                </div>
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderDestinationCards() {
  return `
    <section class="destinations">
      <div class="section-head">
        <div>
          <h3>目的地卡片</h3>
          <p>参考行程卡片形态：开放时间、评价、图片、价格和可调整操作放在同一张卡里。</p>
        </div>
      </div>
      <div class="destination-row">
        ${state.route.nodes.map((node, index) => renderPoiCard(node, index)).join("")}
      </div>
    </section>
  `;
}

function renderPoiCard(node, index) {
  const canMoveUp = index > 1;
  const canMoveDown = index > 0 && index < state.route.nodes.length - 1;
  return `
    <article class="destination-card ${state.selectedPoiId === node.id ? "active" : ""}" data-poi="${node.id}">
      <div class="poi-image ${node.imageClass}">
        <span class="type-icon">${node.icon}</span>
        <b>${node.type}</b>
      </div>
      <div class="poi-content">
        <div class="poi-head">
          <div>
            <h4>${node.name}</h4>
            <p>${node.address}</p>
          </div>
          <span>${index + 1}</span>
        </div>
        <div class="poi-facts">
          <span>${node.hours}</span>
          <span>评分 ${node.rating}</span>
          <span>${node.price}</span>
        </div>
        <div class="tag-list">${node.tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
        <div class="evidence-list">
          ${node.evidence.map((item) => `<p>${item}</p>`).join("")}
        </div>
        <div class="card-actions">
          ${node.type === "晚餐" ? `<button data-action="replaceDinner">${icon("swap")} 替换</button>` : ""}
          ${node.type === "咖啡" ? `<button data-action="removeCoffee">${icon("close")} 删除</button>` : ""}
          ${node.id !== "origin" ? `<button data-delete="${node.id}">${icon("close")} 移除</button>` : ""}
          <button ${canMoveUp ? "" : "disabled"} data-move="${node.id}" data-dir="-1">${icon("up")}</button>
          <button ${canMoveDown ? "" : "disabled"} data-move="${node.id}" data-dir="1">${icon("down")}</button>
        </div>
      </div>
    </article>
  `;
}

function renderReplanPanel() {
  return `
    <section class="replan-panel">
      <div class="replan-main">
        <div class="section-head">
          <div>
            <h3>现场变了，就局部调整</h3>
            <p>不重新生成攻略，只替换、删除或压缩路线节点，并告诉你变化在哪里。</p>
          </div>
        </div>
        <div class="replan-input">
          <input id="replanInput" value="${state.replanInput}" placeholder="例如：这家餐厅排队太久，换一家近一点的" />
          <button id="replanButton">调整路线</button>
        </div>
        <div class="quick-replans">
          <button data-action="replaceDinner">餐厅排队太久</button>
          <button data-action="removeCoffee">预算降到50，不要咖啡</button>
          <button data-action="shorten">只剩2小时</button>
          <button data-action="addPhotoCafe">想更适合拍照</button>
        </div>
      </div>
      ${state.diff ? renderDiff() : renderNoDiff()}
    </section>
  `;
}

function renderNoDiff() {
  return `
    <aside class="diff-card empty">
      <h3>变化会显示在这里</h3>
      <p>比如：原餐厅换成哪家、预算少了多少、步行有没有变长、哪些节点保持不变。</p>
    </aside>
  `;
}

function renderDiff() {
  const diff = state.diff;
  return `
    <aside class="diff-card">
      <span class="diff-label">已再规划</span>
      <h3>${diff.title}</h3>
      <p>${diff.intent}</p>
      <div class="changed-box">${diff.changed}</div>
      <div class="delta-grid">
        <div><span>人均</span><b>${diff.delta.cost[0]} → ${diff.delta.cost[1]}元</b></div>
        <div><span>步行</span><b>${diff.delta.walking[0].toFixed(1)} → ${diff.delta.walking[1].toFixed(1)}km</b></div>
        <div><span>耗时</span><b>${minutesToText(diff.delta.minutes[0])} → ${minutesToText(diff.delta.minutes[1])}</b></div>
        <div><span>等待</span><b>${diff.delta.waitRisk[0]} → ${diff.delta.waitRisk[1]}</b></div>
      </div>
      <div class="kept-list"><b>保留：</b>${diff.kept.join("、")}</div>
      <p class="diff-reason">${diff.reason}</p>
    </aside>
  `;
}

function bindEvents() {
  document.querySelector("#intentInput")?.addEventListener("input", (event) => {
    state.input = event.target.value;
  });

  document.querySelector("#generateButton")?.addEventListener("click", () => {
    generateRoute();
    render();
    window.requestAnimationFrame(() => document.querySelector(".result-shell")?.scrollIntoView({ behavior: "smooth", block: "start" }));
  });

  document.querySelector("#micButton")?.addEventListener("click", () => {
    state.listening = true;
    render();
    window.setTimeout(() => {
      state.input = voiceText;
      state.listening = false;
      render();
    }, 850);
  });

  document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
      state.input = examples[Number(button.dataset.example)];
      render();
    });
  });

  document.querySelectorAll("[data-preference]").forEach((button) => {
    button.addEventListener("click", () => {
      const preference = button.dataset.preference;
      state.preferences = state.preferences.includes(preference)
        ? state.preferences.filter((item) => item !== preference)
        : [...state.preferences, preference];
      render();
    });
  });

  document.querySelectorAll("[data-route]").forEach((button) => {
    button.addEventListener("click", () => {
      switchRoute(button.dataset.route);
      render();
    });
  });

  document.querySelectorAll("[data-poi]").forEach((element) => {
    element.addEventListener("click", () => {
      state.selectedPoiId = element.dataset.poi;
      render();
    });
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      runAction(button.dataset.action);
      render();
      window.requestAnimationFrame(() => document.querySelector(".diff-card")?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
    });
  });

  document.querySelectorAll("[data-delete]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      deletePoi(button.dataset.delete);
      render();
    });
  });

  document.querySelectorAll("[data-move]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      movePoi(button.dataset.move, Number(button.dataset.dir));
      render();
    });
  });

  document.querySelector("#replanInput")?.addEventListener("input", (event) => {
    state.replanInput = event.target.value;
  });

  document.querySelector("#replanButton")?.addEventListener("click", () => {
    handleReplanText();
    render();
  });
}

function runAction(action) {
  if (action === "replaceDinner") replaceDinner();
  if (action === "removeCoffee") removeCoffeeForBudget();
  if (action === "shorten") shortenRoute();
  if (action === "addPhotoCafe") addPhotoCafe();
}

function minutesToText(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}小时${m ? `${m}分钟` : ""}` : `${m}分钟`;
}

function toMinutes(time) {
  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}

function fromMinutes(total) {
  const hours = Math.floor(total / 60) % 24;
  const minutes = total % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

render();
