const STORAGE_KEY = "garden_cat_web_credentials_v1";

const FLOWER_ICON_ASSET = {
  lavender: "/static/lavender.svg",
  lily: "/static/lily.svg",
};

const FLOWER_EMOJI = {
  daisy: "🌼",
  tulip: "🌷",
  sunflower: "🌻",
  rose: "🌹",
  lavender: "🪻",
  lily: "🌺",
  cherry: "🌸",
  moonflower: "🌙",
};

const ITEM_EMOJI = {
  basic_food: "🥣",
  premium_food: "🍗",
  water_bowl: "💧",
  cat_bed: "🛏️",
  ball: "🧶",
  feather_wand: "🪶",
};

let credentials = null;
let catalog = null;
let currentState = null;
let isBusy = false;
let petCooldownTimer = null;
let latestGardenNotice = "";
let stateSnapshotAtMs = 0;
let liveRefreshQueued = false;

const GAME_MINUTES_PER_REAL_SECOND = 96 / 60;
const VASE_LIFESPAN_SECONDS = 12 * 60 * 60;

const $ = (selector) => document.querySelector(selector);
const welcomeScreen = $("#welcomeScreen");
const appShell = $("#app");
const toast = $("#toast");

function escapeText(value) {
  return String(value ?? "");
}

function setFlowerIcon(element, flowerId, fallback = "🌺") {
  const asset = FLOWER_ICON_ASSET[flowerId];
  if (asset) {
    const image = document.createElement("img");
    image.src = asset;
    image.alt = catalog?.flowers?.[flowerId]?.name || "花朵";
    image.className = "flower-icon-image";
    element.replaceChildren(image);
    return;
  }
  element.textContent = FLOWER_EMOJI[flowerId] || fallback;
}

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return "暂停中";
  const total = Math.max(0, Number(seconds) || 0);
  if (total < 60) return `${Math.ceil(total)}秒`;
  if (total < 3600) return `${Math.floor(total / 60)}分${Math.floor(total % 60)}秒`;
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  return `${hours}小时${minutes}分`;
}


function getDaypartLabel(hour) {
  if (hour >= 5 && hour < 8) return "清晨";
  if (hour >= 8 && hour < 12) return "上午";
  if (hour >= 12 && hour < 14) return "中午";
  if (hour >= 14 && hour < 18) return "下午";
  if (hour >= 18 && hour < 21) return "傍晚";
  return "夜晚";
}

function getSnapshotElapsedSeconds() {
  if (!stateSnapshotAtMs) return 0;
  return Math.max(0, (Date.now() - stateSnapshotAtMs) / 1000);
}

function updateLiveGameTime() {
  if (!currentState) return;

  const baseMinutes =
    (Math.max(1, Number(currentState.game_day) || 1) - 1) * 24 * 60 +
    (Number(currentState.game_hour) || 0) * 60 +
    (Number(currentState.game_minute) || 0);

  const liveMinutes = Math.floor(
    baseMinutes + getSnapshotElapsedSeconds() * GAME_MINUTES_PER_REAL_SECOND
  );

  const day = Math.floor(liveMinutes / (24 * 60)) + 1;
  const minuteOfDay = ((liveMinutes % (24 * 60)) + 24 * 60) % (24 * 60);
  const hour = Math.floor(minuteOfDay / 60);
  const minute = minuteOfDay % 60;

  const target = $("#weatherMeta");
  if (target) {
    target.textContent =
      `第${day}天 · ${getDaypartLabel(hour)} ` +
      `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  }
}

function getLiveVaseLabel(remainingSeconds) {
  if (remainingSeconds <= 0) return "🥀 已枯萎";
  const elapsed = VASE_LIFESPAN_SECONDS - remainingSeconds;
  const ratio = elapsed / VASE_LIFESPAN_SECONDS;
  if (ratio < 0.50) return "🌸 新鲜";
  if (ratio < 0.83) return "🌷 微微蔫";
  return "🍂 即将枯萎";
}

function queueLiveRefresh() {
  if (liveRefreshQueued || isBusy || !credentials) return;
  liveRefreshQueued = true;

  window.setTimeout(() => {
    if (!credentials) {
      liveRefreshQueued = false;
      return;
    }
    refreshGarden({ quiet: true }).catch(() => {
      liveRefreshQueued = false;
    });
  }, 250);
}

function updateLiveCountdowns() {
  if (!currentState || document.visibilityState !== "visible") return;

  const elapsed = getSnapshotElapsedSeconds();
  let crossedBoundary = false;

  updateLiveGameTime();

  for (const pot of currentState.pots || []) {
    if (
      pot.status !== "growing" ||
      !pot.watered ||
      pot.has_pest ||
      pot.remaining_seconds === null ||
      pot.remaining_seconds === undefined
    ) {
      continue;
    }

    const remaining = Math.max(0, Number(pot.remaining_seconds) - elapsed);
    const statusElement = document.querySelector(
      `[data-live-pot-status="${pot.slot}"]`
    );
    const progressElement = document.querySelector(
      `[data-live-pot-progress="${pot.slot}"]`
    );

    if (statusElement) {
      statusElement.textContent =
        remaining <= 0
          ? "花已经盛开，可以收获了。"
          : `生长中，还需约${formatDuration(remaining)}`;
    }

    if (progressElement && pot.flower && catalog?.flowers?.[pot.flower]) {
      const growTime = Number(catalog.flowers[pot.flower].grow_time) || 1;
      const speed = Math.max(0, Number(pot.grow_speed) || 0);
      const progress = Math.max(
        0,
        Math.min(100, ((growTime - remaining * speed) / growTime) * 100)
      );
      progressElement.style.width = `${progress}%`;
    }

    if (remaining <= 0) crossedBoundary = true;
  }

  for (const entry of currentState.vase?.flowers || []) {
    const remaining = Math.max(0, Number(entry.remaining_seconds) - elapsed);
    const infoElement = document.querySelector(
      `[data-live-vase-info="${entry.position}"]`
    );

    if (infoElement) {
      const label = getLiveVaseLabel(remaining);
      infoElement.textContent =
        remaining > 0 ? `${label} · ${formatDuration(remaining)}` : label;
    }
  }

  if (crossedBoundary) queueLiveRefresh();
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 2600);
}

function setBusy(value) {
  isBusy = value;
  document.body.classList.toggle("loading", value);
  $("#refreshBtn").classList.toggle("spin", value);
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  });
}

function saveCredentials(value) {
  credentials = value;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}

function loadCredentials() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed.session_id || !parsed.garden_token) return null;
    return parsed;
  } catch {
    return null;
  }
}

function showWelcome() {
  welcomeScreen.classList.remove("hidden");
  appShell.classList.add("hidden");
}

function showApp() {
  welcomeScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch {
    throw new Error("服务器返回了无法识别的内容。");
  }
  if (!response.ok) {
    throw new Error(data.message || `请求失败（${response.status}）`);
  }
  return data;
}

function authHeaders(extra = {}) {
  return {
    "Content-Type": "application/json",
    "X-Garden-Token": credentials?.garden_token || "",
    ...extra,
  };
}

async function createGarden(name) {
  setBusy(true);
  try {
    const data = await requestJson("/web/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    saveCredentials({
      session_id: data.session_id,
      garden_token: data.garden_token,
    });
    showApp();
    updateFromResponse(data);
    showToast("花园创建成功 🌱");
  } finally {
    setBusy(false);
  }
}

async function refreshGarden({ quiet = false } = {}) {
  if (!credentials || isBusy) return;
  setBusy(true);
  try {
    const query = encodeURIComponent(credentials.session_id);
    const data = await requestJson(`/web/status?session_id=${query}`, {
      headers: authHeaders(),
    });
    updateFromResponse(data, quiet);
  } catch (error) {
    if (!quiet) showToast(error.message);
    if (/钥匙/.test(error.message)) {
      localStorage.removeItem(STORAGE_KEY);
      credentials = null;
      showWelcome();
    }
    throw error;
  } finally {
    setBusy(false);
  }
}

async function runCommand(command, sourceButton = null) {
  if (!credentials || isBusy) return;

  const originalLabel = sourceButton?.textContent || "";

  if (sourceButton) {
    sourceButton.disabled = true;
    sourceButton.classList.add("pending-action");
    sourceButton.setAttribute("aria-busy", "true");

    if (command.startsWith("harvest")) {
      sourceButton.textContent = "收获中…";
    } else if (command.startsWith("buy")) {
      sourceButton.textContent = "购买中…";
    } else if (command.startsWith("water")) {
      sourceButton.textContent = "浇水中…";
    } else if (command.startsWith("plant")) {
      sourceButton.textContent = "种植中…";
    } else if (command.startsWith("arrange")) {
      sourceButton.textContent = "插花中…";
    } else {
      sourceButton.textContent = "处理中…";
    }
  }

  if (command.startsWith("harvest")) {
    showToast("正在收获，请稍等一下…");
  }

  setBusy(true);
  await waitForNextPaint();

  try {
    const data = await requestJson("/web/cmd", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        session_id: credentials.session_id,
        command,
      }),
    });

    updateFromResponse(data);

    if (!data.ok) {
      const firstLine = String(data.message || "这个操作没有成功")
        .split("\n")
        .find((line) => line.trim());
      showToast(firstLine || "这个操作没有成功");
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);

    if (sourceButton?.isConnected) {
      sourceButton.disabled = false;
      sourceButton.classList.remove("pending-action");
      sourceButton.removeAttribute("aria-busy");
      sourceButton.textContent = originalLabel;
    }
  }
}

function updateFromResponse(data, quiet = false) {
  currentState = data.state;
  stateSnapshotAtMs = Date.now();
  liveRefreshQueued = false;
  if (!quiet && data.message) latestGardenNotice = data.message;
  renderAll();
  updateLiveCountdowns();
  if (!quiet && data.message) {
    $("#messageBox").textContent = data.message;
  }
}

function renderAll() {
  if (!currentState || !catalog) return;
  $("#gardenTitle").textContent = currentState.garden_name || "我的小花园";
  $("#weatherEmoji").textContent = currentState.weather_emoji || "🌤️";
  $("#weatherName").textContent = currentState.weather_name || "未知";
  $("#weatherMeta").textContent = `第${currentState.game_day || 1}天 · ${currentState.daypart || ""} ${String(currentState.game_hour || 0).padStart(2, "0")}:${String(currentState.game_minute || 0).padStart(2, "0")}`;
  $("#moneyValue").textContent = `${currentState.money} 块`;
  $("#encyclopediaValue").textContent = `${currentState.encyclopedia_count} / ${Object.keys(catalog.flowers).length}`;
  $("#earnedValue").textContent = `${currentState.total_earned} 块`;
  $("#potCountMeta").textContent = `已解锁 ${currentState.max_pots} / ${currentState.pot_capacity || catalog.max_pots || 6}`;
  const readyCount = (currentState.pots || []).filter(
    (pot) => pot.status === "ready" && !pot.has_pest
  ).length;
  const harvestAllButton = $("#harvestAllBtn");
  harvestAllButton.disabled = readyCount === 0;
  harvestAllButton.textContent = readyCount > 0 ? `一键收获 · ${readyCount}朵` : "暂无成熟花";
  renderGardenNotice();
  renderPots();
  renderVase();
  renderCat();
  renderSeedShop();
  renderCatShop();
  renderInventory();
  renderCollection();
  renderEvents();
  startPetCooldownTimer();
}

function makeButton(label, command, className = "mini-btn", disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.disabled = disabled;
  if (!disabled && command) button.addEventListener("click", () => runCommand(command, button));
  return button;
}

function seedOptions(select) {
  const seeds = currentState.inventory.seeds || {};
  const available = Object.entries(seeds).filter(([, qty]) => qty > 0);
  if (!available.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "没有种子";
    select.append(option);
    select.disabled = true;
    return false;
  }
  for (const [id, qty] of available) {
    const flower = catalog.flowers[id];
    if (!flower) continue;
    const option = document.createElement("option");
    option.value = id;
    option.textContent = `${flower.name} ×${qty}`;
    select.append(option);
  }
  return true;
}


function extractGardenNotice(message) {
  const lines = String(message || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !line.startsWith("📊"));

  const important = lines.filter((line) =>
    /^(🌈|🦋|🎁|✉️|🐛|💀|🌤️|🌧️|🎉|🌸|🧺|🧹|💐)/.test(line)
  );
  if (important.length) return important.slice(0, 4).join("\n");
  return lines[0] || "";
}

function renderGardenNotice() {
  const root = $("#gardenNoticeText");
  let notice = extractGardenNotice(latestGardenNotice);
  if (!notice) {
    const events = currentState.recent_events || [];
    notice = events.length
      ? events[events.length - 1]
      : "花园很安静，风从花叶间穿过去。";
  }
  root.textContent = notice;
}


function renderPots() {
  const grid = $("#potsGrid");
  grid.innerHTML = "";

  const capacity = currentState.pot_capacity || catalog.max_pots || 6;
  const unlockedCount = currentState.max_pots || currentState.pots.length;
  const unlockCosts = catalog.pot_unlock_costs || {};

  for (let slot = 1; slot <= capacity; slot += 1) {
    if (slot > unlockedCount) {
      const card = document.createElement("div");
      card.className = "pot-card locked-pot";

      const number = document.createElement("span");
      number.className = "pot-number";
      number.textContent = `POT ${String(slot).padStart(2, "0")}`;

      const lock = document.createElement("div");
      lock.className = "locked-pot-icon";
      lock.textContent = "🔒";

      const title = document.createElement("div");
      title.className = "flower-name";
      title.textContent = "尚未解锁";

      const cost = Number(unlockCosts[String(slot)] ?? unlockCosts[slot] ?? 0);
      const isNext = slot === unlockedCount + 1;

      const status = document.createElement("div");
      status.className = "pot-status";
      status.textContent = isNext
        ? `花费 ${cost} 金币扩建这块花圃`
        : "请先解锁前一个花盆";

      const actions = document.createElement("div");
      actions.className = "pot-actions";
      if (isNext) {
        actions.append(
          makeButton(
            `解锁 · ${cost}块`,
            "buy_pot",
            "mini-btn gold",
            currentState.money < cost
          )
        );
      } else {
        actions.append(makeButton("暂未开放", null, "mini-btn", true));
      }

      card.append(number, lock, title, status, actions);
      grid.append(card);
      continue;
    }

    const pot = currentState.pots[slot - 1] || { slot, status: "empty" };
    const card = document.createElement("div");
    card.className = `pot-card ${pot.status === "empty" ? "empty-pot" : ""} ${pot.status === "withered" ? "withered-pot" : ""}`;

    const number = document.createElement("span");
    number.className = "pot-number";
    number.textContent = `POT ${String(slot).padStart(2, "0")}`;
    card.append(number);

    if (!["empty", "withered"].includes(pot.status)) {
      const speedBadge = document.createElement("span");
      speedBadge.className = `growth-badge ${pot.grow_speed > 0 ? "" : "paused"}`;
      speedBadge.textContent = pot.grow_speed > 0 ? `×${Number(pot.grow_speed).toFixed(1)} 生长` : "生长暂停";
      card.append(speedBadge);
    }

    const visual = document.createElement("div");
    visual.className = "plant-visual";
    if (pot.status === "empty") visual.textContent = "🪴";
    else if (pot.status === "withered") visual.textContent = "🥀";
    else setFlowerIcon(visual, pot.flower);
    card.append(visual);

    const name = document.createElement("div");
    name.className = "flower-name";
    name.textContent = pot.status === "empty" ? "空花盆" : pot.flower_name;
    card.append(name);

    const status = document.createElement("div");
    status.className = "pot-status";
    status.dataset.livePotStatus = String(slot);
    if (pot.status === "empty") status.textContent = "泥土松软，正等着一粒种子。";
    else if (pot.status === "withered") status.textContent = "花已经枯萎，需要清理后才能重新种植。";
    else if (pot.has_pest) status.textContent = "🐛 正在遭受虫害，请尽快治疗。";
    else if (pot.status === "ready") status.textContent = "花已经盛开，可以收获了。";
    else if (!pot.watered) status.textContent = "尚未浇水，生长暂停。";
    else status.textContent = `生长中，还需约${formatDuration(pot.remaining_seconds)}`;
    card.append(status);

    if (!["empty", "withered"].includes(pot.status)) {
      const track = document.createElement("div");
      track.className = "progress-track";
      const fill = document.createElement("div");
      fill.className = "progress-fill";
      fill.dataset.livePotProgress = String(slot);
      fill.style.width = `${pot.progress_pct || 0}%`;
      track.append(fill);
      card.append(track);
    }

    const actions = document.createElement("div");
    actions.className = "pot-actions";
    if (pot.status === "empty") {
      const select = document.createElement("select");
      const hasSeeds = seedOptions(select);
      const plant = makeButton("种下", null, "mini-btn", !hasSeeds);
      plant.addEventListener("click", () => {
        if (select.value) runCommand(`plant ${select.value} ${slot}`, plant);
      });
      actions.append(select, plant);
    } else if (pot.status === "withered") {
      actions.append(makeButton("清理花盆", `clear ${slot}`, "mini-btn rose"));
    } else {
      if (!pot.watered) {
        actions.append(makeButton("浇水", `water ${slot}`));
      } else if (currentState.weather === "rainy") {
        actions.append(makeButton("🌧️ 雨水滋润中", null, "mini-btn", true));
      } else {
        actions.append(makeButton("已浇水", null, "mini-btn", true));
      }
      if (pot.has_pest) actions.append(makeButton("治疗 3块", `treat ${slot}`, "mini-btn rose", currentState.money < 3));
      if (pot.status === "ready" && !pot.has_pest) actions.append(makeButton("收获", `harvest ${slot}`, "mini-btn gold"));
    }
    card.append(actions);
    grid.append(card);
  }
}

function renderVase() {
  const grid = $("#vaseGrid");
  grid.innerHTML = "";
  const entries = currentState.vase?.flowers || [];
  const capacity = currentState.vase?.capacity || catalog.vase_capacity || 3;
  const flowersInBag = Object.entries(currentState.inventory.flowers || {}).filter(([, qty]) => qty > 0);

  for (let position = 1; position <= capacity; position += 1) {
    const entry = entries.find((item) => item.position === position);
    const slot = document.createElement("div");
    slot.className = "vase-slot real-vase-slot";
    if (entry) {
      const icon = document.createElement("div");
      icon.className = "vase-flower";
      setFlowerIcon(icon, entry.flower);
      const name = document.createElement("strong");
      name.textContent = entry.flower_name;
      const info = document.createElement("small");
      info.dataset.liveVaseInfo = String(position);
      info.textContent = `${entry.freshness_label}${entry.remaining_seconds > 0 ? ` · ${formatDuration(entry.remaining_seconds)}` : ""}`;
      slot.append(icon, name, info, makeButton("移除", `remove_vase ${position}`, "mini-btn rose"));
    } else {
      const icon = document.createElement("div");
      icon.className = "vase-flower";
      icon.textContent = "〰️";
      const name = document.createElement("strong");
      name.textContent = `空位 ${position}`;
      const select = document.createElement("select");
      if (!flowersInBag.length) {
        const option = document.createElement("option");
        option.textContent = "背包里没有鲜花";
        option.value = "";
        select.append(option);
        select.disabled = true;
      } else {
        for (const [id, qty] of flowersInBag) {
          const option = document.createElement("option");
          option.value = id;
          option.textContent = `${catalog.flowers[id]?.name || id} ×${qty}`;
          select.append(option);
        }
      }
      const button = makeButton("插入花瓶", null, "mini-btn", !flowersInBag.length);
      button.addEventListener("click", () => {
        if (select.value) runCommand(`arrange ${select.value}`, button);
      });
      slot.append(icon, name, select, button);
    }
    grid.append(slot);
  }
}

function statRow(label, value) {
  const row = document.createElement("div");
  row.className = "stat-row";
  const labelEl = document.createElement("span");
  labelEl.textContent = label;
  const track = document.createElement("div");
  track.className = "stat-track";
  const fill = document.createElement("div");
  fill.className = "stat-fill";
  fill.style.width = `${Math.max(0, Math.min(100, value))}%`;
  track.append(fill);
  const number = document.createElement("strong");
  number.textContent = Math.round(value);
  row.append(labelEl, track, number);
  return row;
}

function renderCat() {
  const root = $("#catContent");
  root.innerHTML = "";
  if (!currentState.has_cat) {
    const empty = document.createElement("div");
    empty.className = "cat-empty";
    empty.innerHTML = `<div class="cat-avatar">🐾</div><h3>还没有猫咪入住</h3><p class="muted">攒够100块，就可以接一只猫回家。</p>`;
    const adoptButton = makeButton("收养猫咪 · 100块", null, "primary-btn", currentState.money < 100);
    adoptButton.addEventListener("click", () => {
      const rawName = window.prompt("给猫咪取一个名字（最多12个字符）", "小猫");
      if (rawName === null) return;
      const name = rawName.trim();
      if (name.length > 12) {
        showToast("猫咪名字不能超过12个字符");
        return;
      }
      runCommand(name ? `adopt ${name}` : "adopt", adoptButton);
    });
    empty.append(adoptButton);
    root.append(empty);
    return;
  }

  const cat = currentState.cat;
  const layout = document.createElement("div");
  layout.className = "cat-layout";
  const portrait = document.createElement("div");
  portrait.className = "cat-portrait";
  const catImage = document.createElement("img");
  catImage.src = "/static/orange_cat.png";
  catImage.alt = "躺在猫窝里的橘猫";
  catImage.className = "cat-image";
  const catName = document.createElement("h3");
  catName.textContent = cat.name || "小猫";
  portrait.append(catImage, catName);
  const utilities = document.createElement("div");
  utilities.className = "cat-utilities";
  const owned = new Set(currentState.permanent_items || []);
  utilities.innerHTML = `
    <div class="utility-card ${owned.has("water_bowl") ? "" : "locked"}">💧<strong>水碗</strong></div>
    <div class="utility-card ${owned.has("cat_bed") ? "" : "locked"}">🛏️<strong>猫窝</strong></div>
  `;
  portrait.append(utilities);

  const details = document.createElement("div");
  details.append(
    statRow("饱食", cat.hunger),
    statRow("口渴", cat.thirst),
    statRow("心情", cat.mood),
    statRow("亲密", cat.affection),
  );
  const actions = document.createElement("div");
  actions.className = "cat-actions";
  const items = currentState.inventory.items || {};
  const renameButton = makeButton("改名字", null, "mini-btn");
  renameButton.addEventListener("click", () => {
    const rawName = window.prompt("给猫咪换一个名字（最多12个字符）", cat.name || "小猫");
    if (rawName === null) return;
    const name = rawName.trim();
    if (!name) {
      showToast("猫咪名字不能为空");
      return;
    }
    if (name.length > 12) {
      showToast("猫咪名字不能超过12个字符");
      return;
    }
    runCommand(`rename_cat ${name}`, renameButton);
  });
  actions.append(
    renameButton,
    makeButton(`普通猫粮 ×${items.basic_food || 0}`, "feed basic", "mini-btn", !(items.basic_food > 0)),
    makeButton(`高级猫粮 ×${items.premium_food || 0}`, "feed premium", "mini-btn gold", !(items.premium_food > 0)),
    makeButton("喂水", "give_water"),
    makeButton(cat.pet_cooldown_remaining_seconds > 0 ? `摸摸猫 · ${formatDuration(cat.pet_cooldown_remaining_seconds)}` : "摸摸猫", "pet", "mini-btn", cat.pet_cooldown_remaining_seconds > 0),
    makeButton(`毛线球 ×${items.ball || 0}`, "play ball", "mini-btn", !(items.ball > 0)),
    makeButton(`逗猫棒 ×${items.feather_wand || 0}`, "play feather", "mini-btn", !(items.feather_wand > 0)),
  );
  details.append(actions);
  layout.append(portrait, details);
  root.append(layout);
}

function startPetCooldownTimer() {
  clearInterval(petCooldownTimer);
  if (!currentState?.cat || !(currentState.cat.pet_cooldown_remaining_seconds > 0)) return;
  const deadline = Date.now() + currentState.cat.pet_cooldown_remaining_seconds * 1000;
  petCooldownTimer = setInterval(() => {
    const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    currentState.cat.pet_cooldown_remaining_seconds = remaining;
    if (remaining <= 0) {
      clearInterval(petCooldownTimer);
      renderCat();
      return;
    }
    const buttons = [...document.querySelectorAll(".cat-actions button")];
    const petButton = buttons.find((button) => button.textContent.startsWith("摸摸猫"));
    if (petButton) {
      petButton.textContent = `摸摸猫 · ${formatDuration(remaining)}`;
      petButton.disabled = true;
    }
  }, 1000);
}

function createShopCard({ iconText, iconId, title, metaLines, buttonLabel, command, disabled, locked = false }) {
  const item = document.createElement("div");
  item.className = `shop-square-card ${locked ? "locked" : ""}`;

  const icon = document.createElement("div");
  icon.className = "shop-square-icon";
  if (iconId) setFlowerIcon(icon, iconId);
  else icon.textContent = iconText || "🎁";

  const name = document.createElement("strong");
  name.className = "shop-square-name";
  name.textContent = title;

  const note = document.createElement("small");
  note.className = "shop-square-note";
  note.innerHTML = metaLines.map((line) => escapeText(line)).join("<br>");

  const button = makeButton(
    buttonLabel,
    command,
    "mini-btn shop-buy-btn",
    disabled
  );

  item.append(icon, name, note, button);
  return item;
}

function renderSeedShop() {
  const root = $("#seedShopGrid");
  root.innerHTML = "";
  const unlocked = new Set(currentState.unlocked_flowers || []);

  for (const [id, flower] of Object.entries(catalog.flowers)) {
    const isUnlocked = unlocked.has(id);
    const metaLines = isUnlocked
      ? [`${flower.seed_price}块`, `约${Math.round(flower.grow_time / 60)}分钟成熟`]
      : [`图鉴${flower.unlock_requirement}种后解锁`];

    root.append(
      createShopCard({
        iconText: isUnlocked ? "" : "🔒",
        iconId: isUnlocked ? id : "",
        title: flower.name,
        metaLines,
        buttonLabel: isUnlocked ? "购买" : "未解锁",
        command: `buy ${id} 1`,
        disabled: !isUnlocked || currentState.money < flower.seed_price,
        locked: !isUnlocked,
      })
    );
  }
}

const ITEM_EFFECT_TEXT = {
  basic_food: ["消耗品", "饱食 +30"],
  premium_food: ["消耗品", "饱食 +60 · 心情 +10"],
  water_bowl: ["永久用品", "口渴下降速度减半"],
  cat_bed: ["永久用品", "心情自然下降降低40%"],
  ball: ["一次性玩具", "心情 +15 · 亲密 +5"],
  feather_wand: ["一次性玩具", "心情 +20 · 亲密 +8"],
};

function renderCatShop() {
  const root = $("#catShopGrid");
  root.innerHTML = "";
  const owned = new Set(currentState.permanent_items || []);

  for (const [id, itemData] of Object.entries(catalog.items)) {
    const ownedPermanent = itemData.type === "permanent" && owned.has(id);
    const effectLines = ITEM_EFFECT_TEXT[id] || [
      itemData.type === "permanent"
        ? "永久用品"
        : itemData.type === "toy"
          ? "一次性玩具"
          : "消耗品",
    ];

    root.append(
      createShopCard({
        iconText: ITEM_EMOJI[id] || "🎁",
        title: itemData.name,
        metaLines: [`${itemData.price}块`, ...effectLines],
        buttonLabel: ownedPermanent ? "已拥有" : "购买",
        command: `buy ${id} 1`,
        disabled: ownedPermanent || currentState.money < itemData.price,
      })
    );
  }
}

function renderInventory() {
  const root = $("#inventoryTab");
  root.innerHTML = "";
  let hasAny = false;

  const addGroup = (title, data, kind) => {
    const entries = Object.entries(data || {}).filter(([, qty]) => qty > 0);
    if (!entries.length) return;
    hasAny = true;
    const heading = document.createElement("h3");
    heading.className = "subheading";
    heading.textContent = title;
    const list = document.createElement("div");
    list.className = "inventory-list";
    for (const [id, qty] of entries) {
      const item = document.createElement("div");
      item.className = "inventory-item";
      const icon = document.createElement("div");
      icon.className = "item-icon";
      if (kind === "items") icon.textContent = ITEM_EMOJI[id] || "🎁";
      else setFlowerIcon(icon, id, "🌱");
      const meta = document.createElement("div");
      meta.className = "item-meta";
      const name = kind === "items" ? catalog.items[id]?.name : catalog.flowers[id]?.name;
      meta.innerHTML = `<strong>${escapeText(name || id)}</strong><small>数量 ×${qty}</small>`;
      const actions = document.createElement("div");
      actions.className = "item-actions";
      if (kind === "flowers") {
        actions.append(
          makeButton("卖1朵", `sell ${id} 1`, "mini-btn gold"),
          makeButton("插花", `arrange ${id}`, "mini-btn", (currentState.vase?.flowers?.length || 0) >= (currentState.vase?.capacity || 3)),
        );
      }
      item.append(icon, meta, actions);
      list.append(item);
    }
    root.append(heading, list);
  };

  addGroup("种子", currentState.inventory.seeds, "seeds");
  addGroup("鲜花", currentState.inventory.flowers, "flowers");
  addGroup("物品", currentState.inventory.items, "items");

  if ((Object.values(currentState.inventory.flowers || {}).reduce((a, b) => a + b, 0)) > 0) {
    const sellAll = makeButton("卖掉背包里的全部鲜花", "sell all", "mini-btn gold");
    sellAll.style.marginTop = "12px";
    root.append(sellAll);
  }
  if (!hasAny) root.innerHTML = `<div class="empty-note">背包还是空的。去商店买一包种子吧。</div>`;
}

function renderCollection() {
  const root = $("#collectionTab");
  root.innerHTML = "";
  const heading = document.createElement("h3");
  heading.className = "subheading";
  heading.textContent = `花卉图鉴 · ${currentState.encyclopedia_count}/${Object.keys(catalog.flowers).length}`;
  const grid = document.createElement("div");
  grid.className = "collection-grid";
  const discovered = new Set(currentState.encyclopedia || []);
  for (const [id, flower] of Object.entries(catalog.flowers)) {
    const known = discovered.has(id);
    const item = document.createElement("div");
    item.className = `collection-item ${known ? "" : "unknown"}`;
    const icon = document.createElement("div");
    icon.className = "item-icon";
    if (known) setFlowerIcon(icon, id);
    else icon.textContent = "❔";
    const meta = document.createElement("div");
    meta.className = "item-meta";
    const title = document.createElement("strong");
    title.textContent = known ? flower.name : "尚未发现";
    const note = document.createElement("small");
    note.textContent = known ? flower.rarity_name : "???";
    meta.append(title, note);
    item.append(icon, meta);
    grid.append(item);
  }
  root.append(heading, grid);

  const catHeading = document.createElement("h3");
  catHeading.className = "subheading";
  catHeading.textContent = "猫咪留下的小东西";
  const collected = currentState.collectibles || {};
  const lines = [
    ["shell", "🐚", "贝壳"],
    ["maple_leaf", "🍁", "枫叶"],
    ["pine_needle", "🌲", "松针"],
    ["clover", "🍀", "四叶草"],
    ["wildflower", "🌺", "野花"],
  ];
  const collectibleGrid = document.createElement("div");
  collectibleGrid.className = "collection-grid";
  for (const [id, emoji, label] of lines) {
    const count = collected[id] || 0;
    const item = document.createElement("div");
    item.className = `collection-item ${count ? "" : "unknown"}`;
    item.innerHTML = `<div class="item-icon">${emoji}</div><div class="item-meta"><strong>${label}</strong><small>数量 ×${count}</small></div>`;
    collectibleGrid.append(item);
  }
  root.append(catHeading, collectibleGrid);

  const letters = currentState.letters || [];
  const letterHeading = document.createElement("h3");
  letterHeading.className = "subheading";
  letterHeading.textContent = `猫咪信箱 · ${letters.length}/5`;
  root.append(letterHeading);

  if (!letters.length) {
    const note = document.createElement("div");
    note.className = "empty-note";
    note.textContent = "✉️ 还没有收到猫咪写来的信。";
    root.append(note);
  } else {
    const letterList = document.createElement("div");
    letterList.className = "letter-list";
    for (const letter of letters) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "letter-card";
      button.innerHTML = `<span>✉️</span><div><strong>第 ${letter.index} 封信</strong><small>点击拆开查看</small></div>`;
      button.addEventListener("click", () => showLetterModal(letter));
      letterList.append(button);
    }
    root.append(letterList);
  }
}

function renderEvents() {
  const root = $("#eventsList");
  root.innerHTML = "";
  const events = currentState.recent_events || [];
  if (!events.length) {
    root.innerHTML = `<div class="muted">还没有新的花园事件。</div>`;
    return;
  }
  for (const event of [...events].reverse()) {
    const line = document.createElement("div");
    line.className = "event-line";
    line.textContent = event;
    root.append(line);
  }
}

function showLetterModal(letter) {
  $("#modalTitle").textContent = `第 ${letter.index} 封猫咪来信`;
  const body = $("#modalBody");
  body.innerHTML = "";
  const paper = document.createElement("div");
  paper.className = "letter-paper";
  paper.textContent = letter.text;
  body.append(paper);
  $("#modal").classList.remove("hidden");
}

function showKeyModal() {
  const keyText = JSON.stringify(credentials, null, 2);
  $("#modalTitle").textContent = "你的花园存档码";
  const body = $("#modalBody");
  body.innerHTML = "";
  const intro = document.createElement("p");
  intro.textContent = "换电脑、清除浏览器数据或想在别的设备继续时，需要这把钥匙。请把它保存在私密位置。";
  const box = document.createElement("div");
  box.className = "key-box";
  box.textContent = keyText;
  const actions = document.createElement("div");
  actions.className = "modal-actions";
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "primary-btn";
  copy.textContent = "复制花园存档码";
  copy.addEventListener("click", async () => {
    await navigator.clipboard.writeText(keyText);
    showToast("花园存档码已复制");
  });
  actions.append(copy);
  body.append(intro, box, actions);
  $("#modal").classList.remove("hidden");
}

function closeModal() {
  $("#modal").classList.add("hidden");
}


function openCollectionShortcut() {
  const collectionButton = document.querySelector(
    '.tab-btn[data-tab="collection"]'
  );
  const collectionTab = $("#collectionTab");
  if (!collectionButton || !collectionTab) return;

  document.querySelectorAll(".tab-btn").forEach((item) => {
    item.classList.remove("active");
  });
  document.querySelectorAll(".tab-content").forEach((item) => {
    item.classList.remove("active");
  });

  collectionButton.classList.add("active");
  collectionTab.classList.add("active");

  const panel = collectionButton.closest(".tabs-panel") || collectionTab;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  panel.classList.remove("shortcut-highlight");
  requestAnimationFrame(() => panel.classList.add("shortcut-highlight"));
  window.setTimeout(() => panel.classList.remove("shortcut-highlight"), 1200);
}

async function initialize() {
  try {
    catalog = await requestJson("/api/catalog");
  } catch (error) {
    showToast(`加载游戏资料失败：${error.message}`);
    return;
  }

  credentials = loadCredentials();
  if (!credentials) {
    showWelcome();
    return;
  }
  showApp();
  try {
    await refreshGarden({ quiet: true });
  } catch {
    // refreshGarden 已处理无效钥匙与提示。
  }
}

$("#createForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("#gardenName").value.trim() || "我的小花园";
  try {
    await createGarden(name);
  } catch (error) {
    showToast(error.message);
  }
});

$("#importBtn").addEventListener("click", async () => {
  try {
    const parsed = JSON.parse($("#importKey").value.trim());
    if (!parsed.session_id || !parsed.garden_token) throw new Error("钥匙格式不完整");
    saveCredentials({ session_id: parsed.session_id, garden_token: parsed.garden_token });
    showApp();
    await refreshGarden();
    showToast("旧花园已经打开");
  } catch (error) {
    showToast(error.message || "无法打开这把花园存档码");
  }
});

$("#refreshBtn").addEventListener("click", () => refreshGarden().catch(() => {}));
$("#encyclopediaCard").addEventListener("click", openCollectionShortcut);
$("#encyclopediaCard").addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    openCollectionShortcut();
  }
});
$("#keyBtn").addEventListener("click", showKeyModal);
$("#modalClose").addEventListener("click", closeModal);
$("#modal").addEventListener("click", (event) => { if (event.target.id === "modal") closeModal(); });

$("#harvestAllBtn").addEventListener("click", (event) => runCommand("harvest all", event.currentTarget));

$("#commandForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const command = $("#commandInput").value.trim();
  if (!command) return;
  $("#commandInput").value = "";
  runCommand(command);
});

$("#leaveBtn").addEventListener("click", () => {
  const confirmed = window.confirm("只会从这台设备移除钥匙，云端花园不会被删除。确认继续吗？");
  if (!confirmed) return;
  localStorage.removeItem(STORAGE_KEY);
  credentials = null;
  currentState = null;
  showWelcome();
  showToast("花园存档码已从当前设备移除");
});

for (const button of document.querySelectorAll(".tab-btn")) {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    $(`#${button.dataset.tab}Tab`).classList.add("active");
  });
}

for (const button of document.querySelectorAll(".store-tab-btn")) {
  button.addEventListener("click", () => {
    document.querySelectorAll(".store-tab-btn").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".store-pane").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    const paneId = button.dataset.storeTab === "cat-items"
      ? "#catItemsStorePane"
      : "#seedsStorePane";
    $(paneId).classList.add("active");
  });
}

window.addEventListener("focus", () => {
  if (credentials && !isBusy) refreshGarden({ quiet: true }).catch(() => {});
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && credentials && !isBusy) {
    refreshGarden({ quiet: true }).catch(() => {});
  }
});

setInterval(updateLiveCountdowns, 1_000);

setInterval(() => {
  if (document.visibilityState === "visible" && credentials && !isBusy) {
    refreshGarden({ quiet: true }).catch(() => {});
  }
}, 60_000);

initialize();
