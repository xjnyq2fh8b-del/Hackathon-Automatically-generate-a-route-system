"use client";

import { useMemo, useState } from "react";

type AppStatus = "idle" | "loading" | "result";
type WaitRisk = "低" | "中" | "高";
type PoiType = "起点" | "景点" | "咖啡" | "晚餐";

type ConstraintChip = {
  id: "origin" | "time" | "budget" | "wait" | "people" | "preference";
  label: string;
  editable: boolean;
};

type PoiNode = {
  id: string;
  name: string;
  type: PoiType;
  icon: string;
  action: string;
  address: string;
  openTime: string;
  rating: string;
  price: number;
  stayMinutes: number;
  walkAfterMinutes: number;
  distanceAfterKm: number;
  mapX: number;
  mapY: number;
  tags: string[];
  reason: string;
  imageTone: string;
};

type RouteMetrics = {
  totalMinutes: number;
  costPerPerson: number;
  walkKm: number;
  waitRisk: WaitRisk;
};

type TransportLeg = {
  from: string;
  to: string;
  mode: "步行" | "打车";
  minutes: number;
  distanceKm: number;
  action: string;
};

type RouteDiff = {
  title: string;
  reason: string;
  changed: string;
  kept: string[];
  removed: string[];
  added: string[];
  before: RouteMetrics;
  after: RouteMetrics;
};

type RouteData = {
  title: string;
  summary: string;
  chips: ConstraintChip[];
  nodes: PoiNode[];
  transport: TransportLeg[];
  metrics: RouteMetrics;
  diff: RouteDiff | null;
};

const examples = [
  "我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队",
  "带老人和小孩看西湖，不想走太多路，晚饭吃杭帮菜，人均120",
];

const loadingSteps = ["正在解析需求", "正在检索西湖周边 POI", "正在计算顺路路线"];

const preferenceOptions = ["少排队", "少走路", "拍照好看", "本地特色"];

const poiLibrary: Record<string, PoiNode> = {
  start: {
    id: "start",
    name: "湖滨银泰 in77",
    type: "起点",
    icon: "起",
    action: "从湖滨银泰出发",
    address: "上城区湖滨商圈",
    openTime: "全天可达",
    rating: "4.7",
    price: 0,
    stayMinutes: 5,
    walkAfterMinutes: 16,
    distanceAfterKm: 0.8,
    mapX: 20,
    mapY: 66,
    tags: ["地铁近", "集合方便"],
    reason: "起点交通明确，适合把路线从湖滨一侧顺着西湖展开。",
    imageTone: "from-stone-200 to-emerald-100",
  },
  bridge: {
    id: "bridge",
    name: "断桥残雪",
    type: "景点",
    icon: "景",
    action: "到断桥看湖景和拍照",
    address: "西湖区北山街",
    openTime: "全天开放",
    rating: "4.6",
    price: 0,
    stayMinutes: 35,
    walkAfterMinutes: 12,
    distanceAfterKm: 0.7,
    mapX: 44,
    mapY: 34,
    tags: ["西湖经典", "免费", "拍照友好"],
    reason: "从湖滨过去顺路，能最快进入西湖游览状态。",
    imageTone: "from-cyan-100 to-emerald-200",
  },
  cafe: {
    id: "cafe",
    name: "湖畔白塔咖啡",
    type: "咖啡",
    icon: "咖",
    action: "步行去咖啡店休息",
    address: "湖滨路附近",
    openTime: "10:00-21:30",
    rating: "4.5",
    price: 42,
    stayMinutes: 35,
    walkAfterMinutes: 14,
    distanceAfterKm: 0.8,
    mapX: 52,
    mapY: 57,
    tags: ["安静", "预算内", "低等待"],
    reason: "放在中段休息，不打断游览节奏，也给晚饭前留缓冲。",
    imageTone: "from-sky-100 to-orange-100",
  },
  dinner: {
    id: "dinner",
    name: "新白鹿餐厅湖滨店",
    type: "晚餐",
    icon: "餐",
    action: "回到湖滨附近吃晚饭",
    address: "上城区延安路附近",
    openTime: "10:30-21:30",
    rating: "4.4",
    price: 78,
    stayMinutes: 55,
    walkAfterMinutes: 0,
    distanceAfterKm: 0,
    mapX: 27,
    mapY: 75,
    tags: ["杭帮菜", "预算友好", "多人适合"],
    reason: "人均在预算内，离湖滨近，结束后打车或地铁都方便。",
    imageTone: "from-orange-100 to-lime-100",
  },
  lowWaitDinner: {
    id: "lowWaitDinner",
    name: "弄堂里湖滨店",
    type: "晚餐",
    icon: "餐",
    action: "换到等待更低的餐厅吃晚饭",
    address: "上城区平海路附近",
    openTime: "11:00-21:00",
    rating: "4.3",
    price: 88,
    stayMinutes: 55,
    walkAfterMinutes: 0,
    distanceAfterKm: 0,
    mapX: 32,
    mapY: 70,
    tags: ["杭帮菜", "低等待", "离湖滨近"],
    reason: "只替换晚餐节点，保留景点和咖啡，降低等待不确定性。",
    imageTone: "from-lime-100 to-orange-100",
  },
  budgetDinner: {
    id: "budgetDinner",
    name: "知味观仁和路店",
    type: "晚餐",
    icon: "餐",
    action: "吃一顿更低预算的本地晚饭",
    address: "上城区仁和路",
    openTime: "07:00-21:00",
    rating: "4.2",
    price: 48,
    stayMinutes: 45,
    walkAfterMinutes: 0,
    distanceAfterKm: 0,
    mapX: 24,
    mapY: 68,
    tags: ["本地特色", "低预算", "游客友好"],
    reason: "预算下降时仍保留本地特色晚餐，整体花费更可控。",
    imageTone: "from-amber-100 to-emerald-100",
  },
};

function clonePoi(id: string) {
  return { ...poiLibrary[id], tags: [...poiLibrary[id].tags] };
}

function buildChips(input: string, preferences: string[]): ConstraintChip[] {
  const budgetMatch = input.match(/人均\s*(\d+)|预算.*?(\d+)/);
  const timeMatch = input.match(/(\d{1,2})\s*点.*?(\d{1,2})\s*点/);
  const hasFamily = /老人|小孩|孩子|亲子/.test(input);
  const waitLabel = /不想排队|少排队/.test(input) || preferences.includes("少排队") ? "少排队" : "可短时等待";

  const chips: ConstraintChip[] = [
    { id: "origin", label: input.includes("湖滨银泰") ? "湖滨银泰出发" : "湖滨出发", editable: false },
    { id: "time", label: timeMatch ? `${timeMatch[1]}:00-${timeMatch[2]}:00` : "14:00-18:00", editable: true },
    { id: "budget", label: `人均${budgetMatch?.[1] || budgetMatch?.[2] || "150"}元`, editable: true },
    { id: "wait", label: waitLabel, editable: true },
  ];

  if (hasFamily) chips.push({ id: "people", label: "带老人小孩", editable: true });
  preferences.forEach((item) => chips.push({ id: "preference", label: item, editable: true }));

  const seen = new Set<string>();
  return chips.filter((chip) => {
    if (seen.has(chip.label)) return false;
    seen.add(chip.label);
    return true;
  });
}

function buildTransport(nodes: PoiNode[]): TransportLeg[] {
  return nodes.slice(0, -1).map((node, index) => {
    const next = nodes[index + 1];
    return {
      from: node.name,
      to: next.name,
      mode: node.walkAfterMinutes > 18 ? "打车" : "步行",
      minutes: node.walkAfterMinutes,
      distanceKm: node.distanceAfterKm,
      action: `${node.name} 到 ${next.name}`,
    };
  });
}

function calculateMetrics(nodes: PoiNode[]): RouteMetrics {
  const totalMinutes = nodes.reduce((sum, node) => sum + node.stayMinutes + node.walkAfterMinutes, 0);
  const costPerPerson = nodes.reduce((sum, node) => sum + node.price, 0);
  const walkKm = Number(nodes.reduce((sum, node) => sum + node.distanceAfterKm, 0).toFixed(1));
  const hasLowWait = nodes.some((node) => node.tags.includes("低等待"));
  const hasDinner = nodes.some((node) => node.type === "晚餐");

  return {
    totalMinutes,
    costPerPerson,
    walkKm,
    waitRisk: hasLowWait && hasDinner ? "低" : "中",
  };
}

function createRoute(input: string, preferences: string[], nodes = [clonePoi("start"), clonePoi("bridge"), clonePoi("cafe"), clonePoi("dinner")], diff: RouteDiff | null = null): RouteData {
  const metrics = calculateMetrics(nodes);
  return {
    title: metrics.costPerPerson <= 90 ? "低预算湖滨线" : "轻松西湖半日线",
    summary: "这条路线适合下午轻松逛西湖：先看景，再喝咖啡休息，最后顺路回湖滨吃晚饭。",
    chips: buildChips(input, preferences),
    nodes,
    transport: buildTransport(nodes),
    metrics,
    diff,
  };
}

function makeDiff(beforeRoute: RouteData, nextNodes: PoiNode[], copy: Pick<RouteDiff, "title" | "reason" | "changed">): RouteDiff {
  const beforeNames = beforeRoute.nodes.map((node) => node.name);
  const afterNames = nextNodes.map((node) => node.name);

  return {
    ...copy,
    kept: afterNames.filter((name) => beforeNames.includes(name)),
    removed: beforeNames.filter((name) => !afterNames.includes(name)),
    added: afterNames.filter((name) => !beforeNames.includes(name)),
    before: beforeRoute.metrics,
    after: calculateMetrics(nextNodes),
  };
}

function formatMinutes(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest}分钟`;
  return rest ? `${hours}小时${rest}分钟` : `${hours}小时`;
}

function formatClock(totalMinutes: number) {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

export default function Page() {
  const [status, setStatus] = useState<AppStatus>("idle");
  const [input, setInput] = useState(examples[0]);
  const [preferences, setPreferences] = useState(["少排队", "拍照好看"]);
  const [loadingStep, setLoadingStep] = useState(0);
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [selectedPoiId, setSelectedPoiId] = useState("bridge");
  const [isListening, setIsListening] = useState(false);

  const selectedPoi = useMemo(() => routeData?.nodes.find((node) => node.id === selectedPoiId), [routeData, selectedPoiId]);

  function generateWithLoading(nextInput = input, nextPreferences = preferences) {
    setStatus("loading");
    setLoadingStep(0);

    loadingSteps.forEach((_, index) => {
      window.setTimeout(() => setLoadingStep(index), index * 650);
    });

    window.setTimeout(() => {
      const route = createRoute(nextInput, nextPreferences);
      setRouteData(route);
      setSelectedPoiId("bridge");
      setStatus("result");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, loadingSteps.length * 650 + 300);
  }

  function simulateVoiceInput() {
    setIsListening(true);
    window.setTimeout(() => {
      setInput("我在湖滨银泰，下午2点到6点，想逛西湖、喝咖啡、吃晚饭，人均150，不想排队，最好拍照好看");
      setPreferences(["少排队", "拍照好看"]);
      setIsListening(false);
    }, 950);
  }

  function updateRoute(nextNodes: PoiNode[], diff: RouteDiff, nextSelectedId?: string) {
    if (!routeData) return;
    const nextRoute = createRoute(input, preferences, nextNodes, diff);
    setRouteData(nextRoute);
    setSelectedPoiId(nextSelectedId || nextNodes[1]?.id || nextNodes[0]?.id || "");
  }

  function applyScenario(action: "queue" | "budget100" | "noCoffee" | "short") {
    if (!routeData) return;
    let nodes = routeData.nodes.map((node) => ({ ...node, tags: [...node.tags] }));
    let selected = selectedPoiId;
    let diffCopy: Pick<RouteDiff, "title" | "reason" | "changed">;

    if (action === "queue") {
      nodes = nodes.map((node) => (node.type === "晚餐" ? clonePoi("lowWaitDinner") : node));
      selected = "lowWaitDinner";
      diffCopy = {
        title: "已替换晚餐点",
        changed: "新白鹿餐厅湖滨店 → 弄堂里湖滨店",
        reason: "只替换晚餐节点，景点和咖啡不动，优先降低排队不确定性。",
      };
    } else if (action === "budget100") {
      nodes = nodes.map((node) => (node.type === "晚餐" ? clonePoi("budgetDinner") : node));
      selected = "budgetDinner";
      diffCopy = {
        title: "已换成更低预算晚餐",
        changed: "晚餐改为知味观仁和路店",
        reason: "保留西湖游览和咖啡休息，把晚餐人均压低，整体预算更稳。",
      };
    } else if (action === "noCoffee") {
      nodes = nodes.filter((node) => node.type !== "咖啡");
      selected = nodes[1]?.id || nodes[0]?.id || "";
      diffCopy = {
        title: "已删除咖啡节点",
        changed: "湖畔白塔咖啡已移除",
        reason: "减少停留时间和消费，但中途休息感会变弱。",
      };
    } else {
      nodes = nodes
        .filter((node) => node.type !== "咖啡")
        .map((node) => (node.type === "晚餐" ? { ...node, stayMinutes: 40 } : node));
      selected = nodes[1]?.id || nodes[0]?.id || "";
      diffCopy = {
        title: "已压缩为 2 小时版本",
        changed: "删除咖啡节点，缩短晚餐停留",
        reason: "优先保留一个代表性景点和晚餐，减少中途停留。",
      };
    }

    updateRoute(nodes, makeDiff(routeData, nodes, diffCopy), selected);
  }

  function deleteNode(id: string) {
    if (!routeData || id === "start") return;
    const removed = routeData.nodes.find((node) => node.id === id);
    const nodes = routeData.nodes.filter((node) => node.id !== id);
    updateRoute(
      nodes,
      makeDiff(routeData, nodes, {
        title: "已删除一个目的地",
        changed: `${removed?.name || "该目的地"} 已移除`,
        reason: "保留其余节点，并重新计算总耗时、预算和步行距离。",
      }),
    );
  }

  function replaceNode(id: string) {
    if (!routeData) return;
    const target = routeData.nodes.find((node) => node.id === id);
    if (target?.type === "晚餐") applyScenario("queue");
    if (target?.type === "咖啡") applyScenario("noCoffee");
  }

  function moveNode(id: string, direction: -1 | 1) {
    if (!routeData) return;
    const index = routeData.nodes.findIndex((node) => node.id === id);
    const target = index + direction;
    if (index <= 0 || target <= 0 || target >= routeData.nodes.length) return;

    const nodes = routeData.nodes.map((node) => ({ ...node, tags: [...node.tags] }));
    const [item] = nodes.splice(index, 1);
    nodes.splice(target, 0, item);

    updateRoute(
      nodes,
      makeDiff(routeData, nodes, {
        title: "已调整目的地顺序",
        changed: `${item.name} 顺序已调整`,
        reason: "按新的访问顺序重新计算路线指标，用来演示顺路重排效果。",
      }),
      id,
    );
  }

  function editChip(chip: ConstraintChip) {
    if (!chip.editable) return;
    if (chip.id === "budget") applyScenario("budget100");
    if (chip.id === "time") applyScenario("short");
    if (chip.id === "wait") applyScenario("queue");
  }

  return (
    <main className="min-h-screen bg-[#f6efe4] text-[#20201d]">
      {status === "idle" && (
        <section className="mx-auto flex min-h-screen w-full max-w-[520px] flex-col justify-center px-5 py-8">
          <div className="mb-5 w-fit rounded-full bg-[#e5f3ed] px-3 py-2 text-sm font-bold text-[#2f6f62]">杭州西湖周边 · 现在就出发</div>
          <h1 className="text-[34px] font-black leading-[1.12] tracking-normal">说出你想怎么逛，我帮你排成一条能直接走的路线。</h1>
          <p className="mt-4 text-[15px] leading-7 text-[#746d64]">景点、咖啡、晚饭、预算、少排队，都可以一句话说完。</p>

          <section className="mt-6 rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)]">
            <div className="grid grid-cols-[52px_1fr] gap-3">
              <button
                className={`grid h-[52px] place-items-center rounded-2xl border-0 ${isListening ? "bg-[#e76f2c] text-white" : "bg-[#e5f3ed] text-[#2f6f62]"}`}
                type="button"
                aria-label="语音输入"
                onClick={simulateVoiceInput}
              >
                <span className="relative h-6 w-4 rounded-full border-2 border-current before:absolute before:-bottom-2 before:left-1/2 before:h-2 before:w-3 before:-translate-x-1/2 before:rounded-b-full before:border-b-2 before:border-l-2 before:border-r-2 before:border-current after:absolute after:-bottom-4 after:left-1/2 after:h-2 after:w-px after:-translate-x-1/2 after:bg-current" />
              </button>
              <textarea
                className="min-h-[124px] w-full resize-none rounded-2xl border border-[#e6d8c7] bg-[#fffaf2] p-3 leading-7 outline-none focus:border-[#9ccfc4]"
                value={isListening ? "语音输入中..." : input}
                onChange={(event) => setInput(event.target.value)}
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {examples.map((example) => (
                <button
                  className="rounded-full border border-[#e6d8c7] bg-white px-3 py-2 text-left text-xs leading-5 text-[#443d35]"
                  key={example}
                  type="button"
                  onClick={() => setInput(example)}
                >
                  {example}
                </button>
              ))}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-[#746d64]">补充偏好</span>
              {preferenceOptions.map((item) => {
                const active = preferences.includes(item);
                return (
                  <button
                    className={`rounded-full border px-3 py-2 text-xs font-bold ${active ? "border-[#b8d8ce] bg-[#e5f3ed] text-[#2f6f62]" : "border-[#e6d8c7] bg-white text-[#443d35]"}`}
                    key={item}
                    type="button"
                    onClick={() => setPreferences(active ? preferences.filter((value) => value !== item) : [...preferences, item])}
                  >
                    {item}
                  </button>
                );
              })}
            </div>

            <button className="mt-4 h-12 w-full rounded-2xl bg-[#e76f2c] font-black text-white" type="button" onClick={() => generateWithLoading()}>
              生成路线
            </button>
          </section>
        </section>
      )}

      {status === "loading" && (
        <section className="mx-auto grid min-h-screen w-full max-w-[520px] place-items-center px-5 py-8">
          <div className="w-full rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-6 text-center shadow-[0_18px_45px_rgba(48,39,28,0.12)]">
            <div className="mx-auto mb-5 h-11 w-11 animate-spin rounded-full border-4 border-[#efd9c8] border-t-[#e76f2c]" />
            <h2 className="text-xl font-black">{loadingSteps[loadingStep]}</h2>
            <div className="mt-5 grid gap-3 text-left">
              {loadingSteps.map((step, index) => (
                <div className={`flex items-center gap-3 ${index <= loadingStep ? "font-bold text-[#2f6f62]" : "text-[#746d64]"}`} key={step}>
                  <span className={`grid h-7 w-7 place-items-center rounded-full text-xs ${index <= loadingStep ? "bg-[#e5f3ed]" : "bg-[#eee2d4]"}`}>{index + 1}</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {status === "result" && routeData && (
        <section className="mx-auto grid w-full max-w-[920px] gap-4 px-4 py-4 md:grid-cols-2 md:items-start md:px-6">
          <header className="sticky top-0 z-20 -mx-4 bg-[#f6efe4]/90 px-4 py-3 backdrop-blur md:col-span-2 md:-mx-6 md:px-6">
            <button className="mb-3 border-0 bg-transparent text-sm font-black text-[#2f6f62]" type="button" onClick={() => setStatus("idle")}>
              重新输入
            </button>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {routeData.chips.map((chip, index) => (
                <button
                  className={`shrink-0 rounded-full border px-3 py-2 text-xs font-bold ${chip.editable ? "border-[#b8d8ce] bg-[#e5f3ed] text-[#2f6f62]" : "border-[#e6d8c7] bg-white text-[#443d35]"}`}
                  key={`${chip.id}-${chip.label}-${index}`}
                  type="button"
                  onClick={() => editChip(chip)}
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </header>

          <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)] md:col-span-2">
            <span className="rounded-full bg-[#fff0e5] px-3 py-1 text-xs font-black text-[#b84f18]">当前推荐</span>
            <h2 className="mt-3 text-[28px] font-black leading-tight">{routeData.title}</h2>
            <p className="mt-2 text-[15px] leading-7 text-[#746d64]">{routeData.summary}</p>
            <div className="mt-4 grid grid-cols-4 gap-2">
              <Metric label="总耗时" value={formatMinutes(routeData.metrics.totalMinutes)} />
              <Metric label="人均" value={`${routeData.metrics.costPerPerson}元`} />
              <Metric label="步行" value={`${routeData.metrics.walkKm}km`} />
              <Metric label="等待" value={routeData.metrics.waitRisk} />
            </div>
            <button className="mt-4 h-12 w-full rounded-2xl bg-[#e76f2c] font-black text-white" type="button">
              按这条走
            </button>
          </section>

          <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)] md:col-span-2">
            <h3 className="mb-3 text-lg font-black">交通方案摘要</h3>
            <div className="grid gap-2">
              {routeData.transport.map((leg) => (
                <div className="rounded-2xl bg-[#f3eee5] p-3" key={`${leg.from}-${leg.to}`}>
                  <b>{leg.mode} {leg.minutes}分钟</b>
                  <span className="mt-1 block text-sm leading-6 text-[#746d64]">{leg.action}</span>
                </div>
              ))}
            </div>
          </section>

          <MapPanel routeData={routeData} selectedPoiId={selectedPoiId} onSelect={setSelectedPoiId} />
          <TimelinePanel routeData={routeData} selectedPoiId={selectedPoiId} onSelect={setSelectedPoiId} />

          <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)] md:col-span-2">
            <div className="mb-3 flex items-end justify-between gap-3">
              <div>
                <h3 className="text-lg font-black">目的地卡片</h3>
                {selectedPoi && <p className="mt-1 text-sm text-[#746d64]">当前选中：{selectedPoi.name}</p>}
              </div>
            </div>
            <div className="grid auto-cols-[minmax(260px,82%)] grid-flow-col gap-3 overflow-x-auto pb-1 md:auto-cols-[minmax(260px,31%)]">
              {routeData.nodes.map((node, index) => (
                <article
                  className={`overflow-hidden rounded-[18px] border bg-white ${selectedPoiId === node.id ? "border-[#9ccfc4]" : "border-[#e6d8c7]"}`}
                  key={node.id}
                  onClick={() => setSelectedPoiId(node.id)}
                >
                  <div className={`h-28 bg-gradient-to-br ${node.imageTone} p-3`}>
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-white/90 font-black text-[#2f6f62]">{node.icon}</span>
                  </div>
                  <div className="p-3">
                    <h4 className="font-black">{node.name}</h4>
                    <p className="mt-1 text-sm leading-6 text-[#746d64]">{node.address}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <SmallPill>{node.openTime}</SmallPill>
                      <SmallPill>评价 {node.rating}</SmallPill>
                      <SmallPill>{node.price ? `${node.price}元` : "免费"}</SmallPill>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {node.tags.map((tag) => (
                        <span className="rounded-full bg-[#e5f3ed] px-2 py-1 text-xs font-bold text-[#2f6f62]" key={tag}>{tag}</span>
                      ))}
                    </div>
                    <div className="mt-3 rounded-2xl bg-[#f9f3eb] p-3">
                      <b className="text-sm">为什么推荐</b>
                      <p className="mt-1 text-sm leading-6 text-[#746d64]">{node.reason}</p>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <ActionButton onClick={() => replaceNode(node.id)}>替换</ActionButton>
                      <ActionButton disabled={node.id === "start"} onClick={() => deleteNode(node.id)}>删除</ActionButton>
                      <ActionButton disabled={index <= 1} onClick={() => moveNode(node.id, -1)}>上移</ActionButton>
                      <ActionButton disabled={index === 0 || index === routeData.nodes.length - 1} onClick={() => moveNode(node.id, 1)}>下移</ActionButton>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)] md:col-span-2">
            <h3 className="text-lg font-black">快速调整</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              <ActionButton onClick={() => applyScenario("queue")}>餐厅排队太久</ActionButton>
              <ActionButton onClick={() => applyScenario("budget100")}>预算降到 100</ActionButton>
              <ActionButton onClick={() => applyScenario("noCoffee")}>不要咖啡</ActionButton>
              <ActionButton onClick={() => applyScenario("short")}>只剩 2 小时</ActionButton>
            </div>
            {routeData.diff ? (
              <DiffPanel diff={routeData.diff} />
            ) : (
              <p className="mt-3 rounded-2xl bg-[#f9f3eb] p-3 text-sm leading-6 text-[#746d64]">点击任一情况，系统会只调整相关节点并展示变化。</p>
            )}
          </section>

          <footer className="pb-8 text-xs leading-6 text-[#746d64] md:col-span-2">
            当前页面使用样例 POI 数据来演示完整路线决策流程；真实上线时，地点、路线耗时、排队和标签会替换为地图服务、业务数据和模型解析结果。
          </footer>
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-[#f7efe5] px-2 py-3">
      <b className="block text-sm leading-tight md:text-base">{value}</b>
      <span className="mt-1 block text-[11px] font-bold text-[#746d64]">{label}</span>
    </div>
  );
}

function SmallPill({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-[#f2ece3] px-2 py-1 text-xs font-bold text-[#5c5349]">{children}</span>;
}

function ActionButton({ children, disabled, onClick }: { children: React.ReactNode; disabled?: boolean; onClick: () => void }) {
  return (
    <button
      className="rounded-full border border-[#e6d8c7] bg-white px-3 py-2 text-xs font-bold text-[#443d35] disabled:cursor-not-allowed disabled:opacity-35"
      disabled={disabled}
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
    >
      {children}
    </button>
  );
}

function MapPanel({ routeData, selectedPoiId, onSelect }: { routeData: RouteData; selectedPoiId: string; onSelect: (id: string) => void }) {
  const polyline = routeData.nodes.map((node) => `${node.mapX},${node.mapY}`).join(" ");
  return (
    <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)]">
      <h3 className="mb-3 text-lg font-black">路线地图</h3>
      <div className="relative h-[280px] overflow-hidden rounded-[18px] bg-[#edf0e8]">
        <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none" viewBox="0 0 100 100">
          <path d="M38 6 C68 0 91 22 88 52 C85 82 55 98 29 82 C8 68 9 20 38 6Z" fill="#a5d8d1" />
          <path d="M8 42 C26 31 40 39 43 56 C47 76 31 88 16 80 C4 72 0 53 8 42Z" fill="#cfe7ca" />
          <path d="M5 70 C26 60 42 63 58 72 C72 79 84 78 96 70" fill="none" stroke="#f4d4aa" strokeWidth="3.5" />
          <path d="M19 19 C35 31 49 34 68 28 C80 24 88 32 94 45" fill="none" stroke="#fff" strokeWidth="2.5" />
          <path d="M20 5 C18 24 21 45 18 92" fill="none" stroke="#fff" strokeWidth="2.5" />
          <polyline fill="none" points={polyline} stroke="#e76f2c" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.4" />
        </svg>
        <span className="absolute right-10 top-[112px] text-3xl font-black text-black/25">西湖</span>
        {routeData.nodes.map((node, index) => (
          <button
            className="absolute flex max-w-[145px] -translate-x-3 -translate-y-1/2 items-center gap-1.5 rounded-full border border-black/10 bg-[#fffdf8]/95 py-1 pl-1 pr-2 text-left text-[11px] font-black shadow"
            key={node.id}
            style={{ left: `${node.mapX}%`, top: `${node.mapY}%` }}
            type="button"
            onClick={() => onSelect(node.id)}
          >
            <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-white ${selectedPoiId === node.id ? "bg-[#e76f2c]" : "bg-[#2f6f62]"}`}>{index + 1}</span>
            <span className="truncate">{node.name}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function TimelinePanel({ routeData, selectedPoiId, onSelect }: { routeData: RouteData; selectedPoiId: string; onSelect: (id: string) => void }) {
  let cursor = 14 * 60;
  return (
    <section className="rounded-[22px] border border-[#e6d8c7] bg-[#fffdf8] p-4 shadow-[0_18px_45px_rgba(48,39,28,0.12)]">
      <h3 className="mb-3 text-lg font-black">今天怎么走</h3>
      <div className="grid gap-3">
        {routeData.nodes.map((node, index) => {
          const start = formatClock(cursor);
          cursor += node.stayMinutes;
          const leg = routeData.transport[index];
          if (leg) cursor += leg.minutes;
          return (
            <button
              className={`grid w-full grid-cols-[56px_1fr] gap-3 rounded-2xl border p-3 text-left ${selectedPoiId === node.id ? "border-[#9ccfc4] bg-[#eef8f4]" : "border-[#e6d8c7] bg-white"}`}
              key={node.id}
              type="button"
              onClick={() => onSelect(node.id)}
            >
              <time className="font-black text-[#2f6f62]">{start}</time>
              <div>
                <b>{node.action}</b>
                <span className="mt-1 block text-xs leading-5 text-[#746d64]">{node.stayMinutes}分钟 · {node.name}</span>
                {leg && <span className="mt-2 block text-xs leading-5 text-[#746d64]">下一段：{leg.mode} {leg.minutes}分钟到 {leg.to}</span>}
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function DiffPanel({ diff }: { diff: RouteDiff }) {
  return (
    <div className="mt-3 rounded-2xl bg-[#fff4ea] p-3">
      <strong>{diff.title}</strong>
      <p className="mt-1 text-sm leading-6 text-[#746d64]">{diff.reason}</p>
      <div className="my-3 font-black text-[#b84f18]">{diff.changed}</div>
      <div className="grid grid-cols-2 gap-2">
        <DiffMetric label="耗时" before={formatMinutes(diff.before.totalMinutes)} after={formatMinutes(diff.after.totalMinutes)} />
        <DiffMetric label="预算" before={`${diff.before.costPerPerson}元`} after={`${diff.after.costPerPerson}元`} />
        <DiffMetric label="步行" before={`${diff.before.walkKm}km`} after={`${diff.after.walkKm}km`} />
        <DiffMetric label="等待" before={diff.before.waitRisk} after={diff.after.waitRisk} />
      </div>
      <p className="mt-3 text-sm leading-6 text-[#746d64]">保留：{diff.kept.join("、") || "无"}</p>
      {diff.removed.length > 0 && <p className="text-sm leading-6 text-[#746d64]">删除：{diff.removed.join("、")}</p>}
      {diff.added.length > 0 && <p className="text-sm leading-6 text-[#746d64]">新增：{diff.added.join("、")}</p>}
    </div>
  );
}

function DiffMetric({ label, before, after }: { label: string; before: string; after: string }) {
  return (
    <div className="rounded-2xl bg-[#f7efe5] p-3">
      <span className="block text-xs font-bold text-[#746d64]">{label}</span>
      <b className="mt-1 block text-sm">{before} → {after}</b>
    </div>
  );
}
