// ===== 计算器浮动面板 =====
$("calcToggleBtn").addEventListener("click", () => {
  $("calcPanel").classList.toggle("hidden");
});
$("calcPanelClose").addEventListener("click", () => {
  $("calcPanel").classList.add("hidden");
});

// 拖动计算器
(function initCalcDrag() {
  const panel = $("calcPanel");
  const header = panel.querySelector(".calc-panel-header");
  if (!panel || !header) return;
  let isDragging = false, startX, startY, startLeft, startTop;

  header.addEventListener("mousedown", (e) => {
    if (e.target.closest(".btn")) return; // 不拦截关闭按钮
    isDragging = true;
    const rect = panel.getBoundingClientRect();
    startX = e.clientX;
    startY = e.clientY;
    startLeft = rect.left;
    startTop = rect.top;
    // 切为 fixed + left/top 定位
    panel.style.right = "auto";
    panel.style.bottom = "auto";
    panel.style.left = startLeft + "px";
    panel.style.top = startTop + "px";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    panel.style.left = (startLeft + dx) + "px";
    panel.style.top = (startTop + dy) + "px";
  });

  document.addEventListener("mouseup", () => { isDragging = false; });
})();

$("colToggleBtn").addEventListener("click", (e) => {
  e.stopPropagation();
  const panel = $("colPanel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) buildColPanel(activeKey);
});
$("colPanelClose").addEventListener("click", () => $("colPanel").classList.add("hidden"));

// 点击外部区域关闭列设置面板
document.addEventListener("click", (e) => {
  const panel = $("colPanel");
  if (panel.classList.contains("hidden")) return;
  if (!panel.contains(e.target) && e.target !== $("colToggleBtn")) {
    panel.classList.add("hidden");
  }
});

$("colPanelBody").addEventListener("change", (e) => {
  if (e.target.type !== "checkbox") return;
  // 全选逻辑
  if (e.target.id === "colSelectAll") {
    const checked = e.target.checked;
    const cols = COLS[activeKey];
    if (checked) {
      hiddenCols[activeKey].clear();
    } else {
      cols.forEach((_, i) => hiddenCols[activeKey].add(i));
    }
    // 更新所有子 checkbox
    $("colPanelBody").querySelectorAll('input[data-idx]').forEach((cb) => { cb.checked = checked; });
    applyColVisibility(activeKey);
    return;
  }
  const idx = +e.target.dataset.idx;
  if (e.target.checked) hiddenCols[activeKey].delete(idx);
  else hiddenCols[activeKey].add(idx);
  applyColVisibility(activeKey);
  // 更新全选状态
  const allSel = $("colSelectAll");
  if (allSel) allSel.checked = hiddenCols[activeKey].size === 0;
});

// applyColVisibility 已在 renderTable 末尾直接调用，无需额外 patch


// ===== 天气模块 =====
// 天气描述英文→中文翻译
const WEATHER_DESC_MAP = {
  "Sunny": "晴", "Clear": "晴", "Partly cloudy": "多云", "Partly Cloudy": "多云",
  "Cloudy": "阴", "Overcast": "阴天", "Mist": "薄雾", "Fog": "雾",
  "Freezing fog": "冻雾", "Patchy rain possible": "可能有零星小雨",
  "Patchy rain nearby": "附近有零星小雨",
  "Patchy snow possible": "可能有零星小雪", "Patchy sleet possible": "可能有零星雨夹雪",
  "Patchy freezing drizzle possible": "可能有零星冻毛毛雨",
  "Thundery outbreaks possible": "可能有雷阵雨", "Blowing snow": "吹雪",
  "Blizzard": "暴风雪", "Patchy light drizzle": "零星小毛毛雨",
  "Light drizzle": "小毛毛雨", "Freezing drizzle": "冻毛毛雨",
  "Heavy freezing drizzle": "大冻毛毛雨", "Patchy light rain": "零星小雨",
  "Light rain": "小雨", "Moderate rain at times": "时有中雨",
  "Moderate rain": "中雨", "Heavy rain at times": "时有大雨",
  "Heavy rain": "大雨", "Light freezing rain": "小冻雨",
  "Moderate or heavy freezing rain": "中到大冻雨",
  "Light sleet": "小雨夹雪", "Moderate or heavy sleet": "中到大雨夹雪",
  "Patchy light snow": "零星小雪", "Light snow": "小雪",
  "Patchy moderate snow": "零星中雪", "Moderate snow": "中雪",
  "Patchy heavy snow": "零星大雪", "Heavy snow": "大雪",
  "Ice pellets": "冰粒", "Light rain shower": "小阵雨",
  "Moderate or heavy rain shower": "中到大阵雨", "Torrential rain shower": "暴雨",
  "Light sleet showers": "小雨夹雪阵雨", "Moderate or heavy sleet showers": "中到大雨夹雪阵雨",
  "Light snow showers": "小阵雪", "Moderate or heavy snow showers": "中到大阵雪",
  "Light showers of ice pellets": "小冰粒阵雨",
  "Moderate or heavy showers of ice pellets": "中到大冰粒阵雨",
  "Patchy light rain with thunder": "零星小雨伴雷", "Moderate or heavy rain with thunder": "中到大雨伴雷",
  "Patchy light snow with thunder": "零星小雪伴雷", "Moderate or heavy snow with thunder": "中到大雪伴雷",
  "Haze": "霾", "Smoke": "烟雾", "Smoky haze": "烟霾", "Dust": "扬尘", "Sand": "沙尘",
};

function translateWeatherDesc(desc) {
  if (!desc) return "未知";
  desc = desc.trim();
  // 精确匹配
  if (WEATHER_DESC_MAP[desc]) return WEATHER_DESC_MAP[desc];
  // 忽略大小写匹配
  const lower = desc.toLowerCase();
  for (const [en, zh] of Object.entries(WEATHER_DESC_MAP)) {
    if (en.toLowerCase() === lower) return zh;
  }
  // 包含关键词匹配
  if (lower.includes("rain")) return "雨";
  if (lower.includes("snow")) return "雪";
  if (lower.includes("cloud")) return "多云";
  if (lower.includes("sun") || lower.includes("clear")) return "晴";
  if (lower.includes("fog") || lower.includes("mist")) return "雾";
  if (lower.includes("haze") || lower.includes("smoke") || lower.includes("smog")) return "霾";
  if (lower.includes("dust") || lower.includes("sand")) return "沙尘";
  if (lower.includes("thunder")) return "雷";
  return desc; // 无法翻译则保留原文
}

(async function loadWeather() {
  try {
    const resp = await fetch("/api/weather");
    const data = await resp.json();
    if (!data.ok) { $("weatherInfo").textContent = "天气获取失败"; return; }
    const { temp, desc, code, city } = data;
    const descZh = translateWeatherDesc(desc);
    $("weatherInfo").innerHTML = `<div class="temp">${temp}°C</div><div class="desc">${city || "北京朝阳"} · ${descZh}</div>`;
    renderWeatherIcon(code, desc);
  } catch (e) {
    $("weatherInfo").textContent = "天气加载失败";
  }
})();

function renderWeatherIcon(code, desc) {
  const icon = $("weatherIcon");
  const c = Number(code);
  // 根据天气代码判断类型
  // 晴天: 113; 多云: 116,119,122; 雨: 176,263,266,293,296,299,302,305,308,311,314,317,353,356,359
  // 雪: 179,182,185,227,230,320,323,326,329,332,335,338,350,368,371,374,377,392,395
  if (c === 113) {
    // 晴天
    icon.innerHTML = '<div class="sun"></div>';
  } else if ([116, 119, 122].includes(c)) {
    // 多云
    icon.innerHTML = '<div class="sun" style="width:20px;height:20px;top:6px;left:2px;"></div><div class="cloud"></div>';
  } else if (desc.includes("雨") || desc.includes("雷") || [176,263,266,293,296,299,302,305,308,311,314,317,353,356,359,386,389].includes(c)) {
    // 雨天
    let drops = '<div class="cloud" style="top:8px;"></div><div class="rain-container">';
    for (let i = 0; i < 8; i++) {
      const left = 5 + Math.random() * 38;
      const h = 8 + Math.random() * 8;
      const delay = Math.random() * 0.8;
      drops += `<div class="raindrop" style="left:${left}px;height:${h}px;top:24px;animation-delay:${delay}s;"></div>`;
    }
    drops += '</div>';
    icon.innerHTML = drops;
  } else if (desc.includes("雪") || [179,182,185,227,230,320,323,326,329,332,335,338,350,368,371,374,377,392,395].includes(c)) {
    // 雪天
    let flakes = '<div class="cloud" style="top:6px;"></div><div class="snow-container">';
    for (let i = 0; i < 6; i++) {
      const left = 6 + Math.random() * 36;
      const delay = Math.random() * 2;
      const size = 3 + Math.random() * 3;
      flakes += `<div class="snowflake" style="left:${left}px;top:22px;width:${size}px;height:${size}px;animation-delay:${delay}s;"></div>`;
    }
    flakes += '</div>';
    icon.innerHTML = flakes;
  } else {
    // 默认多云
    icon.innerHTML = '<div class="cloud"></div>';
  }
}


// ===== 更新日志 =====
(function initChangelog() {
  const btn = $("changelogBtn");
  const popup = $("changelogPopup");
  const closeBtn = $("changelogClose");
  if (!btn || !popup) return;
  btn.addEventListener("click", (e) => { e.stopPropagation(); popup.classList.toggle("hidden"); });
  closeBtn.addEventListener("click", () => popup.classList.add("hidden"));
  document.addEventListener("click", (e) => {
    if (!popup.contains(e.target) && e.target !== btn) popup.classList.add("hidden");
  });
})();


// ===== 环境切换 =====
(function initEnvSwitch() {
  const toggle = $("envToggle");
  const label = $("envLabel");
  if (!toggle || !label) return;

  // 初始化：获取后端当前环境状态
  fetch("/api/env").then(r => r.json()).then(data => {
    if (data.ok) {
      const isProd = data.env === "production";
      toggle.checked = isProd;
      updateEnvLabel(data.env, data.label);
    }
  }).catch(() => {});

  // 切换事件
  toggle.addEventListener("change", async () => {
    const env = toggle.checked ? "production" : "test";
    try {
      const resp = await fetch("/api/env", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ env }),
      });
      const data = await resp.json();
      if (data.ok) {
        updateEnvLabel(data.env, data.label);
        setStatus(data.msg, data.env === "production" ? "error" : "ok");
        // 切换环境后自动检查/恢复登录
        autoCheckLogin();
        // 清空所有表的数据
        TABLES.forEach((t) => {
          st[t.key].records = [];
          st[t.key].total = 0;
          st[t.key].pageNo = 1;
          renderTable(t.key);
        });
      } else {
        setStatus(data.msg || "切换失败", "error");
        // 回退开关
        toggle.checked = !toggle.checked;
      }
    } catch (e) {
      setStatus("切换环境失败：" + e.message, "error");
      toggle.checked = !toggle.checked;
    }
  });

  function updateEnvLabel(env, text) {
    label.textContent = "环境:";
    label.classList.remove("env-prod", "env-test");
    label.classList.add(env === "production" ? "env-prod" : "env-test");
    // 生产环境时整个头部容器标红，方便区分
    const box = document.querySelector(".header-bar-box");
    if (box) {
      box.classList.toggle("env-danger", env === "production");
    }
  }
})();


// ===== 日志面板 =====
(function initLogPanel() {
  const logBody = $("logBody");
  const logEntries = $("logEntries");
  const logCount = $("logCount");
  const toggleBtn = $("logToggleBtn");
  const refreshBtn = $("logRefreshBtn");
  const clearBtn = $("logClearBtn");
  if (!logBody || !logEntries) return;

  let collapsed = false;

  // 渲染日志
  function renderLogs(logs) {
    if (!logs || !logs.length) {
      logEntries.innerHTML = '<div class="log-empty">暂无日志，执行查询后会自动记录</div>';
      logCount.textContent = "0";
      return;
    }
    logCount.textContent = logs.length;
    logEntries.innerHTML = logs.map(log => {
      const levelIcon = log.level === "error" ? "✗" : log.level === "warn" ? "⚠" : "●";
      let detail = String(log.detail || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      // 如果是 JSON 格式，格式化为缩进展示
      if (detail.startsWith("{") || detail.startsWith("[")) {
        try {
          const obj = JSON.parse(log.detail);
          detail = JSON.stringify(obj, null, 2).replace(/</g, "&lt;").replace(/>/g, "&gt;");
          detail = `<pre class="log-json">${detail}</pre>`;
        } catch (e) { /* 非有效JSON，保持原样 */ }
      }
      return `<div class="log-entry">
        <span class="log-time">${log.time}</span>
        <span class="log-level ${log.level}">${levelIcon}</span>
        <span class="log-action">${log.action}</span>
        <span class="log-detail">${detail}</span>
      </div>`;
    }).join("");
    // 自动滚动到底部
    logBody.scrollTop = logBody.scrollHeight;
  }

  // 拉取日志
  async function fetchLogs() {
    try {
      const resp = await fetch("/api/logs");
      const data = await resp.json();
      if (data.ok) renderLogs(data.logs);
    } catch (e) { /* 忽略 */ }
  }

  // 清空日志
  async function clearLogs() {
    try {
      await fetch("/api/logs", { method: "DELETE" });
      renderLogs([]);
    } catch (e) { /* 忽略 */ }
  }

  // 收起/展开
  toggleBtn.addEventListener("click", () => {
    collapsed = !collapsed;
    logBody.classList.toggle("collapsed", collapsed);
    toggleBtn.textContent = collapsed ? "▶ 展开" : "▼ 收起";
  });

  refreshBtn.addEventListener("click", fetchLogs);
  clearBtn.addEventListener("click", clearLogs);

  // 查询完成后自动拉取日志 — 拦截 fetch 响应
  const _origFetch = window.fetch;
  window.fetch = async function(...args) {
    const resp = await _origFetch.apply(this, args);
    const url = typeof args[0] === "string" ? args[0] : (args[0]?.url || "");
    // 查询/登录/环境切换 后自动刷新日志
    if (url.includes("/api/query") || url.includes("/api/login") || url === "/api/env") {
      setTimeout(fetchLogs, 300);
    }
    return resp;
  };

  // 页面加载时获取日志
  fetchLogs();
})();


// ===== 计算器 =====
(function initCalc() {
  const input = $("calcInput");
  const history = $("calcHistory");
  const buttons = $("calcButtons");
  if (!input || !buttons) return;

  let expr = "";
  let records = [];

  function updateDisplay() {
    input.value = expr || "0";
  }

  function addRecord(expression, result) {
    records.push({ expr: expression, result });
    if (records.length > 10) records.shift();
    history.innerHTML = records.map((r) =>
      `<div class="calc-record" title="点击复制结果">${r.expr} = ${r.result}</div>`
    ).join("");
    history.scrollTop = history.scrollHeight;
  }

  function calculate() {
    if (!expr) return;
    try {
      // 安全计算：只允许数字和运算符
      const safe = expr.replace(/[^0-9+\-*/.%()]/g, "");
      if (!safe) return;
      // 处理百分号：转为 /100
      const processed = safe.replace(/(\d+\.?\d*)%/g, "($1/100)");
      const result = Function('"use strict"; return (' + processed + ")")();
      const formatted = Number.isFinite(result) ? parseFloat(result.toPrecision(12)) : "错误";
      addRecord(expr, formatted);
      expr = String(formatted);
      updateDisplay();
    } catch (e) {
      addRecord(expr, "错误");
      expr = "";
      updateDisplay();
    }
  }

  // 按钮点击
  buttons.addEventListener("click", (e) => {
    const btn = e.target.closest(".calc-btn");
    if (!btn) return;
    const val = btn.dataset.val;
    if (val === "C") { expr = ""; updateDisplay(); }
    else if (val === "back") { expr = expr.slice(0, -1); updateDisplay(); }
    else if (val === "=") { calculate(); }
    else { expr += val; updateDisplay(); }
  });

  // 键盘支持
  document.addEventListener("keydown", (e) => {
    // 只在计算器面板打开时响应
    if ($("calcPanel").classList.contains("hidden")) return;
    const key = e.key;
    // Ctrl+V / Cmd+V 粘贴
    if ((e.ctrlKey || e.metaKey) && key === "v") { return; /* 让paste事件处理 */ }
    // Ctrl+C 不拦截（允许复制）
    if ((e.ctrlKey || e.metaKey) && key === "c") { return; }
    if (/[\d+\-*/.%()]/.test(key)) { expr += key; updateDisplay(); e.preventDefault(); }
    else if (key === "Enter" || key === "=") { calculate(); e.preventDefault(); }
    else if (key === "Backspace") { expr = expr.slice(0, -1); updateDisplay(); e.preventDefault(); }
    else if (key === "Escape") { expr = ""; updateDisplay(); e.preventDefault(); }
  });

  // 粘贴支持：Ctrl+V / Cmd+V 粘贴数字到计算器
  document.addEventListener("paste", (e) => {
    if ($("calcPanel").classList.contains("hidden")) return;
    const text = (e.clipboardData || window.clipboardData).getData("text").replace(/\s+/g, "");
    // 只保留数字和运算符
    const clean = text.replace(/[^0-9+\-*/.%()]/g, "");
    if (clean) {
      expr += clean;
      updateDisplay();
      e.preventDefault();
    }
  });

  // 点击历史记录复制结果
  history.addEventListener("click", (e) => {
    const record = e.target.closest(".calc-record");
    if (!record) return;
    const text = record.textContent.split("=").pop().trim();
    navigator.clipboard.writeText(text).then(() => {
      record.style.color = "var(--accent)";
      setTimeout(() => record.style.color = "", 800);
    });
  });

  // 点击输入框复制当前值
  input.addEventListener("click", () => {
    if (expr) {
      navigator.clipboard.writeText(expr).then(() => {
        input.style.borderColor = "var(--accent)";
        setTimeout(() => input.style.borderColor = "", 600);
      });
    }
  });
})();


// ===== 搜索历史记录 =====
(function initSearchHistory() {
  const FIELDS = ["projectName", "projectNo", "tjHoldingSubject", "tjCreditCode"];
  const MAX = 10;
  const STORAGE_KEY = "equity_search_history";

  // 从 localStorage 读取
  function loadHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
    catch (e) { return {}; }
  }
  function saveHistory(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  // 添加搜索记录
  function addToHistory(field, value) {
    if (!value) return;
    const data = loadHistory();
    if (!data[field]) data[field] = [];
    // 去重，移到最前面
    data[field] = data[field].filter(v => v !== value);
    data[field].unshift(value);
    if (data[field].length > MAX) data[field] = data[field].slice(0, MAX);
    saveHistory(data);
  }

  // 渲染下拉列表
  function renderDropdown(field) {
    const dropdown = $("history-" + field);
    const data = loadHistory();
    const list = data[field] || [];
    if (!list.length) {
      dropdown.innerHTML = '<div class="history-empty">暂无搜索记录</div>';
      return;
    }
    dropdown.innerHTML = list.map((v, i) =>
      `<div class="history-item" data-value="${v.replace(/"/g, '&quot;')}">
        <span>${v}</span>
        <span class="history-item-del" data-field="${field}" data-idx="${i}" title="删除">×</span>
      </div>`
    ).join("");
  }

  // 显示/隐藏下拉
  FIELDS.forEach((field) => {
    const icon = document.querySelector(`.history-icon[data-for="${field}"]`);
    const dropdown = $("history-" + field);
    if (!icon || !dropdown) return;

    icon.addEventListener("click", (e) => {
      e.stopPropagation();
      // 关闭其他下拉
      FIELDS.forEach(f => { if (f !== field) $("history-" + f).classList.add("hidden"); });
      dropdown.classList.toggle("hidden");
      if (!dropdown.classList.contains("hidden")) renderDropdown(field);
    });

    // 点击条目填入输入框
    dropdown.addEventListener("click", (e) => {
      const del = e.target.closest(".history-item-del");
      if (del) {
        // 删除某条记录
        const data = loadHistory();
        const idx = parseInt(del.dataset.idx);
        const f = del.dataset.field;
        if (data[f]) { data[f].splice(idx, 1); saveHistory(data); }
        renderDropdown(f);
        e.stopPropagation();
        return;
      }
      const item = e.target.closest(".history-item");
      if (item) {
        $(field).value = item.dataset.value;
        dropdown.classList.add("hidden");
      }
    });
  });

  // 点击外部关闭所有下拉
  document.addEventListener("click", () => {
    FIELDS.forEach(f => $("history-" + f).classList.add("hidden"));
  });

  // 查询时记录搜索历史 — 拦截 /api/query-all 请求
  const _origFetch2 = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === "string" ? args[0] : (args[0]?.url || "");
    if (url.includes("/api/query-all")) {
      FIELDS.forEach(f => {
        const val = $(f).value.replace(/\s+/g, "").trim();
        if (val) addToHistory(f, val);
      });
    }
    return _origFetch2.apply(this, args);
  };
})();

