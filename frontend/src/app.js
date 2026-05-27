"use strict";

const examples = [
  "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
  "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，预算人均120",
  "我想找适合拍照但不要太网红的咖啡店，顺路喝咖啡，晚上吃点本地特色",
];

const strategyMeta = {
  balanced: { label: "综合推荐", tone: "orange", description: "兼顾体验、预算、距离和等待风险" },
  lowWalk: { label: "少走路", tone: "green", description: "减少步行段，必要时使用打车衔接" },
  lowWait: { label: "低等待", tone: "blue", description: "降低餐饮排队风险，牺牲少量网红热度" },
  budget: { label: "低预算", tone: "yellow", description: "保留核心体验，压低餐饮和咖啡消费" },
  complete: { label: "体验更完整", tone: "purple", description: "增加拍照和夜景节点，节奏更满" },
};

const basePois = [
  {
    id: "hubin",
    name: "湖滨银泰 in77",
    type: "出发地",
    address: "杭州市上城区湖滨商圈",
    x: 16,
    y: 58,
    price: 0,
    rating: 4.7,
    hours: "全天可达",
    tags: ["地铁近", "集合方便", "商业配套"],
    waitRisk: "低",
    stayMinutes: 5,
    reason: "作为出发点交通方便，适合快速进入西湖东线。",
    scores: { preference: 84, budget: 100, distance: 92, wait: 94, hours: 100 },
  },
  {
    id: "broken-bridge",
    name: "断桥残雪",
    type: "景点",
    address: "杭州市西湖区北山街",
    x: 37,
    y: 37,
    price: 0,
    rating: 4.6,
    hours: "全天开放",
    tags: ["西湖经典", "拍照", "游客友好"],
    waitRisk: "低",
    stayMinutes: 35,
    reason: "从湖滨出发顺路，能快速建立西湖游玩的空间感。",
    scores: { preference: 90, budget: 100, distance: 86, wait: 88, hours: 100 },
  },
  {
    id: "beishan",
    name: "北山街湖边步道",
    type: "散步",
    address: "杭州市西湖区北山街沿线",
    x: 51,
    y: 28,
    price: 0,
    rating: 4.8,
    hours: "全天开放",
    tags: ["湖景", "慢节奏", "拍照"],
    waitRisk: "低",
    stayMinutes: 30,
    reason: "比热门观景点更舒展，适合把景点和咖啡串起来。",
    scores: { preference: 92, budget: 100, distance: 78, wait: 90, hours: 100 },
  },
  {
    id: "solitary-hill",
    name: "孤山路观景点",
    type: "拍照点",
    address: "杭州市西湖区孤山路",
    x: 58,
    y: 42,
    price: 0,
    rating: 4.7,
    hours: "全天开放",
    tags: ["拍照", "西湖经典", "体验完整"],
    waitRisk: "中",
    stayMinutes: 30,
    reason: "景观完整度高，但会增加一些步行和游览时长。",
    scores: { preference: 94, budget: 100, distance: 70, wait: 70, hours: 100 },
  },
  {
    id: "quiet-cafe",
    name: "湖畔白塔咖啡",
    type: "咖啡",
    address: "杭州市上城区湖滨路附近",
    x: 42,
    y: 63,
    price: 42,
    rating: 4.5,
    hours: "10:00-21:30",
    tags: ["安静", "拍照", "低等待估计"],
    waitRisk: "低",
    stayMinutes: 35,
    reason: "距离上一站步行约8分钟，人均在预算内，等待风险较低。",
    scores: { preference: 88, budget: 84, distance: 84, wait: 92, hours: 96 },
  },
  {
    id: "photo-cafe",
    name: "湖边胶片咖啡",
    type: "咖啡",
    address: "杭州市西湖区北山街附近",
    x: 61,
    y: 31,
    price: 58,
    rating: 4.6,
    hours: "09:30-22:00",
    tags: ["拍照", "小众感", "顺路估计"],
    waitRisk: "中",
    stayMinutes: 40,
    reason: "更适合拍照，但绕行和等待风险略高。",
    scores: { preference: 95, budget: 74, distance: 68, wait: 70, hours: 96 },
  },
  {
    id: "family-restaurant",
    name: "新白鹿餐厅湖滨店",
    type: "晚餐",
    address: "杭州市上城区延安路附近",
    x: 22,
    y: 72,
    price: 78,
    rating: 4.4,
    hours: "10:30-21:30",
    tags: ["杭帮菜", "家庭友好", "预算友好"],
    waitRisk: "中",
    stayMinutes: 55,
    reason: "人均低于预算，适合晚餐收尾，但晚高峰可能短时等待。",
    scores: { preference: 86, budget: 90, distance: 82, wait: 72, hours: 94 },
  },
  {
    id: "lowwait-restaurant",
    name: "弄堂里湖滨店",
    type: "晚餐",
    address: "杭州市上城区平海路附近",
    x: 29,
    y: 68,
    price: 88,
    rating: 4.3,
    hours: "11:00-21:00",
    tags: ["杭帮菜", "低等待估计", "离湖滨近"],
    waitRisk: "低",
    stayMinutes: 55,
    reason: "距离路线末段更近，历史热度估计等待风险较低。",
    scores: { preference: 82, budget: 84, distance: 88, wait: 90, hours: 90 },
  },
  {
    id: "budget-restaurant",
    name: "知味观仁和路店",
    type: "晚餐",
    address: "杭州市上城区仁和路",
    x: 19,
    y: 66,
    price: 48,
    rating: 4.2,
    hours: "07:00-21:00",
    tags: ["本地特色", "低预算", "游客友好"],
    waitRisk: "中",
    stayMinutes: 45,
    reason: "预算降低后仍能保留本地特色晚餐，建议避开正餐峰值。",
    scores: { preference: 80, budget: 98, distance: 86, wait: 68, hours: 92 },
  },
  {
    id: "tea-restaurant",
    name: "茶人村龙井路店",
    type: "晚餐",
    address: "杭州市西湖区龙井路",
    x: 80,
    y: 70,
    price: 132,
    rating: 4.6,
    hours: "10:00-21:00",
    tags: ["本地特色", "体验完整", "环境好"],
    waitRisk: "高",
    stayMinutes: 70,
    reason: "体验完整但明显绕路，且晚餐等待风险较高。",
    scores: { preference: 94, budget: 58, distance: 42, wait: 45, hours: 88 },
  },
];

const routeRecipes = {
  balanced: ["hubin", "broken-bridge", "quiet-cafe", "family-restaurant"],
  lowWalk: ["hubin", "broken-bridge", "lowwait-restaurant"],
  lowWait: ["hubin", "beishan", "quiet-cafe", "lowwait-restaurant"],
  budget: ["hubin", "broken-bridge", "budget-restaurant"],
  complete: ["hubin", "broken-bridge", "beishan", "photo-cafe", "tea-restaurant"],
};

const state = {
  input: examples[0],
  quickTags: ["少排队", "拍照好看"],
  constraints: null,
  plans: {},
  selectedStrategy: "balanced",
  selectedPoiId: null,
  replanDiff: null,
  routeGenerated: false,
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function getPoi(id) {
  return clone(basePois.find((poi) => poi.id === id));
}

function parseIntent(text, quickTags = []) {
  const source = text || "";
  const budgetMatch = source.match(/人均\s*(\d+)|预算.*?(\d+)/);
  const timeMatch = source.match(/(\d{1,2})\s*点.*?(\d{1,2})\s*点/);
  const wantsFamily = /老人|小孩|孩子|亲子/.test(source);
  const wantsCoffee = !/不要咖啡|不喝咖啡/.test(source) && /咖啡/.test(source);
  const wantsDinner = /晚饭|晚餐|吃饭|杭帮菜|本地特色/.test(source);
  const preferences = new Set(quickTags);

  if (/不想排队|少排队|不排队|低等待/.test(source)) preferences.add("少排队");
  if (/少走路|不想走|老人|小孩|轻松/.test(source)) preferences.add("少走路");
  if (/拍照|好看|小众|不要太网红/.test(source)) preferences.add("拍照好看");
  if (/本地特色|杭帮菜|知味观/.test(source)) preferences.add("本地特色");
  if (/安静|休息/.test(source)) preferences.add("安静");

  return {
    rawInput: source,
    origin: source.includes("湖滨银泰") ? "湖滨银泰 in77" : "杭州西湖湖滨附近",
    area: "杭州西湖周边",
    timeWindow: {
      start: timeMatch ? `${timeMatch[1].padStart(2, "0")}:00` : "14:00",
      end: timeMatch ? `${timeMatch[2].padStart(2, "0")}:00` : "18:00",
    },
    budgetPerPerson: budgetMatch ? Number(budgetMatch[1] || budgetMatch[2]) : wantsFamily ? 120 : 150,
    companions: wantsFamily ? "老人小孩同行" : "朋友/个人即时出行",
    goals: [
      "西湖景点",
      ...(wantsCoffee ? ["咖啡休息"] : []),
      ...(wantsDinner ? ["晚餐"] : ["轻食"]),
    ],
    preferences: Array.from(preferences),
    transport: wantsFamily || preferences.has("少走路") ? "步行 + 短途打车" : "步行优先",
    waitTolerance: preferences.has("少排队") || /不想排队/.test(source) ? "低：不接受长时间排队" : "中：可接受约20分钟等待",
  };
}

function calculatePlanMetrics(nodes, strategy) {
  const paidNodes = nodes.filter((node) => node.price > 0);
  const totalPrice = paidNodes.reduce((sum, node) => sum + node.price, 0);
  const stayMinutes = nodes.reduce((sum, node) => sum + node.stayMinutes, 0);
  const legMinutes = Math.max(18, (nodes.length - 1) * (strategy === "lowWalk" ? 10 : strategy === "complete" ? 16 : 12));
  const walkKm = {
    balanced: 2.4,
    lowWalk: 1.2,
    lowWait: 2.1,
    budget: 1.8,
    complete: 4.1,
  }[strategy];
  const riskWeight = nodes.some((node) => node.waitRisk === "高") ? "高" : nodes.some((node) => node.waitRisk === "中") ? "中" : "低";
  const averageScore = Math.round(
    nodes.reduce((sum, node) => {
      const values = Object.values(node.scores);
      return sum + values.reduce((a, b) => a + b, 0) / values.length;
    }, 0) / nodes.length
  );

  return {
    totalMinutes: stayMinutes + legMinutes,
    estimatedCost: totalPrice,
    walkingDistanceKm: walkKm,
    waitRisk: riskWeight,
    score: strategy === "complete" ? Math.max(78, averageScore - 4) : averageScore,
  };
}

function makeSegments(nodes, strategy) {
  return nodes.slice(1).map((node, index) => {
    const previous = nodes[index];
    const mode = strategy === "lowWalk" && index > 0 ? "打车" : "步行";
    const minutes = mode === "打车" ? 8 : strategy === "complete" ? 16 : 12;
    return {
      from: previous.name,
      to: node.name,
      mode,
      minutes,
      note: mode === "打车" ? "减少体力消耗" : "沿湖或商圈顺路移动",
    };
  });
}

function generateRoute(constraints, strategy = "balanced") {
  const nodes = routeRecipes[strategy].map(getPoi);
  const metrics = calculatePlanMetrics(nodes, strategy);
  const meta = strategyMeta[strategy];
  const risks = [];

  if (metrics.waitRisk !== "低") risks.push("等待风险为历史热度与人工标签估计，建议出发前确认。");
  if (metrics.walkingDistanceKm > 3.2) risks.push("该方案体验更完整，但步行距离偏长。");
  if (metrics.estimatedCost > constraints.budgetPerPerson) risks.push("预计消费接近或超过当前人均预算。");
  if (constraints.timeWindow.end <= "18:00" && strategy === "complete") risks.push("18:00 前完成会略赶，建议压缩拍照停留。");
  if (risks.length === 0) risks.push("当前路线无明显闭店风险，排队信息为估计标签。");

  return {
    id: strategy,
    name: meta.label,
    strategy,
    description: meta.description,
    metrics,
    nodes,
    segments: makeSegments(nodes, strategy),
    risks,
    explanation: buildRouteExplanation(strategy, constraints, metrics),
  };
}

function buildRouteExplanation(strategy, constraints, metrics) {
  if (strategy === "lowWalk") return "该路线优先减少步行，把晚餐安排在湖滨附近，用短途打车替代长距离移动。";
  if (strategy === "lowWait") return "该路线避开高热度餐厅，把咖啡和晚餐都放在低等待风险估计的点位。";
  if (strategy === "budget") return `该路线保留西湖核心游览，把人均消费压到约${metrics.estimatedCost}元，适合预算下降时使用。`;
  if (strategy === "complete") return "该路线覆盖经典西湖、湖边步道、拍照咖啡和环境型晚餐，体验更完整但节奏更满。";
  return `该路线按${constraints.timeWindow.start}-${constraints.timeWindow.end}组织，兼顾少排队、拍照和晚餐预算。`;
}

function createPlans(constraints) {
  return Object.keys(strategyMeta).reduce((plans, strategy) => {
    plans[strategy] = generateRoute(constraints, strategy);
    return plans;
  }, {});
}

function replanRoute(plan, action, constraints) {
  const nextPlan = clone(plan);
  let diff;

  if (action === "replaceDinner") {
    const oldNode = nextPlan.nodes.find((node) => node.type === "晚餐");
    const newNode = getPoi("lowwait-restaurant");
    nextPlan.nodes = nextPlan.nodes.map((node) => (node.type === "晚餐" ? newNode : node));
    diff = {
      intent: "替换晚餐点，降低排队风险，保持路线末段稳定",
      kept: nextPlan.nodes.filter((node) => node.id !== newNode.id).map((node) => node.name),
      replaced: [{ from: oldNode.name, to: newNode.name }],
      removed: [],
      added: [],
      metricChanges: {
        cost: [oldNode.price, newNode.price],
        walk: [plan.metrics.walkingDistanceKm, Math.max(1, plan.metrics.walkingDistanceKm - 0.5)],
        wait: [oldNode.waitRisk, newNode.waitRisk],
        minutes: [plan.metrics.totalMinutes, plan.metrics.totalMinutes - 8],
      },
      reason: "原晚餐点等待风险较高或不稳定，新餐厅离湖滨更近，历史热度估计等待更低。",
    };
  }

  if (action === "removeCoffee") {
    const oldNodes = nextPlan.nodes;
    const removed = oldNodes.filter((node) => node.type === "咖啡");
    nextPlan.nodes = oldNodes.filter((node) => node.type !== "咖啡");
    diff = {
      intent: "删除咖啡节点，预算降到人均50，保留晚餐",
      kept: nextPlan.nodes.map((node) => node.name),
      replaced: [],
      removed: removed.map((node) => node.name),
      added: [],
      metricChanges: {
        cost: [plan.metrics.estimatedCost, Math.max(48, plan.metrics.estimatedCost - removed.reduce((sum, node) => sum + node.price, 0))],
        walk: [plan.metrics.walkingDistanceKm, Math.max(1, plan.metrics.walkingDistanceKm - 0.4)],
        wait: [plan.metrics.waitRisk, "中"],
        minutes: [plan.metrics.totalMinutes, plan.metrics.totalMinutes - 42],
      },
      reason: "去掉咖啡后能降低消费和停留时长，但休息与拍照体验会减少。",
    };
    nextPlan.nodes = nextPlan.nodes.map((node) => (node.type === "晚餐" ? getPoi("budget-restaurant") : node));
  }

  if (action === "shorten") {
    const removed = nextPlan.nodes.filter((node) => node.type === "散步" || node.type === "拍照点");
    nextPlan.nodes = nextPlan.nodes.filter((node) => node.type !== "散步" && node.type !== "拍照点");
    diff = {
      intent: "只剩2小时，压缩游览节点，保留一个景点和晚餐",
      kept: nextPlan.nodes.map((node) => node.name),
      replaced: [],
      removed: removed.map((node) => node.name),
      added: [],
      metricChanges: {
        cost: [plan.metrics.estimatedCost, plan.metrics.estimatedCost],
        walk: [plan.metrics.walkingDistanceKm, Math.max(1, plan.metrics.walkingDistanceKm - 1.1)],
        wait: [plan.metrics.waitRisk, plan.metrics.waitRisk],
        minutes: [plan.metrics.totalMinutes, Math.min(122, plan.metrics.totalMinutes - 48)],
      },
      reason: "压缩非必要游览点后，路线更适合现场临时变短的时间窗口。",
    };
  }

  if (action === "addPhotoCafe") {
    const newNode = getPoi("photo-cafe");
    const dinnerIndex = nextPlan.nodes.findIndex((node) => node.type === "晚餐");
    nextPlan.nodes.splice(Math.max(1, dinnerIndex), 0, newNode);
    diff = {
      intent: "加入更适合拍照的顺路咖啡点",
      kept: nextPlan.nodes.filter((node) => node.id !== newNode.id).map((node) => node.name),
      replaced: [],
      removed: [],
      added: [newNode.name],
      metricChanges: {
        cost: [plan.metrics.estimatedCost, plan.metrics.estimatedCost + newNode.price],
        walk: [plan.metrics.walkingDistanceKm, plan.metrics.walkingDistanceKm + 0.6],
        wait: [plan.metrics.waitRisk, "中"],
        minutes: [plan.metrics.totalMinutes, plan.metrics.totalMinutes + 48],
      },
      reason: "该咖啡点更匹配拍照和小众偏好，但会增加预算和路线时长。",
    };
  }

  const metrics = calculatePlanMetrics(nextPlan.nodes, nextPlan.strategy);
  nextPlan.metrics = {
    ...metrics,
    estimatedCost: diff.metricChanges.cost[1],
    walkingDistanceKm: diff.metricChanges.walk[1],
    waitRisk: diff.metricChanges.wait[1],
    totalMinutes: diff.metricChanges.minutes[1],
  };
  nextPlan.segments = makeSegments(nextPlan.nodes, nextPlan.strategy);
  nextPlan.risks = [
    "这是基于当前 Demo 数据的局部再规划结果。",
    "排队、拍照、安静等信息为估计标签，不代表实时官方数据。",
  ];
  nextPlan.explanation = diff.reason;

  return { plan: nextPlan, diff };
}

function minutesToText(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest}分钟`;
  return `${hours}小时${rest ? `${rest}分钟` : ""}`;
}

function riskClass(risk) {
  if (risk === "高") return "risk high";
  if (risk === "中") return "risk mid";
  return "risk low";
}

function scoreBars(scores) {
  const labels = {
    preference: "偏好",
    budget: "预算",
    distance: "距离",
    wait: "等待",
    hours: "时间",
  };
  return Object.entries(scores)
    .map(
      ([key, value]) => `
        <div class="score-row">
          <span>${labels[key]}</span>
          <div class="score-track"><i style="width:${value}%"></i></div>
          <b>${value}</b>
        </div>
      `
    )
    .join("");
}

function render() {
  const app = document.querySelector("#app");
  const constraints = state.constraints || parseIntent(state.input, state.quickTags);
  const selectedPlan = state.plans[state.selectedStrategy] || generateRoute(constraints, state.selectedStrategy);
  const selectedPoi = selectedPlan.nodes.find((node) => node.id === state.selectedPoiId) || selectedPlan.nodes[1] || selectedPlan.nodes[0];

  app.innerHTML = `
    <main class="workspace">
      ${renderHeader()}
      <section class="layout">
        ${renderInputPanel(constraints)}
        ${renderMapAndTimeline(selectedPlan)}
        ${renderDecisionPanel(selectedPlan, selectedPoi)}
      </section>
    </main>
  `;

  bindEvents();
}

function renderHeader() {
  return `
    <header class="topbar">
      <div>
        <p class="eyebrow">杭州西湖周边 · 现在出发</p>
        <h1>AI 本地路线决策 Agent</h1>
      </div>
      <div class="demo-note">
        <span>Demo 数据</span>
        <strong>POI 真实结构 + 排队/体验估计标签</strong>
      </div>
    </header>
  `;
}

function renderInputPanel(constraints) {
  return `
    <aside class="panel left-panel">
      <div class="section-title">
        <span>1</span>
        <div>
          <h2>输入与约束</h2>
          <p>用一句话表达当前位置、时间、预算和偏好。</p>
        </div>
      </div>
      <textarea id="intentInput" class="intent-input" rows="6">${state.input}</textarea>
      <div class="examples">
        ${examples
          .map(
            (example, index) => `
              <button class="example-button" data-example="${index}">${example}</button>
            `
          )
          .join("")}
      </div>
      <div class="quick-tags">
        ${["少排队", "少走路", "拍照好看", "本地特色", "安静"].map((tag) => {
          const active = state.quickTags.includes(tag);
          return `<button class="tag-button ${active ? "active" : ""}" data-tag="${tag}">${tag}</button>`;
        }).join("")}
      </div>
      <button class="primary-button" id="generateButton">生成可执行路线</button>

      <div class="constraint-card">
        <div class="card-head">
          <h3>已识别条件</h3>
          <span>${state.routeGenerated ? "已确认" : "待生成"}</span>
        </div>
        ${renderConstraintEditor(constraints)}
      </div>
    </aside>
  `;
}

function renderConstraintEditor(constraints) {
  return `
    <label class="field">
      <span>出发地</span>
      <input id="originInput" value="${constraints.origin}" />
    </label>
    <div class="field-grid">
      <label class="field">
        <span>开始</span>
        <input id="startInput" value="${constraints.timeWindow.start}" />
      </label>
      <label class="field">
        <span>结束</span>
        <input id="endInput" value="${constraints.timeWindow.end}" />
      </label>
    </div>
    <div class="field-grid">
      <label class="field">
        <span>预算/人</span>
        <input id="budgetInput" type="number" value="${constraints.budgetPerPerson}" />
      </label>
      <label class="field">
        <span>交通</span>
        <select id="transportInput">
          ${["步行优先", "步行 + 短途打车", "打车优先"].map((item) => `<option ${constraints.transport === item ? "selected" : ""}>${item}</option>`).join("")}
        </select>
      </label>
    </div>
    <div class="recognized-list">
      <div><b>目标</b><span>${constraints.goals.join(" / ")}</span></div>
      <div><b>人群</b><span>${constraints.companions}</span></div>
      <div><b>偏好</b><span>${constraints.preferences.join("、") || "暂无"}</span></div>
      <div><b>排队容忍</b><span>${constraints.waitTolerance}</span></div>
    </div>
  `;
}

function renderMapAndTimeline(plan) {
  return `
    <section class="center-column">
      <div class="panel map-panel">
        <div class="section-title compact">
          <span>2</span>
          <div>
            <h2>地图与路线顺序</h2>
            <p>模拟地图面板，后续可由高德地图替换。</p>
          </div>
        </div>
        ${renderMap(plan)}
      </div>
      <div class="panel timeline-panel">
        <div class="section-title compact">
          <span>3</span>
          <div>
            <h2>时间轴</h2>
            <p>${plan.explanation}</p>
          </div>
        </div>
        ${renderTimeline(plan)}
      </div>
    </section>
  `;
}

function renderMap(plan) {
  const points = plan.nodes;
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  return `
    <div class="fake-map" aria-label="西湖周边路线地图">
      <svg viewBox="0 0 100 100" role="img">
        <defs>
          <linearGradient id="lakeGradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stop-color="#a9d7d1" />
            <stop offset="100%" stop-color="#5fb3a5" />
          </linearGradient>
        </defs>
        <path class="lake" d="M42 17 C66 8 86 27 82 49 C78 76 53 88 34 76 C15 64 16 36 42 17Z" />
        <path class="district" d="M5 48 C17 40 26 41 36 52 C48 65 45 84 28 90 C15 95 6 78 5 48Z" />
        <polyline class="route-line" points="${polyline}" />
        ${points
          .map(
            (point, index) => `
              <g class="map-point ${point.id === state.selectedPoiId ? "selected" : ""}" data-poi="${point.id}">
                <circle cx="${point.x}" cy="${point.y}" r="4.4"></circle>
                <text x="${point.x}" y="${point.y + 1.3}">${index + 1}</text>
              </g>
            `
          )
          .join("")}
      </svg>
      <div class="map-labels">
        ${points
          .map(
            (point, index) => `
              <button class="map-label" data-poi="${point.id}" style="left:${Math.min(82, point.x + 2)}%; top:${Math.min(86, point.y + 2)}%">
                ${index + 1}. ${point.name}
              </button>
            `
          )
          .join("")}
      </div>
      <div class="map-legend">
        <span><i class="legend-lake"></i>西湖水域</span>
        <span><i class="legend-route"></i>推荐顺序</span>
      </div>
    </div>
  `;
}

function renderTimeline(plan) {
  let cursor = toMinutes(state.constraints?.timeWindow.start || "14:00");
  return `
    <div class="timeline">
      ${plan.nodes
        .map((node, index) => {
          const arrive = fromMinutes(cursor);
          cursor += node.stayMinutes;
          const leave = fromMinutes(cursor);
          const segment = plan.segments[index];
          if (segment) cursor += segment.minutes;
          return `
            <article class="timeline-item ${node.id === state.selectedPoiId ? "active" : ""}" data-poi="${node.id}">
              <div class="time">${arrive}<span>${leave}离开</span></div>
              <div class="timeline-body">
                <div class="timeline-head">
                  <h3>${node.name}</h3>
                  <span>${node.type}</span>
                </div>
                <p>${node.reason}</p>
                <div class="node-meta">
                  <span>停留${node.stayMinutes}分钟</span>
                  <span>人均${node.price ? `${node.price}元` : "免费"}</span>
                  <span class="${riskClass(node.waitRisk)}">等待${node.waitRisk}</span>
                </div>
                ${segment ? `<div class="segment">下一段：${segment.mode}约${segment.minutes}分钟 · ${segment.note}</div>` : ""}
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderDecisionPanel(plan, selectedPoi) {
  return `
    <aside class="panel right-panel">
      <div class="section-title">
        <span>4</span>
        <div>
          <h2>路线决策</h2>
          <p>先给默认方案，再通过策略和局部调整更新。</p>
        </div>
      </div>
      ${renderPlanSummary(plan)}
      ${renderStrategyTabs()}
      ${renderPoiInspector(selectedPoi)}
      ${renderReplanActions()}
      ${state.replanDiff ? renderDiff(state.replanDiff) : renderEmptyDiff()}
    </aside>
  `;
}

function renderPlanSummary(plan) {
  return `
    <div class="summary-card ${strategyMeta[plan.strategy].tone}">
      <div class="card-head">
        <div>
          <h3>${plan.name}</h3>
          <p>${plan.description}</p>
        </div>
        <strong>${plan.metrics.score}</strong>
      </div>
      <div class="metric-grid">
        <div><b>${minutesToText(plan.metrics.totalMinutes)}</b><span>总耗时</span></div>
        <div><b>${plan.metrics.estimatedCost}元</b><span>预计人均</span></div>
        <div><b>${plan.metrics.walkingDistanceKm.toFixed(1)}km</b><span>步行距离</span></div>
        <div><b>${plan.metrics.waitRisk}</b><span>等待风险</span></div>
      </div>
      <div class="risk-list">
        ${plan.risks.map((risk) => `<p>${risk}</p>`).join("")}
      </div>
    </div>
  `;
}

function renderStrategyTabs() {
  return `
    <div class="strategy-grid">
      ${Object.entries(strategyMeta)
        .map(
          ([key, meta]) => `
            <button class="strategy-button ${state.selectedStrategy === key ? "active" : ""}" data-strategy="${key}">
              <b>${meta.label}</b>
              <span>${meta.description}</span>
            </button>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPoiInspector(poi) {
  return `
    <div class="poi-card">
      <div class="card-head">
        <div>
          <h3>${poi.name}</h3>
          <p>${poi.address}</p>
        </div>
        <span class="${riskClass(poi.waitRisk)}">等待${poi.waitRisk}</span>
      </div>
      <div class="poi-tags">
        ${poi.tags.map((tag) => `<span>${tag}</span>`).join("")}
      </div>
      <div class="poi-details">
        <span>${poi.type}</span>
        <span>评分 ${poi.rating}</span>
        <span>人均 ${poi.price ? `${poi.price}元` : "免费"}</span>
        <span>${poi.hours}</span>
      </div>
      <p class="reason">${poi.reason}</p>
      <div class="score-list">${scoreBars(poi.scores)}</div>
      <div class="node-actions">
        <button data-action="replaceDinner">换一家餐厅</button>
        <button data-action="removeCoffee">不要咖啡</button>
      </div>
    </div>
  `;
}

function renderReplanActions() {
  return `
    <div class="replan-actions">
      <h3>快捷再规划</h3>
      <div>
        <button data-action="replaceDinner">餐厅排队太久</button>
        <button data-action="removeCoffee">预算降到50</button>
        <button data-action="shorten">只剩2小时</button>
        <button data-action="addPhotoCafe">加拍照咖啡</button>
      </div>
    </div>
  `;
}

function renderEmptyDiff() {
  return `
    <div class="diff-card muted">
      <h3>新旧方案对比</h3>
      <p>点击右侧快捷再规划后，这里会展示保留、替换、删除和指标变化。</p>
    </div>
  `;
}

function renderDiff(diff) {
  return `
    <div class="diff-card">
      <div class="card-head">
        <h3>新旧方案对比</h3>
        <span>局部再规划</span>
      </div>
      <p class="diff-intent">${diff.intent}</p>
      <div class="diff-groups">
        <div><b>保留</b><span>${diff.kept.length ? diff.kept.join("、") : "无"}</span></div>
        <div><b>替换</b><span>${diff.replaced.length ? diff.replaced.map((item) => `${item.from} → ${item.to}`).join("、") : "无"}</span></div>
        <div><b>删除</b><span>${diff.removed.length ? diff.removed.join("、") : "无"}</span></div>
        <div><b>新增</b><span>${diff.added.length ? diff.added.join("、") : "无"}</span></div>
      </div>
      <div class="change-grid">
        <div><span>人均</span><b>${diff.metricChanges.cost[0]} → ${diff.metricChanges.cost[1]}</b></div>
        <div><span>步行</span><b>${diff.metricChanges.walk[0]}km → ${diff.metricChanges.walk[1]}km</b></div>
        <div><span>等待</span><b>${diff.metricChanges.wait[0]} → ${diff.metricChanges.wait[1]}</b></div>
        <div><span>耗时</span><b>${minutesToText(diff.metricChanges.minutes[0])} → ${minutesToText(diff.metricChanges.minutes[1])}</b></div>
      </div>
      <p class="reason">${diff.reason}</p>
    </div>
  `;
}

function bindEvents() {
  document.querySelector("#intentInput")?.addEventListener("input", (event) => {
    state.input = event.target.value;
  });

  document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
      state.input = examples[Number(button.dataset.example)];
      state.constraints = parseIntent(state.input, state.quickTags);
      state.plans = createPlans(state.constraints);
      state.routeGenerated = true;
      state.replanDiff = null;
      render();
    });
  });

  document.querySelectorAll("[data-tag]").forEach((button) => {
    button.addEventListener("click", () => {
      const tag = button.dataset.tag;
      state.quickTags = state.quickTags.includes(tag)
        ? state.quickTags.filter((item) => item !== tag)
        : [...state.quickTags, tag];
      state.constraints = parseIntent(state.input, state.quickTags);
      if (state.routeGenerated) state.plans = createPlans(state.constraints);
      render();
    });
  });

  document.querySelector("#generateButton")?.addEventListener("click", () => {
    const parsed = parseIntent(state.input, state.quickTags);
    parsed.origin = document.querySelector("#originInput").value;
    parsed.timeWindow.start = document.querySelector("#startInput").value;
    parsed.timeWindow.end = document.querySelector("#endInput").value;
    parsed.budgetPerPerson = Number(document.querySelector("#budgetInput").value || parsed.budgetPerPerson);
    parsed.transport = document.querySelector("#transportInput").value;
    state.constraints = parsed;
    state.plans = createPlans(parsed);
    state.routeGenerated = true;
    state.selectedStrategy = pickDefaultStrategy(parsed);
    state.selectedPoiId = null;
    state.replanDiff = null;
    render();
  });

  document.querySelectorAll("[data-strategy]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedStrategy = button.dataset.strategy;
      state.selectedPoiId = null;
      state.replanDiff = null;
      render();
    });
  });

  document.querySelectorAll("[data-poi]").forEach((item) => {
    item.addEventListener("click", () => {
      state.selectedPoiId = item.dataset.poi;
      render();
    });
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const currentPlan = state.plans[state.selectedStrategy] || generateRoute(state.constraints, state.selectedStrategy);
      const result = replanRoute(currentPlan, button.dataset.action, state.constraints);
      state.plans[state.selectedStrategy] = result.plan;
      state.replanDiff = result.diff;
      state.selectedPoiId = result.plan.nodes.find((node) => node.type === "晚餐")?.id || result.plan.nodes[1]?.id;
      render();
    });
  });
}

function pickDefaultStrategy(constraints) {
  if (constraints.budgetPerPerson <= 60) return "budget";
  if (constraints.preferences.includes("少走路")) return "lowWalk";
  if (constraints.preferences.includes("少排队")) return "balanced";
  return "balanced";
}

function toMinutes(value) {
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

function fromMinutes(total) {
  const hours = Math.floor(total / 60) % 24;
  const minutes = total % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

state.constraints = parseIntent(state.input, state.quickTags);
state.plans = createPlans(state.constraints);
render();
