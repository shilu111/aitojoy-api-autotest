// 股权资产管理 · 四表联查 前端逻辑
const TABLES = window.__TABLES__ || [];
const COLS = {};            // key -> columns
const FREEZE = {};          // key -> 需冻结的前 N 个数据列
TABLES.forEach((t) => { COLS[t.key] = t.columns; FREEZE[t.key] = t.freeze || 0; });

// 每张表的独立状态
const st = {};
TABLES.forEach((t) => (st[t.key] = { pageNo: 1, pageSize: 20, total: 0, records: [], sorts: [] }));
let activeKey = TABLES.length ? TABLES[0].key : null;

const $ = (id) => document.getElementById(id);

function getFilters() {
  return {
    projectName: $("projectName").value.replace(/\s+/g, ""),
    projectNo: $("projectNo").value.replace(/\s+/g, ""),
    tjHoldingSubject: $("tjHoldingSubject").value.replace(/\s+/g, ""),
    tjCreditCode: $("tjCreditCode").value.replace(/\s+/g, ""),
  };
}

// 粘贴时自动去空格（不影响中文输入法）
["projectName", "projectNo", "tjHoldingSubject", "tjCreditCode"].forEach((id) => {
  $(id).addEventListener("paste", (e) => {
    e.preventDefault();
    const text = (e.clipboardData || window.clipboardData).getData("text").replace(/\s+/g, "");
    document.execCommand("insertText", false, text);
  });
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function fmtCell(value, type, field, label) {
  if (value === null || value === undefined || value === "") return "-";
  if (type === "label") return value && value.label ? value.label : (typeof value === "object" ? "-" : value);
  if (type === "date" || type === "month") {
    const s = String(value);
    if (/^\d{10,13}$/.test(s)) {
      const d = new Date(Number(s));
      const p = (x) => String(x).padStart(2, "0");
      if (type === "month") return `${d.getFullYear()}-${p(d.getMonth() + 1)}`;
      // 创建时间、更新时间保留时分秒，其他日期只显示年月日
      const isTimestamp = field && (field.includes("create_time") || field.includes("update_time"));
      if (isTimestamp) {
        return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
      }
      return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
    }
    return s;
  }
  if (type === "number") {
    const n = Number(value);
    if (isNaN(n)) return value;
    if (n === 0) return 0;
    // 月度/历史表中 time_point_* 和 end_period_* 字段保留6位小数
    if (field && (field.startsWith("time_point_") || field.startsWith("end_period_"))) {
      return n.toFixed(6);
    }
    // 对赌表：股权比例字段加%
    if (field && (field === "basic_stock_rate" || field === "confirmation_stock_rate" ||
        field === "should_confirmation_stock_rate" || field === "complete_gambling_shareholding_ratio")) {
      return n + "%";
    }
    // 台账表：带（万元）保留6位小数，带（元）保留2位小数，带（%）拼上%
    if (label) {
      if (label.includes("（万元）")) return n.toFixed(6);
      if (label.includes("（元）")) return n.toFixed(2);
      if (label.includes("（%）")) return n + "%";
    }
    return n;
  }
  return typeof value === "object" ? JSON.stringify(value) : value;
}

function renderTable(key) {
  const cols = COLS[key];
  const s = st[key];
  const body = $("body-" + key);

  // 前端排序：如果有排序条件，对当前页数据排序
  let records = s.records;
  if (s.sorts && s.sorts.length) {
    const sortField = s.sorts[0].field;
    const sortOrder = s.sorts[0].order;
    records = [...records].sort((a, b) => {
      const va = a[sortField], vb = b[sortField];
      // 数值/时间戳比较
      const na = Number(va), nb = Number(vb);
      if (!isNaN(na) && !isNaN(nb)) {
        return sortOrder === "ASC" ? na - nb : nb - na;
      }
      // 字符串比较
      const sa = String(va || ""), sb = String(vb || "");
      return sortOrder === "ASC" ? sa.localeCompare(sb) : sb.localeCompare(sa);
    });
  }

  if (!records.length) {
    body.innerHTML = `<tr class="empty-row"><td colspan="${cols.length + 1}">暂无数据</td></tr>`;
  } else {
    const start = (s.pageNo - 1) * s.pageSize;
    body.innerHTML = records.map((r, i) => {
      const tds = cols.map((c) => {
        const v = escapeHtml(fmtCell(r[c.field], c.type, c.field, c.label));
        return `<td data-field="${c.field}" title="${v}">${v}</td>`;
      }).join("");
      const rowId = r.id || "";
      return `<tr data-record-id="${rowId}"><td class="idx">${start + i + 1}</td>${tds}</tr>`;
    }).join("");
  }
  const totalPages = Math.max(1, Math.ceil(s.total / s.pageSize));
  $("pageinfo-" + key).textContent = `第 ${s.pageNo} / ${totalPages} 页`;
  $("badge-" + key).textContent = s.total;
  applyFreeze(key);
  applyColVisibility(key);
}

// 冻结左侧列：横向滚动时固定 # 序号 + 前 freeze 个标识列
function applyFreeze(key) {
  const panel = $("panel-" + key);
  if (!panel) return;
  const table = panel.querySelector("table");
  if (!table) return;
  const frozenCount = (FREEZE[key] || 0) + 1; // +1 含 # 序号列

  // 用 tbody 第一行的实际列宽计算偏移（最可靠，不受双表头 rowspan 影响）
  const refRow = table.querySelector("tbody tr:not(.empty-row)") || table.querySelector("thead tr:last-child");
  if (!refRow) return;
  const refCells = refRow.children;
  if (refCells.length < frozenCount) return;

  const offsets = [];
  let acc = 0;
  for (let i = 0; i < frozenCount && i < refCells.length; i++) {
    offsets[i] = acc;
    acc += refCells[i].getBoundingClientRect().width;
  }

  // 对 group-header 行：冻结 # 列（rowspan 的 .idx 单元格）
  const groupRow = table.querySelector("tr.group-header");
  if (groupRow) {
    const idxCell = groupRow.querySelector("th.idx");
    if (idxCell) { idxCell.classList.add("frozen"); idxCell.style.left = "0px"; idxCell.style.zIndex = "4"; }
  }

  // 对字段名行和数据行应用冻结
  table.querySelectorAll("tr:not(.group-header)").forEach((tr) => {
    const cells = tr.children;
    // 双表头的字段名行没有 # 列（被 rowspan 跨了），所以它只有 N-1 个需要冻结
    const isFieldRow = tr.closest("thead") && groupRow;
    const count = isFieldRow ? frozenCount - 1 : frozenCount;

    for (let i = 0; i < cells.length; i++) {
      const c = cells[i];
      if (i < count) {
        c.classList.add("frozen");
        // 字段行偏移从 offsets[1] 开始（跳过 # 列宽度）
        c.style.left = (isFieldRow ? offsets[i + 1] : offsets[i]) + "px";
        c.classList.toggle("frozen-edge", i === count - 1);
      } else {
        c.classList.remove("frozen", "frozen-edge");
        c.style.left = "";
      }
    }
  });
}

function setStatus(msg, cls = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = "status " + cls;
}

// 查询四张表
async function queryAll() {
  setStatus("四张表查询中…");
  $("queryBtn").disabled = true;
  // 清除高级功能的高亮标记
  const mBody = $("body-monthly");
  if (mBody) {
    mBody.querySelectorAll(".adv-row-highlight").forEach((r) => r.classList.remove("adv-row-highlight"));
    mBody.querySelectorAll(".adv-cell-highlight").forEach((c) => c.classList.remove("adv-cell-highlight"));
    mBody.querySelectorAll(".adv-cell-mismatch").forEach((c) => c.classList.remove("adv-cell-mismatch"));
  }
  TABLES.forEach((t) => (st[t.key].pageNo = 1));
  // 收集各表排序参数
  const sortsMap = {};
  TABLES.forEach((t) => { if (st[t.key].sorts.length) sortsMap[t.key] = st[t.key].sorts; });
  try {
    const resp = await fetch("/api/query-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filters: getFilters(), pageSize: st[activeKey].pageSize, sorts: sortsMap }),
    });
    const data = await resp.json();
    if (!data.ok) { setStatus(data.msg || "查询失败", "error"); return; }
    let summary = [];
    TABLES.forEach((t) => {
      const r = data.tables[t.key] || {};
      st[t.key].total = r.total || 0;
      st[t.key].records = r.records || [];
      renderTable(t.key);
      summary.push(`${t.name} ${r.ok ? r.total : "失败"}`);
    });
    setStatus("查询完成：" + summary.join(" | "), "ok");
  } catch (e) {
    setStatus("请求异常：" + e.message, "error");
  } finally {
    $("queryBtn").disabled = false;
  }
}

// 单表翻页/改每页条数
async function queryOne(key) {
  const s = st[key];
  setStatus("加载中…");
  try {
    const resp = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ table: key, filters: getFilters(), pageNo: s.pageNo, pageSize: s.pageSize, sorts: s.sorts }),
    });
    const r = await resp.json();
    if (!r.ok) { setStatus(r.msg || "查询失败", "error"); return; }
    s.total = r.total; s.records = r.records;
    renderTable(key);
    setStatus("已更新 " + tableName(key), "ok");
  } catch (e) {
    setStatus("请求异常：" + e.message, "error");
  }
}

function tableName(key) {
  const t = TABLES.find((x) => x.key === key);
  return t ? t.name : key;
}

function switchTab(key) {
  activeKey = key;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.key === key));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("hidden", p.id !== "panel-" + key));
  // 切到可见后重算冻结列偏移（隐藏时宽度为 0 无法计算）
  applyFreeze(key);
  // 更新导出按钮文字
  $("exportBtn").textContent = "导出" + tableName(key);
  // 更新导入按钮文字
  const importBtn = $("importToggleBtn");
  if (importBtn) importBtn.textContent = "📥 导入" + tableName(key);
  // 切换tab时收起导入面板并重置状态
  const importSection = $("importSection");
  if (importSection) {
    importSection.classList.add("hidden");
    // 重置导入状态文字和详情
    const importStatus = $("importStatus");
    if (importStatus) {
      importStatus.textContent = "";
      importStatus.className = "status";
    }
    const importStatusWrap = $("importStatusWrap");
    if (importStatusWrap) importStatusWrap.innerHTML = "";
    // 重置进度条
    const progressWrap = $("importProgress");
    if (progressWrap) progressWrap.classList.add("hidden");
    // 清除已选文件
    const fileNameEl = $("importFileName");
    const fileInput = $("importFileInput");
    const uploadBtn = $("importUploadBtn");
    const fileRemoveBtn = $("importFileRemove");
    if (fileNameEl) { fileNameEl.textContent = "未选择文件"; fileNameEl.classList.remove("has-file"); }
    if (fileInput) fileInput.value = "";
    if (uploadBtn) uploadBtn.disabled = true;
    if (fileRemoveBtn) fileRemoveBtn.style.display = "none";
  }
  // 切换tab后滚动到页面顶部
  window.scrollTo(0, 0);
}

function exportCsv() {
  const key = activeKey;
  const s = st[key], cols = COLS[key];
  if (!s.records.length) { setStatus("当前表无数据可导出", "error"); return; }

  // 台账表：按导入模板格式导出 xlsx（支持生产导出→测试导入场景）
  if (key === "ledger") {
    exportLedgerImportFormat(s.records);
    return;
  }

  // 天九持股主体表：按导入模板格式导出
  if (key === "holding_subject") {
    exportHoldingSubjectFormat(s.records);
    return;
  }

  // 股权历史表：按导入模板格式导出
  if (key === "history") {
    exportHistoryFormat(s.records);
    return;
  }

  const header = cols.map((c) => c.label).join(",");
  const rows = s.records.map((r) =>
    cols.map((c) => `"${String(fmtCell(r[c.field], c.type, c.field, c.label)).replace(/"/g, '""')}"`).join(",")
  );
  const csv = "\uFEFF" + [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${tableName(key)}-${getEnvLabel()}_第${s.pageNo}页.csv`;
  a.click();
  setStatus("已导出", "ok");
}

// 获取当前环境标签（用于导出文件名）
function getEnvLabel() {
  const toggle = $("envToggle");
  return (toggle && toggle.checked) ? "生产" : "测试";
}

// 台账表：按导入模板格式导出 xlsx（生产/测试均可，导出后可直接导入测试环境）
async function exportLedgerImportFormat(records) {
  setStatus("正在导出导入格式…", "");
  try {
    const resp = await fetch("/api/export/ledger-import-format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records }),
    });
    if (!resp.ok) {
      // 尝试解析 JSON 错误信息，如果后端返回非 JSON 则用 text
      let msg = "导出失败";
      const contentType = resp.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await resp.json();
        msg = data.msg || msg;
      } else {
        msg = `服务器错误 (HTTP ${resp.status})`;
      }
      setStatus(msg, "error");
      return;
    }
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    // 文件名：导出台账-年月日时分.xlsx
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const dateStr = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}`;
    a.download = `导出台账-${getEnvLabel()}-${dateStr}.xlsx`;
    a.click();
    setStatus("已导出（可直接用于导入台账）", "ok");
  } catch (e) {
    setStatus("导出异常：" + e.message, "error");
  }
}

// 天九持股主体表：按导入模板格式导出 xlsx
async function exportHoldingSubjectFormat(records) {
  setStatus("正在导出…", "");
  try {
    const resp = await fetch("/api/export/holding-subject-format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records }),
    });
    if (!resp.ok) {
      let msg = "导出失败";
      const contentType = resp.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await resp.json();
        msg = data.msg || msg;
      } else {
        msg = `服务器错误 (HTTP ${resp.status})`;
      }
      setStatus(msg, "error");
      return;
    }
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const dateStr = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}`;
    a.download = `导出天九持股主体-${getEnvLabel()}-${dateStr}.xlsx`;
    a.click();
    setStatus("已导出（可直接用于导入）", "ok");
  } catch (e) {
    setStatus("导出异常：" + e.message, "error");
  }
}

// 股权历史表：按导入模板格式导出 xlsx
async function exportHistoryFormat(records) {
  setStatus("正在导出…", "");
  try {
    const resp = await fetch("/api/export/history-format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records }),
    });
    if (!resp.ok) {
      let msg = "导出失败";
      const contentType = resp.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await resp.json();
        msg = data.msg || msg;
      } else {
        msg = `服务器错误 (HTTP ${resp.status})`;
      }
      setStatus(msg, "error");
      return;
    }
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const dateStr = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}`;
    a.download = `导出股权历史-${getEnvLabel()}-${dateStr}.xlsx`;
    a.click();
    setStatus("已导出（可直接用于导入）", "ok");
  } catch (e) {
    setStatus("导出异常：" + e.message, "error");
  }
}

// ===== 事件绑定 =====
// 登录
$("loginBtn").addEventListener("click", async () => {
  const mobile = "13622034186";
  const password = "daming123";
  $("loginBtn").disabled = true;
  $("loginStatus").textContent = "登录中…";
  try {
    const resp = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile, password }),
    });
    const data = await resp.json();
    if (data.ok) {
      setLoggedIn(true);
    } else {
      $("loginStatus").textContent = "❌ " + (data.msg || "登录失败");
      $("loginStatus").style.color = "#ff7a90";
    }
  } catch (e) {
    $("loginStatus").textContent = "❌ " + e.message;
    $("loginStatus").style.color = "#ff7a90";
  } finally {
    $("loginBtn").disabled = false;
  }
});

// ===== 登录状态管理 =====
let isLoggedIn = false;

function setLoggedIn(val) {
  isLoggedIn = val;
  if (val) {
    $("loginBtn").classList.add("hidden");
    $("loginStatus").textContent = "✅ 已登录";
    $("loginStatus").style.color = "var(--accent)";
    $("loginInfoField").classList.remove("hidden");
  } else {
    $("loginBtn").classList.remove("hidden");
    $("loginStatus").textContent = "未登录";
    $("loginStatus").style.color = "#ffc107";
    $("loginInfoField").classList.add("hidden");
  }
}

// 自动检查/恢复登录状态
async function autoCheckLogin() {
  try {
    const resp = await fetch("/api/auth/status");
    const data = await resp.json();
    if (data.ok && data.loggedIn) {
      setLoggedIn(true);
      return;
    }
    // token 无效，尝试自动登录
    $("loginStatus").textContent = "自动登录中…";
    $("loginStatus").style.color = "var(--muted)";
    const loginResp = await fetch("/api/auth/auto-login", { method: "POST" });
    const loginData = await loginResp.json();
    if (loginData.ok) {
      setLoggedIn(true);
    } else {
      setLoggedIn(false);
    }
  } catch (e) {
    setLoggedIn(false);
  }
}

function checkLogin(action) {
  if (!isLoggedIn) {
    setStatus("请先点击「登录」按钮", "error");
    $("loginBtn").classList.add("login-btn-pulse");
    setTimeout(() => $("loginBtn").classList.remove("login-btn-pulse"), 1500);
    return false;
  }
  return true;
}

$("queryBtn").addEventListener("click", () => { if (checkLogin()) queryAll(); });
$("resetBtn").addEventListener("click", () => {
  if (!checkLogin()) return;
  $("projectName").value = ""; $("projectNo").value = ""; $("tjHoldingSubject").value = ""; $("tjCreditCode").value = "";
  queryAll();
});
$("exportBtn").addEventListener("click", () => { if (checkLogin()) exportCsv(); });

// 页面加载时自动检查登录状态
autoCheckLogin();

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.key)));

document.querySelectorAll("[data-page]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!checkLogin()) return;
    const key = btn.dataset.key, s = st[key];
    const totalPages = Math.max(1, Math.ceil(s.total / s.pageSize));
    if (btn.dataset.page === "prev" && s.pageNo > 1) s.pageNo--;
    else if (btn.dataset.page === "next" && s.pageNo < totalPages) s.pageNo++;
    else return;
    queryOne(key);
  });
});

document.querySelectorAll(".pageSize").forEach((sel) => {
  sel.addEventListener("change", (e) => {
    if (!checkLogin()) { e.target.value = st[sel.dataset.key].pageSize; return; }
    const key = sel.dataset.key;
    st[key].pageSize = Number(e.target.value);
    st[key].pageNo = 1;
    queryOne(key);
  });
});

// 窗口尺寸变化时，重算当前表的冻结列偏移
window.addEventListener("resize", () => { if (activeKey) applyFreeze(activeKey); });

// 表格滚轮速度提升
document.querySelectorAll(".table-wrap").forEach((wrap) => {
  wrap.addEventListener("wheel", (e) => {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      wrap.scrollTop += e.deltaY * 3;
      e.preventDefault();
    }
  }, { passive: false });
});

// ===== 表格单元格双击复制 =====
function copyText(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;top:-9999px;left:-9999px;opacity:0;";
  document.body.appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  document.execCommand("copy");
  document.body.removeChild(ta);
}
document.querySelectorAll(".table-wrap").forEach((wrap) => {
  wrap.addEventListener("dblclick", (e) => {
    const td = e.target.closest("td:not(.idx)");
    if (!td) return;
    const text = td.textContent.trim();
    if (!text || text === "-") return;
    window.getSelection().removeAllRanges();
    copyText(text);
    td.classList.add("td-copied");
    setTimeout(() => td.classList.remove("td-copied"), 600);
  });
});

// ===== 排序点击 =====
document.querySelectorAll("th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const field = th.dataset.field;
    const tableKey = th.dataset.table;
    const s = st[tableKey];
    // 排序三态切换：无 -> DESC -> ASC -> 无
    const existing = s.sorts.find(x => x.field === field);
    if (!existing) {
      s.sorts = [{ field, order: "DESC" }];
    } else if (existing.order === "DESC") {
      s.sorts = [{ field, order: "ASC" }];
    } else {
      s.sorts = [];
    }
    // 更新图标状态并重新渲染
    updateSortIcons(tableKey);
    renderTable(tableKey);
  });
});

function updateSortIcons(key) {
  const panel = $("panel-" + key);
  if (!panel) return;
  const s = st[key];
  panel.querySelectorAll("th.sortable").forEach((th) => {
    const field = th.dataset.field;
    const sort = s.sorts.find(x => x.field === field);
    const icon = th.querySelector(".sort-icon");
    th.classList.remove("sort-asc", "sort-desc");
    if (sort && sort.order === "ASC") {
      th.classList.add("sort-asc");
      if (icon) icon.textContent = "↑";
    } else if (sort && sort.order === "DESC") {
      th.classList.add("sort-desc");
      if (icon) icon.textContent = "↓";
    } else {
      if (icon) icon.textContent = "⇅";
    }
  });
}

// ===== 列显隐控制 =====
// hiddenCols[key] = Set of hidden column indices
const hiddenCols = {};
TABLES.forEach((t) => {
  hiddenCols[t.key] = new Set();
  t.columns.forEach((c, i) => { if (c.hidden) hiddenCols[t.key].add(i); });
});

function buildColPanel(key) {
  const body = $("colPanelBody");
  const cols = COLS[key];
  const hidden = hiddenCols[key];
  const allChecked = hidden.size === 0;
  // 全选行
  let html = `<label class="col-check col-check-all"><input type="checkbox" id="colSelectAll" ${allChecked ? "checked" : ""}/><span>全选</span><span style="margin-left:auto;color:var(--muted);font-size:12px;">字段名称</span></label>`;
  html += cols.map((c, i) => {
    const checked = !hidden.has(i) ? "checked" : "";
    return `<label class="col-check"><input type="checkbox" data-idx="${i}" ${checked}/>${c.label}</label>`;
  }).join("");
  body.innerHTML = html;
}

function applyColVisibility(key) {
  const hidden = hiddenCols[key];
  const panel = $("panel-" + key);
  if (!panel) return;
  const table = panel.querySelector("table");
  if (!table) return;
  const cols = COLS[key];

  // 1. 隐藏/显示数据行（tbody）的单元格：cells[0] 是 #，数据从 cells[1] 开始
  table.querySelectorAll("tbody tr").forEach((tr) => {
    const cells = tr.children;
    for (let i = 1; i < cells.length; i++) {
      cells[i].style.display = hidden.has(i - 1) ? "none" : "";
    }
  });

  // 2. 处理字段名行（thead 最后一个 tr，不是 group-header）
  const headRows = table.querySelectorAll("thead tr");
  const groupRow = table.querySelector("tr.group-header");
  const fieldRow = headRows.length > 1 && groupRow ? headRows[headRows.length - 1] : headRows[0];
  if (fieldRow && !fieldRow.classList.contains("group-header")) {
    const cells = fieldRow.children;
    // 如果有 group-header（双表头），字段行没有 # 列，索引从 0 开始直接对应列
    // 如果是单表头，cells[0] 是 #，数据从 cells[1] 开始
    const offset = groupRow ? 0 : 1;
    for (let i = 0; i < cols.length; i++) {
      const cell = cells[i + offset];
      if (cell) cell.style.display = hidden.has(i) ? "none" : "";
    }
  }

  // 3. 更新 group-header 的 colspan（只对有分组的表）
  if (groupRow) {
    const groupCells = [...groupRow.querySelectorAll("th.group-th")];
    const groupNames = [];
    let prev = "";
    cols.forEach((c) => { if (c.group !== prev) { groupNames.push(c.group); prev = c.group; } });
    groupNames.forEach((g, gi) => {
      const visCount = cols.filter((c, ci) => c.group === g && !hidden.has(ci)).length;
      if (groupCells[gi]) {
        groupCells[gi].setAttribute("colspan", Math.max(visCount, 1));
        groupCells[gi].style.display = visCount === 0 ? "none" : "";
      }
    });
  }
}



// ===== 查询栏 sticky 阴影效果 =====
(function() {
  const queryCard = document.querySelector(".query-card");
  if (!queryCard) return;
  const observer = new IntersectionObserver(
    ([e]) => queryCard.classList.toggle("is-stuck", e.intersectionRatio < 1),
    { threshold: [1], rootMargin: "-1px 0px 0px 0px" }
  );
  observer.observe(queryCard);
})();
