"use strict";

const examples = [
  "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
  "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，预算人均120",
];

const loadingSteps = ["正在解析需求", "正在检索西湖周边 POI", "正在计算顺路路线"];

const poiLibrary = {
  start: {
    id: "start",
    name: "湖滨银泰 in77",
    type: "起点",
    icon: "起",
    timeAction: "从湖滨银泰出发",
    address: "上城区湖滨商圈",
    open: "全天可达",
    rating: "4.7",
    price: 0,
    stay: 5,
    walkAfter: 18,
    distanceAfter: 0.9,
    x: 20,
    y: 65,
    tags: ["地铁近", "集合方便"],
    why: "作为起点交通明确，方便直接进入西湖东线。",
    image: "start",
  },
  bridge: {
    id: "bridge",
    name: "断桥残雪",
    type: "景点",
    icon: "景",
    timeAction: "到断桥，看湖景和拍照",
    address: "西湖区北山街",
    open: "全天开放",
    rating: "4.6",
    price: 0,
    stay: 35,
    walkAfter: 12,
    distanceAfter: 0.7,
    x: 44,
    y: 36,
    tags: ["西湖经典", "免费", "拍照友好"],
    why: "从湖滨过去顺路，能最快进入西湖游玩状态。",
    image: "bridge",
  },
  cafe: {
    id: "cafe",
    name: "湖畔白塔咖啡",
    type: "咖啡",
    icon: "咖",
    timeAction: "步行去咖啡店，休息一会儿",
    address: "湖滨路附近",
    open: "10:00-21:30",
    rating: "4.5",
    price: 42,
    stay: 35,
    walkAfter: 14,
    distanceAfter: 0.8,
    x: 51,
    y: 58,
    tags: ["安静", "预算内", "低等待"],
    why: "放在中段休息，不打断游览节奏，也给晚饭前留缓冲。",
    image: "cafe",
  },
  dinner: {
    id: "dinner",
    name: "新白鹿餐厅湖滨店",
    type: "晚餐",
    icon: "餐",
    timeAction: "回到湖滨附近吃晚饭",
    address: "上城区延安路附近",
    open: "10:30-21:30",
    rating: "4.4",
    price: 78,
    stay: 55,
    walkAfter: 0,
    distanceAfter: 0,
    x: 27,
    y: 74,
    tags: ["杭帮菜", "预算友好", "适合多人"],
    why: "人均在预算内，离湖滨近，结束后打车或地铁都方便。",
    image: "dinner",
  },
  lowWaitDinner: {
    id: "lowWaitDinner",
    name: "弄堂里湖滨店",
    type: "晚餐",
    icon: "餐",
    timeAction: "换到低等待餐厅吃晚饭",
    address: "上城区平海路附近",
    open: "11:00-21:00",
    rating: "4.3",
    price: 88,
    stay: 55,
    walkAfter: 0,
    distanceAfter: 0,
    x: 32,
    y: 70,
    tags: ["杭帮菜", "低等待", "离湖滨近"],
    why: "当餐厅排队太久时，优先换晚餐节点，保留其他路线不变。",
    image: "dinner2",
  },
  budgetDinner: {
    id: "budgetDinner",
    name: "知味观仁和路店",
    type: "晚餐",
    icon: "餐",
    timeAction: "吃一顿低预算本地晚饭",
    address: "上城区仁和路",
    open: "07:00-21:00",
    rating: "4.2",
    price: 48,
    stay: 45,
    walkAfter: 0,
    distanceAfter: 0,
    x: 24,
    y: 68,
    tags: ["本地特色", "低预算", "游客友好"],
    why: "预算下降时仍保留本地特色晚餐，消费更可控。",
    image: "budget",
  },
};

const state = {
  status: "input",
  input: examples[0],
  preferences: ["少排队", "拍照好看"],
  loadingStep: 0,
  selectedPoiId: "bridge",
  routeData: null,
  diff: null,
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function getPoi(id) {
  return clone(poiLibrary[id]);
}

function parseConstraints(text, preferences) {
  const budgetMatch = text.match(/人均\s*(\d+)|预算.*?(\d+)/);
  const timeMatch = text.match(/(\d{1,2})\s*点.*?(\d{1,2})\s*点/);
  const chips = [
    { id: "origin", label: text.includes("湖滨银泰") ? "湖滨银泰出发" : "西湖湖滨出发", editable: false },
    { id: "time", label: timeMatch ? `${timeMatch[1]}:00-${timeMatch[2]}:00` : "14:00-18:00", editable: true },
    { id: "budget", label: `人均${budgetMatch ? budgetMatch[1] || budgetMatch[2] : 150}元`, editable: true },
    { id: "wait", label: /不想排队|少排队/.test(text) || preferences.includes("少排队") ? "少排队" : "可短时等待", editable: true },
    ...preferences.map((item) => ({ id: `pref-${item}`, label: item, editable: true })),
  ];

  return {
    origin: chips[0].label,
    timeRange: chips[1].label,
    budget: budgetMatch ? Number(budgetMatch[1] || budgetMatch[2]) : 150,
    preferences,
    chips: dedupeChips(chips),
  };
}

function dedupeChips(chips) {
  const seen = new Set();
  return chips.filter((chip) => {
    if (seen.has(chip.label)) return false;
    seen.add(chip.label);
    return true;
  });
}

function createRoute(constraints, nodes = [getPoi("start"), getPoi("bridge"), getPoi("cafe"), getPoi("dinner")], diff = null) {
  const totalStay = nodes.reduce((sum, node) => sum + node.stay, 0);
  const totalWalk = nodes.reduce((sum, node) => sum + node.walkAfter, 0);
  const distance = nodes.reduce((sum, node) => sum + node.distanceAfter, 0);
  const cost = nodes.reduce((sum, node) => sum + node.price, 0);
  const waitRisk = nodes.some((node) => node.tags.includes("低等待")) ? "低-中" : "中";

  return {
    title: cost <= 60 ? "低预算湖滨线" : waitRisk === "低-中" ? "轻松西湖半日线" : "轻松西湖半日线",
    summary: "先看西湖经典景，再留出咖啡休息，最后回到湖滨附近吃晚饭。",
    constraints,
    nodes,
    metrics: {
      minutes: totalStay + totalWalk,
      cost,
      distance: Number(distance.toFixed(1)),
      waitRisk,
    },
    transport: buildTransport(nodes),
    diff,
  };
}

function buildTransport(nodes) {
  return nodes.slice(0, -1).map((node, index) => ({
    from: node.name,
    to: nodes[index + 1].name,
    mode: "步行",
    minutes: node.walkAfter,
    distance: node.distanceAfter,
  }));
}

function generateRouteWithLoading() {
  state.status = "loading";
  state.loadingStep = 0;
  state.diff = null;
  render();

  loadingSteps.forEach((_, index) => {
    window.setTimeout(() => {
      state.loadingStep = index;
      render();
    }, index * 650);
  });

  window.setTimeout(() => {
    const constraints = parseConstraints(state.input, state.preferences);
    state.routeData = createRoute(constraints);
    state.selectedPoiId = "bridge";
    state.status = "result";
    render();
  }, loadingSteps.length * 650 + 300);
}

function applyScenario(action) {
  if (!state.routeData) return;
  const previous = clone(state.routeData);
  let nodes = clone(state.routeData.nodes);
  let diff;

  if (action === "queue") {
    nodes = nodes.map((node) => (node.id === "dinner" ? getPoi("lowWaitDinner") : node));
    diff = makeDiff(previous, nodes, {
      title: "已替换晚餐点",
      changed: "新白鹿餐厅湖滨店 → 弄堂里湖滨店",
      reason: "只替换晚餐节点，保留景点和咖啡，降低等待风险。",
    });
    state.selectedPoiId = "lowWaitDinner";
  }

  if (action === "budget100") {
    nodes = nodes.map((node) => (node.type === "晚餐" ? getPoi("budgetDinner") : node));
    diff = makeDiff(previous, nodes, {
      title: "已把晚餐换成更低预算选择",
      changed: "晚餐改为知味观仁和路店",
      reason: "保留咖啡和西湖游览，同时把晚餐消费压低。",
    });
    state.selectedPoiId = "budgetDinner";
  }

  if (action === "noCoffee") {
    nodes = nodes.filter((node) => node.type !== "咖啡");
    diff = makeDiff(previous, nodes, {
      title: "已删除咖啡节点",
      changed: "湖畔白塔咖啡已移除",
      reason: "减少停留时间和预算，但中途休息体验会变弱。",
    });
    state.selectedPoiId = nodes[1]?.id || nodes[0]?.id;
  }

  if (action === "short") {
    nodes = nodes.filter((node) => node.type !== "咖啡");
    nodes = nodes.map((node) => (node.type === "晚餐" ? { ...node, stay: 40 } : node));
    diff = makeDiff(previous, nodes, {
      title: "已压缩为2小时版本",
      changed: "删除咖啡节点，压缩晚餐停留",
      reason: "优先保留一个景点和晚餐，减少中途停留。",
    });
    state.selectedPoiId = nodes[1]?.id || nodes[0]?.id;
  }

  state.routeData = createRoute(state.routeData.constraints, nodes, diff);
  render();
}

function makeDiff(previous, nextNodes, copy) {
  const next = createRoute(previous.constraints, nextNodes);
  const prevNames = previous.nodes.map((node) => node.name);
  const nextNames = nextNodes.map((node) => node.name);
  const kept = nextNames.filter((name) => prevNames.includes(name));
  const removed = prevNames.filter((name) => !nextNames.includes(name));
  const added = nextNames.filter((name) => !prevNames.includes(name));

  return {
    ...copy,
    kept,
    removed,
    added,
    delta: {
      minutes: [previous.metrics.minutes, next.metrics.minutes],
      cost: [previous.metrics.cost, next.metrics.cost],
      distance: [previous.metrics.distance, next.metrics.distance],
      waitRisk: [previous.metrics.waitRisk, next.metrics.waitRisk],
    },
  };
}

function deleteNode(id) {
  if (!state.routeData || id === "start") return;
  const previous = clone(state.routeData);
  const nodes = state.routeData.nodes.filter((node) => node.id !== id);
  const removed = previous.nodes.find((node) => node.id === id);
  const diff = makeDiff(previous, nodes, {
    title: "已移除一个目的地",
    changed: `${removed?.name || "该节点"} 已移除`,
    reason: "系统保留其余节点，并重新计算总耗时、预算和步行距离。",
  });
  state.routeData = createRoute(state.routeData.constraints, nodes, diff);
  state.selectedPoiId = nodes[1]?.id || nodes[0]?.id;
  render();
}

function replaceNode(id) {
  if (!state.routeData) return;
  if (id === "dinner" || id === "lowWaitDinner") applyScenario("queue");
  if (id === "cafe") applyScenario("noCoffee");
}

function moveNode(id, direction) {
  if (!state.routeData) return;
  const index = state.routeData.nodes.findIndex((node) => node.id === id);
  const target = index + direction;
  if (index <= 0 || target <= 0 || target >= state.routeData.nodes.length) return;

  const previous = clone(state.routeData);
  const nodes = clone(state.routeData.nodes);
  const [item] = nodes.splice(index, 1);
  nodes.splice(target, 0, item);
  const diff = makeDiff(previous, nodes, {
    title: "已调整目的地顺序",
    changed: `${item.name} 顺序已调整`,
    reason: "当前按新的节点顺序重新计算路线指标。",
  });
  state.routeData = createRoute(state.routeData.constraints, nodes, diff);
  state.selectedPoiId = id;
  render();
}

function editChip(id) {
  if (!state.routeData) return;
  if (id === "budget") {
    state.routeData.constraints.budget = 100;
    state.routeData.constraints.chips = state.routeData.constraints.chips.map((chip) => chip.id === "budget" ? { ...chip, label: "人均100元" } : chip);
    applyScenario("budget100");
  }
  if (id === "time") applyScenario("short");
  if (id === "wait") applyScenario("queue");
}

function render() {
  const app = document.querySelector("#app");
  app.innerHTML = `
    <main class="app-shell ${state.status}">
      ${state.status === "input" ? renderInputState() : ""}
      ${state.status === "loading" ? renderLoadingState() : ""}
      ${state.status === "result" ? renderResultState() : ""}
    </main>
  `;
  bindEvents();
}

function renderInputState() {
  return `
    <section class="input-state">
      <div class="brand-pill">杭州西湖周边 · 现在出发</div>
      <h1>说出你想怎么玩，我帮你排成一条能直接走的路线。</h1>
      <p class="subhead">适合现场临时决定：景点、咖啡、晚饭、预算、少排队，都可以一句话说完。</p>
      ${renderInputBox()}
    </section>
  `;
}

function renderInputBox() {
  return `
    <section class="input-card">
      <div class="input-row">
        <button class="mic-button" aria-label="语音输入">🎙</button>
        <textarea id="intentInput" rows="4">${state.input}</textarea>
      </div>
      <div class="example-row">
        ${examples.map((example, index) => `<button data-example="${index}">${example}</button>`).join("")}
      </div>
      <div class="preference-row">
        <span>偏好</span>
        ${["少排队", "少走路", "拍照好看", "本地特色"].map((item) => `
          <button class="${state.preferences.includes(item) ? "active" : ""}" data-preference="${item}">${item}</button>
        `).join("")}
      </div>
      <button class="primary-button" id="generateButton">生成路线</button>
    </section>
  `;
}

function renderLoadingState() {
  return `
    <section class="loading-state">
      <div class="loading-card">
        <div class="loader"></div>
        <h2>${loadingSteps[state.loadingStep]}</h2>
        <div class="loading-steps">
          ${loadingSteps.map((step, index) => `
            <div class="${index <= state.loadingStep ? "done" : ""}">
              <i>${index + 1}</i><span>${step}</span>
            </div>
          `).join("")}
        </div>
      </div>
    </section>
  `;
}

function renderResultState() {
  const route = state.routeData;
  return `
    <section class="result-state">
      ${renderTopBar(route)}
      ${renderRouteSummary(route)}
      ${renderTransport(route)}
      ${renderMap(route)}
      ${renderTimeline(route)}
      ${renderPoiCards(route)}
      ${renderAdjustments(route)}
      <footer>说明：当前为前端样例数据，排队、热度、体验标签为演示用估计；后续可替换为真实 POI、路线计算和大模型解析。</footer>
    </section>
  `;
}

function renderTopBar(route) {
  return `
    <header class="top-bar">
      <button class="back-button" id="backButton">重新输入</button>
      <div class="chips">
        ${route.constraints.chips.map((chip) => `
          <button class="${chip.editable ? "editable" : ""}" data-chip="${chip.id}">${chip.label}</button>
        `).join("")}
      </div>
    </header>
  `;
}

function renderRouteSummary(route) {
  return `
    <section class="route-card">
      <span class="route-label">当前推荐</span>
      <h2>${route.title}</h2>
      <p>${route.summary}</p>
      <div class="metrics">
        <div><b>${formatMinutes(route.metrics.minutes)}</b><span>总耗时</span></div>
        <div><b>${route.metrics.cost}元</b><span>人均</span></div>
        <div><b>${route.metrics.distance}km</b><span>步行</span></div>
        <div><b>${route.metrics.waitRisk}</b><span>等待</span></div>
      </div>
      <button class="primary-button">按这条走</button>
    </section>
  `;
}

function renderTransport(route) {
  return `
    <section class="transport-card">
      <h3>交通方案摘要</h3>
      <div class="transport-list">
        ${route.transport.map((leg) => `
          <div>
            <b>${leg.mode} ${leg.minutes}分钟</b>
            <span>${leg.from} → ${leg.to}</span>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function renderMap(route) {
  const points = route.nodes.map((node, index) => ({ ...node, index: index + 1 }));
  return `
    <section class="map-card">
      <h3>路线地图</h3>
      <div class="map">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
          <path class="lake" d="M38 6 C68 0 91 22 88 52 C85 82 55 98 29 82 C8 68 9 20 38 6Z"></path>
          <path class="park" d="M8 42 C26 31 40 39 43 56 C47 76 31 88 16 80 C4 72 0 53 8 42Z"></path>
          <path class="road main" d="M5 70 C26 60 42 63 58 72 C72 79 84 78 96 70"></path>
          <path class="road" d="M19 19 C35 31 49 34 68 28 C80 24 88 32 94 45"></path>
          <polyline class="route-line" points="${points.map((point) => `${point.x},${point.y}`).join(" ")}"></polyline>
        </svg>
        <span class="lake-text">西湖</span>
        ${points.map((point) => `
          <button class="marker ${state.selectedPoiId === point.id ? "active" : ""}" style="left:${point.x}%;top:${point.y}%;" data-poi="${point.id}">
            <i>${point.index}</i><span>${point.name}</span>
          </button>
        `).join("")}
      </div>
    </section>
  `;
}

function renderTimeline(route) {
  let cursor = 14 * 60;
  return `
    <section class="timeline-card">
      <h3>今天怎么走</h3>
      <div class="timeline">
        ${route.nodes.map((node, index) => {
          const start = formatClock(cursor);
          cursor += node.stay;
          const nextLeg = route.transport[index];
          if (nextLeg) cursor += nextLeg.minutes;
          return `
            <button class="timeline-item ${state.selectedPoiId === node.id ? "active" : ""}" data-poi="${node.id}">
              <time>${start}</time>
              <div><b>${node.timeAction}</b><span>${node.stay}分钟 · ${node.name}</span></div>
            </button>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderPoiCards(route) {
  return `
    <section class="poi-section">
      <h3>目的地卡片</h3>
      <div class="poi-scroll">
        ${route.nodes.map((node, index) => `
          <article class="poi-card ${state.selectedPoiId === node.id ? "active" : ""}" data-poi="${node.id}">
            <div class="poi-image ${node.image}"><span>${node.icon}</span></div>
            <h4>${node.name}</h4>
            <p>${node.address}</p>
            <div class="facts"><span>${node.open}</span><span>评分 ${node.rating}</span><span>${node.price ? `${node.price}元` : "免费"}</span></div>
            <div class="tags">${node.tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
            <div class="why"><b>为什么推荐</b><p>${node.why}</p></div>
            <div class="actions">
              <button data-replace="${node.id}">替换</button>
              <button data-delete="${node.id}" ${node.id === "start" ? "disabled" : ""}>删除</button>
              <button data-move="${node.id}" data-dir="-1" ${index <= 1 ? "disabled" : ""}>上移</button>
              <button data-move="${node.id}" data-dir="1" ${index === 0 || index === route.nodes.length - 1 ? "disabled" : ""}>下移</button>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderAdjustments(route) {
  return `
    <section class="adjust-card">
      <h3>快速调整</h3>
      <div class="quick-buttons">
        <button data-action="queue">餐厅排队太久</button>
        <button data-action="budget100">预算降到 100</button>
        <button data-action="noCoffee">不要咖啡</button>
        <button data-action="short">只剩 2 小时</button>
      </div>
      ${route.diff ? renderDiff(route.diff) : `<p class="adjust-hint">点击任一情况，系统会只调整相关节点并展示变化。</p>`}
    </section>
  `;
}

function renderDiff(diff) {
  return `
    <div class="diff">
      <strong>${diff.title}</strong>
      <p>${diff.reason}</p>
      <div class="changed">${diff.changed}</div>
      <div class="diff-grid">
        <div><span>耗时</span><b>${formatMinutes(diff.delta.minutes[0])} → ${formatMinutes(diff.delta.minutes[1])}</b></div>
        <div><span>预算</span><b>${diff.delta.cost[0]} → ${diff.delta.cost[1]}元</b></div>
        <div><span>步行</span><b>${diff.delta.distance[0]} → ${diff.delta.distance[1]}km</b></div>
        <div><span>等待</span><b>${diff.delta.waitRisk[0]} → ${diff.delta.waitRisk[1]}</b></div>
      </div>
      <p class="kept">保留：${diff.kept.join("、") || "无"}</p>
      ${diff.removed.length ? `<p class="kept">删除：${diff.removed.join("、")}</p>` : ""}
      ${diff.added.length ? `<p class="kept">新增：${diff.added.join("、")}</p>` : ""}
    </div>
  `;
}

function bindEvents() {
  document.querySelector("#intentInput")?.addEventListener("input", (event) => {
    state.input = event.target.value;
  });

  document.querySelector("#generateButton")?.addEventListener("click", generateRouteWithLoading);
  document.querySelector("#backButton")?.addEventListener("click", () => {
    state.status = "input";
    render();
  });

  document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
      state.input = examples[Number(button.dataset.example)];
      render();
    });
  });

  document.querySelectorAll("[data-preference]").forEach((button) => {
    button.addEventListener("click", () => {
      const value = button.dataset.preference;
      state.preferences = state.preferences.includes(value)
        ? state.preferences.filter((item) => item !== value)
        : [...state.preferences, value];
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
    button.addEventListener("click", () => applyScenario(button.dataset.action));
  });

  document.querySelectorAll("[data-delete]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteNode(button.dataset.delete);
    });
  });

  document.querySelectorAll("[data-replace]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      replaceNode(button.dataset.replace);
    });
  });

  document.querySelectorAll("[data-move]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      moveNode(button.dataset.move, Number(button.dataset.dir));
    });
  });

  document.querySelectorAll("[data-chip]").forEach((chip) => {
    chip.addEventListener("click", () => editChip(chip.dataset.chip));
  });
}

function formatMinutes(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours ? `${hours}小时${rest ? `${rest}分` : ""}` : `${rest}分`;
}

function formatClock(total) {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

render();
