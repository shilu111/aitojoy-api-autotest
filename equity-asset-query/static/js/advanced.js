// ===== 高级功能弹窗 =====
// 保存上次选择的下拉值，用于重新打开时回显
let _lastAdvLedgerSelectValue = "";

$("advancedBtn").addEventListener("click", () => {
  $("advancedModal").classList.remove("hidden");
  // 用台账表已查询的数据填充下拉选择框
  populateAdvLedgerSelect();
  // 回显上次选择的值
  const sel = $("advLedgerSelect");
  if (sel && _lastAdvLedgerSelectValue) {
    sel.value = _lastAdvLedgerSelectValue;
  }
});
$("advancedModalClose").addEventListener("click", () => {
  $("advancedModal").classList.add("hidden");
});
$("advancedModal").addEventListener("click", (e) => {
  if (e.target === $("advancedModal")) $("advancedModal").classList.add("hidden");
});

// 子模块折叠/展开
document.querySelectorAll(".adv-module-header").forEach((header) => {
  header.addEventListener("click", () => {
    const targetId = header.dataset.toggle;
    const body = $(targetId);
    const arrow = $(targetId + "Arrow");
    if (body) body.classList.toggle("collapsed");
    if (arrow) arrow.classList.toggle("collapsed");
  });
});

// ===== 高级功能：股权登记比例计算 =====

// 用台账表已查询的数据填充下拉选择框（过滤：体系内 + 工商变更日期 > 2024-12-31）
function populateAdvLedgerSelect() {
  const sel = $("advLedgerSelect");
  if (!sel) return;
  const records = st.ledger ? st.ledger.records : [];
  let html = '<option value="">-- 请先查询台账表，然后选择一条记录 --</option>';
  if (!records.length) {
    html = '<option value="">-- 台账表暂无数据，请先查询 --</option>';
  } else {
    let count = 0;
    records.forEach((r, i) => {
      // 过滤条件1：天九持股主体体系 = 体系内
      const sysType = r.system_type;
      const sysLabel = (typeof sysType === "object" && sysType) ? (sysType.label || "") : (sysType || "");
      if (sysLabel !== "体系内") return;

      // 过滤条件2：工商变更日期 > 2024-12-31
      const dateRaw = r.date_0f5998;
      if (!dateRaw) return;
      let dateStr = "";
      const s = String(dateRaw);
      if (/^\d{10,13}$/.test(s)) {
        const d = new Date(Number(s));
        const p = (x) => String(x).padStart(2, "0");
        dateStr = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
      } else if (s.length >= 10 && s.includes("-")) {
        dateStr = s.slice(0, 10);
      }
      if (!dateStr || dateStr <= "2024-12-31") return;

      const no = r.input_36c323 || "-";
      const name = r.input_c31c2bm03734eb || "-";
      const holdSubject = r.input_195656m037hs3h || "-";
      const seq = r.number_8e6771 != null ? r.number_8e6771 : "-";
      // 股权变更方式（select_fa5c4a）
      const changeTypeRaw = r.select_fa5c4a;
      const changeType = (typeof changeTypeRaw === "object" && changeTypeRaw) ? (changeTypeRaw.label || "-") : (changeTypeRaw || "-");
      html += `<option value="${i}">序号:${seq} | ${name}(${no}) | ${holdSubject} | ${changeType} | 工商变更:${dateStr}</option>`;
      count++;
    });
    if (count === 0) {
      html = '<option value="">-- 无符合条件的记录（需体系内 + 工商变更日期>2024-12-31）--</option>';
    }
  }
  sel.innerHTML = html;
  // 动态调整 size：无数据时紧凑，有数据时展开（最大10行）
  const optCount = sel.options.length;
  sel.size = Math.min(Math.max(optCount, 2), 10);
}

// 下拉选择台账记录后自动填充四要素 + 工商变更日期
document.addEventListener("change", (e) => {
  if (e.target.id !== "advLedgerSelect") return;
  const idx = e.target.value;
  // 保存选择值，用于下次打开弹窗时回显
  _lastAdvLedgerSelectValue = idx;
  if (idx === "" || !st.ledger) return;
  const r = st.ledger.records[Number(idx)];
  if (!r) return;
  // 填充四要素
  $("advProjectNo").value = r.input_36c323 || "";
  $("advProjectCompanyUscc").value = r.project_company_main_uscc || "";
  $("advHoldingSubjectUscc").value = r.input_2c2b00_uscc || "";
  $("advAgreementCompanyUscc").value = r.agreement_subject_company_uscc || "";
  // 填充工商变更日期
  const dateRaw = r.date_0f5998;
  if (dateRaw) {
    const s = String(dateRaw);
    if (/^\d{10,13}$/.test(s)) {
      const d = new Date(Number(s));
      const p = (x) => String(x).padStart(2, "0");
      $("advBizChangeDate").value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
    } else {
      $("advBizChangeDate").value = s.slice(0, 10);
    }
  } else {
    $("advBizChangeDate").value = "";
  }
});

(function initAdvancedCalc() {
  const calcBtn = $("advCalcBtn");
  const resetBtn = $("advResetBtn");
  const statusEl = $("advStatus");
  const resultWrap = $("advResult");
  const resultBody = $("advResultBody");

  if (!calcBtn) return;

  function setAdvStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className = "status " + (cls || "");
  }

  resetBtn.addEventListener("click", () => {
    $("advProjectNo").value = "";
    $("advProjectCompanyUscc").value = "";
    $("advHoldingSubjectUscc").value = "";
    $("advAgreementCompanyUscc").value = "";
    $("advBizChangeDate").value = "";
    setAdvStatus("", "");
    resultWrap.classList.add("hidden");
    resultBody.innerHTML = "";
  });

  calcBtn.addEventListener("click", async () => {
    if (!checkLogin()) return;

    const params = {
      projectNo: $("advProjectNo").value.replace(/\s+/g, ""),
      projectCompanyUscc: $("advProjectCompanyUscc").value.replace(/\s+/g, ""),
      holdingSubjectUscc: $("advHoldingSubjectUscc").value.replace(/\s+/g, ""),
      agreementCompanyUscc: $("advAgreementCompanyUscc").value.replace(/\s+/g, ""),
      bizChangeDate: $("advBizChangeDate").value,
    };

    // 前端校验
    const missing = [];
    if (!params.projectNo) missing.push("项目编号");
    if (!params.projectCompanyUscc) missing.push("项目公司主体统一社会信用代码");
    if (!params.holdingSubjectUscc) missing.push("持股主体统一社会信用代码");
    if (!params.agreementCompanyUscc) missing.push("协议标的公司统一社会信用代码");
    if (!params.bizChangeDate) missing.push("工商变更日期");
    if (missing.length) {
      setAdvStatus("缺少：" + missing.join("、"), "error");
      return;
    }

    setAdvStatus("计算中…", "");
    calcBtn.disabled = true;
    resultWrap.classList.add("hidden");

    try {
      const resp = await fetch("/api/advanced/equity-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await resp.json();

      if (!data.ok) {
        setAdvStatus(data.msg || "计算失败", "error");
        resultWrap.classList.add("hidden");
        return;
      }

      setAdvStatus("计算完成", "ok");
      resultWrap.classList.remove("hidden");
      renderAdvResult(data);

      // 判断是否不一致（标红）
      const isMismatch = data.verification && data.verification.match === false;
      // 期末计算是否不一致
      const isEndMismatch = data.endPeriodCalc && data.endPeriodCalc.match === false;

      // 高亮月度表中匹配的行
      clearMonthlyHighlight();
      if (data.monthly && data.monthly.recordId) {
        const highlightField = data.monthlyField || "time_point_stock_register";
        // 确定期末字段名
        const endFieldMap = {
          "time_point_stock_register": "end_period_stock_register",
          "time_point_stock_return": "end_period_stock_return",
          "time_point_stock_disposal": "end_period_stock_disposal",
        };
        const endField = endFieldMap[highlightField] || null;
        // 先尝试在已有数据中高亮
        const found = tryHighlight(data.monthly.recordId, highlightField, isMismatch, endField, isEndMismatch);
        if (!found) {
          // 月度表中没有这条数据（可能未查询或分页外），自动查询月度表后再高亮
          await loadMonthlyAndHighlight(params, data.monthly.recordId, highlightField, isMismatch, endField, isEndMismatch);
        }
      }

      // 计算完成后关闭弹窗
      $("advancedModal").classList.add("hidden");
    } catch (e) {
      setAdvStatus("请求异常：" + e.message, "error");
    } finally {
      calcBtn.disabled = false;
    }
  });

  function renderAdvResult(data) {
    const { ledger, calcResult, monthly, verification, calcType, monthlyFieldLabel, endPeriodCalc } = data;
    let html = "";

    // 台账信息
    html += `<div class="adv-info-block">
      <div class="adv-info-title"><span class="adv-icon adv-icon-info"></span>台账匹配信息</div>
      <div class="adv-info-grid">
        <span class="adv-kv"><b>项目编号：</b>${ledger.projectNo}</span>
        <span class="adv-kv"><b>股权价值变动方式：</b>${ledger.changeType}</span>
        <span class="adv-kv"><b>持股类型：</b>${ledger.holdingType}</span>
        <span class="adv-kv"><b>工商变更日期：</b>${ledger.bizChangeDate}</span>
        <span class="adv-kv"><b>工商变更比例：</b>${ledger.bizChangeRatio != null ? ledger.bizChangeRatio + "%" : "-"}</span>
        <span class="adv-kv"><b>协议标的持有最终标的股权：</b>${ledger.agreementHoldUltimate != null ? ledger.agreementHoldUltimate + "%" : "-"}</span>
      </div>
    </div>`;

    // 计算结果（高亮显示）
    html += `<div class="adv-info-block adv-highlight">
      <div class="adv-info-title"><span class="adv-icon adv-icon-calc"></span>${calcType || "计算"}结果</div>
      <div class="adv-result-value">${calcResult.equityValue != null ? calcResult.equityValue : "无法计算"}</div>
      <div class="adv-formula">${calcResult.formula}</div>
    </div>`;

    // ===== 月度表校验区（统一风格） =====
    html += `<div class="adv-info-block adv-monthly-section">
      <div class="adv-info-title"><span class="adv-icon adv-icon-check"></span>月度表校验</div>`;

    // 时点校验
    html += `<div class="adv-sub-section">
      <div class="adv-sub-title">① 时点校验（${monthlyFieldLabel || ""}）</div>`;
    if (monthly && monthly.statisticsMonth) {
      html += `<div class="adv-info-grid">
        <span class="adv-kv"><b>统计月：</b>${monthly.statisticsMonth}</span>
        <span class="adv-kv"><b>月度表${monthlyFieldLabel || ""}：</b>${monthly.currentValue != null ? monthly.currentValue : "空"}</span>
        <span class="adv-kv"><b>计算值：</b>${calcResult.equityValue != null ? calcResult.equityValue : "-"}</span>
      </div>`;
    } else if (monthly && monthly.msg) {
      html += `<div class="adv-kv" style="color:var(--muted);">${monthly.msg}</div>`;
    }
    if (verification) {
      const vCls = verification.match === true ? "adv-verify-ok" : (verification.match === false ? "adv-verify-fail" : "adv-verify-warn");
      html += `<div class="adv-verify ${vCls}">${verification.msg}</div>`;
    }
    html += `</div>`;

    // 期末校验
    if (endPeriodCalc) {
      html += `<div class="adv-sub-section">
        <div class="adv-sub-title">② 期末校验（${endPeriodCalc.label || ""}）</div>`;
      if (endPeriodCalc.formula) {
        html += `<div class="adv-info-grid">
          <span class="adv-kv"><b>上月期末值：</b>${endPeriodCalc.prevEndValue != null ? endPeriodCalc.prevEndValue : "-"}<span class="adv-tag">${endPeriodCalc.prevMonth || ""}</span></span>
          <span class="adv-kv"><b>当月时点值：</b>${endPeriodCalc.currentTimeValue != null ? endPeriodCalc.currentTimeValue : "-"}</span>
          <span class="adv-kv"><b>计算期末值：</b>${endPeriodCalc.calcEndValue != null ? endPeriodCalc.calcEndValue : "-"}</span>
          <span class="adv-kv"><b>月度表期末值：</b>${endPeriodCalc.actualEndValue != null ? endPeriodCalc.actualEndValue : "空"}</span>
        </div>`;
        html += `<div class="adv-formula">${endPeriodCalc.formula}</div>`;
      }
      if (endPeriodCalc.msg) {
        const epCls = endPeriodCalc.match === true ? "adv-verify-ok" : (endPeriodCalc.match === false ? "adv-verify-fail" : "adv-verify-warn");
        html += `<div class="adv-verify ${epCls}">${endPeriodCalc.msg}</div>`;
      }
      html += `</div>`;
    }

    html += `</div>`; // 关闭月度表校验区

    resultBody.innerHTML = html;
  }

  // 尝试在已渲染的月度表中高亮指定行，返回是否成功
  function tryHighlight(recordId, fieldName, isMismatch, endField, isEndMismatch) {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return false;
    const rows = monthlyBody.querySelectorAll("tr[data-record-id]");
    for (const row of rows) {
      if (row.dataset.recordId === String(recordId)) {
        row.classList.add("adv-row-highlight");
        // 根据计算类型高亮对应时点字段
        const targetCell = row.querySelector(`td[data-field="${fieldName}"]`);
        if (targetCell) {
          if (isMismatch) {
            targetCell.classList.add("adv-cell-mismatch");
          } else {
            targetCell.classList.add("adv-cell-highlight");
          }
        }
        // 高亮期末字段
        if (endField) {
          const endCell = row.querySelector(`td[data-field="${endField}"]`);
          if (endCell) {
            if (isEndMismatch) {
              endCell.classList.add("adv-cell-mismatch");
            } else {
              endCell.classList.add("adv-cell-highlight");
            }
          }
        }
        switchTab("monthly");
        setTimeout(() => row.scrollIntoView({ behavior: "smooth", block: "center" }), 200);
        return true;
      }
    }
    return false;
  }

  // 查月度表（用四要素），加载数据后高亮
  async function loadMonthlyAndHighlight(params, recordId, fieldName, isMismatch, endField, isEndMismatch) {
    // 用高级功能的四要素条件查月度表
    const filters = {
      projectNo: params.projectNo,
      tjCreditCode: params.holdingSubjectUscc,
    };
    try {
      const resp = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table: "monthly", filters, pageNo: 1, pageSize: 100, sorts: [] }),
      });
      const r = await resp.json();
      if (r.ok) {
        st.monthly.total = r.total;
        st.monthly.records = r.records;
        st.monthly.pageNo = 1;
        renderTable("monthly");
        $("badge-monthly").textContent = r.total;
        // 切到月度表 Tab
        switchTab("monthly");
        // 等渲染完成后高亮
        setTimeout(() => tryHighlight(recordId, fieldName, isMismatch, endField, isEndMismatch), 100);
      }
    } catch (e) {
      // 忽略，只是高亮失败
    }
  }

  // 清除月度表高亮
  function clearMonthlyHighlight() {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return;
    monthlyBody.querySelectorAll(".adv-row-highlight").forEach((r) => r.classList.remove("adv-row-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-highlight").forEach((c) => c.classList.remove("adv-cell-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-mismatch").forEach((c) => c.classList.remove("adv-cell-mismatch"));
  }
})();

// ===== 高级功能：项目对赌计算 =====
(function initVamCalc() {
  const checkBtn = $("advVamCheckBtn");
  const calcBtn = $("advVamCalcBtn");
  const resetBtn = $("advVamResetBtn");
  const statusEl = $("advVamStatus");
  const resultWrap = $("advVamResult");
  const resultBody = $("advVamResultBody");
  const checkResultWrap = $("advVamCheckResult");
  const checkResultBody = $("advVamCheckResultBody");

  if (!checkBtn) return;

  let _lastVamSelectValue = "";
  let _checkPassed = false;

  function setVamStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className = "status " + (cls || "");
  }

  // 用月度表已查询的数据填充下拉选择框（自动使用主页面查询条件过滤）
  function populateVamMonthlySelect() {
    const sel = $("advVamMonthlySelect");
    if (!sel) return;
    const records = st.monthly ? st.monthly.records : [];

    // 从主页面获取当前查询条件（项目名称和项目编号）
    const mainProjectName = ($("projectName").value || "").trim().toLowerCase();
    const mainProjectNo = ($("projectNo").value || "").trim().toLowerCase();
    const hasFilter = mainProjectName || mainProjectNo;

    if (!hasFilter) {
      sel.innerHTML = '<option value="">-- 请先在主页面输入项目名称/编号查询 --</option>';
      sel.size = 2;
      return;
    }

    if (!records.length) {
      sel.innerHTML = '<option value="">-- 月度表暂无数据，请先在主页面查询 --</option>';
      sel.size = 2;
      return;
    }

    // 用主页面查询条件过滤月度表数据
    let html = '<option value="">-- 请选择一条记录 --</option>';
    let count = 0;
    records.forEach((r, i) => {
      const no = (r.project_no || "").toLowerCase();
      const name = (r.project_name || "").toLowerCase();
      // 匹配主页面的项目名称或项目编号
      let match = false;
      if (mainProjectName && name.includes(mainProjectName)) match = true;
      if (mainProjectNo && no.includes(mainProjectNo)) match = true;
      if (!match) return;

      const holdSubject = r.tojoy_stock || "-";
      const smRaw = r.statistics_month;
      let smStr = "-";
      if (smRaw) {
        const s = String(smRaw);
        if (/^\d{10,13}$/.test(s)) {
          const d = new Date(Number(s));
          const p = (x) => String(x).padStart(2, "0");
          smStr = `${d.getFullYear()}-${p(d.getMonth() + 1)}`;
        } else if (s.length >= 7) {
          smStr = s.slice(0, 7);
        }
      }
      html += `<option value="${i}">${r.project_name || "-"}(${r.project_no || "-"}) | ${holdSubject} | 统计月:${smStr}</option>`;
      count++;
    });

    if (count === 0) {
      const kw = mainProjectName || mainProjectNo;
      html = `<option value="">-- 未找到匹配「${kw}」的月度数据 --</option>`;
    }
    sel.innerHTML = html;
    // 动态调整 size：无数据时紧凑，有数据时展开（最大10行）
    const optCount = sel.options.length;
    sel.size = Math.min(Math.max(optCount, 2), 10);
    if (_lastVamSelectValue) sel.value = _lastVamSelectValue;
  }

  // 打开高级弹窗时自动用主页面查询条件刷新下拉
  const origAdvOpen = $("advancedBtn");
  if (origAdvOpen) {
    origAdvOpen.addEventListener("click", () => {
      populateVamMonthlySelect();
    });
  }

  // 下拉选择月度记录后自动填充四要素 + 统计月，并重置判断状态
  document.addEventListener("change", (e) => {
    if (e.target.id !== "advVamMonthlySelect") return;
    const idx = e.target.value;
    _lastVamSelectValue = idx;
    // 切换选择后重置判断状态
    _checkPassed = false;
    checkResultWrap.classList.add("hidden");
    checkResultBody.innerHTML = "";
    resultWrap.classList.add("hidden");
    resultBody.innerHTML = "";
    setVamStatus("", "");

    if (idx === "" || !st.monthly) return;
    const r = st.monthly.records[Number(idx)];
    if (!r) return;
    // 填充四要素
    $("advVamProjectNo").value = r.project_no || "";
    $("advVamProjectCompanyUscc").value = r.project_company_credit_code || "";
    $("advVamHoldingSubjectUscc").value = r.tojoy_stock_credit_code || "";
    $("advVamAgreementCompanyUscc").value = r.agreement_company_credit_code || "";
    // 填充统计月
    const smRaw = r.statistics_month;
    if (smRaw) {
      const s = String(smRaw);
      if (/^\d{10,13}$/.test(s)) {
        const d = new Date(Number(s));
        const p = (x) => String(x).padStart(2, "0");
        $("advVamStatisticsMonth").value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
      } else {
        $("advVamStatisticsMonth").value = s.slice(0, 10);
      }
    } else {
      $("advVamStatisticsMonth").value = "";
    }
  });

  resetBtn.addEventListener("click", () => {
    $("advVamProjectNo").value = "";
    $("advVamProjectCompanyUscc").value = "";
    $("advVamHoldingSubjectUscc").value = "";
    $("advVamAgreementCompanyUscc").value = "";
    $("advVamStatisticsMonth").value = "";
    const sel = $("advVamMonthlySelect");
    if (sel) sel.value = "";
    _lastVamSelectValue = "";
    _checkPassed = false;
    setVamStatus("", "");
    resultWrap.classList.add("hidden");
    resultBody.innerHTML = "";
    checkResultWrap.classList.add("hidden");
    checkResultBody.innerHTML = "";
    populateVamMonthlySelect();
  });

  // ===== 判断按钮 =====
  checkBtn.addEventListener("click", async () => {
    if (!checkLogin()) return;

    // 检查是否选了项目
    if (!$("advVamProjectNo").value.trim()) {
      setVamStatus("请先从下拉列表选择一条月度数据记录", "error");
      return;
    }

    const params = {
      projectNo: $("advVamProjectNo").value.replace(/\s+/g, ""),
      projectCompanyUscc: $("advVamProjectCompanyUscc").value.replace(/\s+/g, ""),
      holdingSubjectUscc: $("advVamHoldingSubjectUscc").value.replace(/\s+/g, ""),
      agreementCompanyUscc: $("advVamAgreementCompanyUscc").value.replace(/\s+/g, ""),
      statisticsMonth: $("advVamStatisticsMonth").value,
    };

    // 前端校验
    const missing = [];
    if (!params.projectNo) missing.push("项目编号");
    if (!params.projectCompanyUscc) missing.push("项目公司主体统一社会信用代码");
    if (!params.holdingSubjectUscc) missing.push("持股主体统一社会信用代码");
    if (!params.agreementCompanyUscc) missing.push("协议标的公司统一社会信用代码");
    if (!params.statisticsMonth) missing.push("统计月份");
    if (missing.length) {
      setVamStatus("缺少：" + missing.join("、"), "error");
      return;
    }

    setVamStatus("判断中…", "");
    checkBtn.disabled = true;
    _checkPassed = false;
    checkResultWrap.classList.add("hidden");
    resultWrap.classList.add("hidden");

    try {
      const resp = await fetch("/api/advanced/vam-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await resp.json();

      if (!data.ok) {
        setVamStatus(data.msg || "判断失败", "error");
        return;
      }

      // 渲染判断结果
      checkResultWrap.classList.remove("hidden");
      renderCheckResult(data);

      if (data.canCalc) {
        _checkPassed = true;
        setVamStatus("✅ 判断通过，可以计算", "ok");
      } else {
        _checkPassed = false;
        setVamStatus("⚠️ 不满足计算条件，请查看判断结果", "error");
      }
    } catch (e) {
      setVamStatus("请求异常：" + e.message, "error");
    } finally {
      checkBtn.disabled = false;
    }
  });

  function renderCheckResult(data) {
    const { gamble, history } = data;
    let html = "";

    // 对赌表判断
    const gambleIcon = gamble.monthExists ? "✅" : (gamble.exists ? "⚠️" : "❌");
    const gambleCls = gamble.monthExists ? "adv-verify-ok" : (gamble.exists ? "adv-verify-warn" : "adv-verify-fail");
    html += `<div class="adv-verify ${gambleCls}" style="margin-bottom:8px;">
      <b>${gambleIcon} 对赌表：</b>${gamble.detail}
    </div>`;

    // 历史表判断
    const historyIcon = history.exists ? "✅" : "⚠️";
    const historyCls = history.exists ? "adv-verify-ok" : "adv-verify-warn";
    html += `<div class="adv-verify ${historyCls}">
      <b>${historyIcon} 历史表：</b>${history.detail}
    </div>`;

    checkResultBody.innerHTML = html;
  }

  // ===== 计算按钮 =====
  calcBtn.addEventListener("click", async () => {
    if (!checkLogin()) return;

    // 检查是否选了项目
    const projectNo = $("advVamProjectNo").value.replace(/\s+/g, "");
    if (!projectNo) {
      setVamStatus("请先从下拉列表选择一条月度数据", "error");
      return;
    }

    // 检查是否通过判断
    if (!_checkPassed) {
      setVamStatus("请先点击「🔍 判断数据是否存在」", "error");
      return;
    }

    const params = {
      projectNo: $("advVamProjectNo").value.replace(/\s+/g, ""),
      projectCompanyUscc: $("advVamProjectCompanyUscc").value.replace(/\s+/g, ""),
      holdingSubjectUscc: $("advVamHoldingSubjectUscc").value.replace(/\s+/g, ""),
      agreementCompanyUscc: $("advVamAgreementCompanyUscc").value.replace(/\s+/g, ""),
      statisticsMonth: $("advVamStatisticsMonth").value,
    };

    // 前端校验
    const missing = [];
    if (!params.projectNo) missing.push("项目编号");
    if (!params.projectCompanyUscc) missing.push("项目公司主体统一社会信用代码");
    if (!params.holdingSubjectUscc) missing.push("持股主体统一社会信用代码");
    if (!params.agreementCompanyUscc) missing.push("协议标的公司统一社会信用代码");
    if (!params.statisticsMonth) missing.push("统计月份");
    if (missing.length) {
      setVamStatus("缺少：" + missing.join("、"), "error");
      return;
    }

    setVamStatus("计算中…", "");
    resultWrap.classList.add("hidden");

    try {
      const resp = await fetch("/api/advanced/vam-calc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await resp.json();

      if (!data.ok) {
        setVamStatus(data.msg || "计算失败", "error");
        resultWrap.classList.add("hidden");
        return;
      }

      setVamStatus("计算完成", "ok");
      resultWrap.classList.remove("hidden");
      renderVamResult(data);

      // 高亮月度表中匹配的行
      clearVamHighlight();
      if (data.monthly && data.monthly.recordId) {
        const hasAnyMismatch = data.verification && data.verification.overall === false;
        const mismatchFields = [];
        if (data.verification) {
          ["end_period_non_liable", "end_period_vam_stock", "time_point_non_liable", "time_point_vam_complete"].forEach(f => {
            if (data.verification[f] && data.verification[f].match === false) mismatchFields.push(f);
          });
        }
        const found = tryVamHighlight(data.monthly.recordId, mismatchFields);
        if (!found) {
          await loadMonthlyAndVamHighlight(params, data.monthly.recordId, mismatchFields);
        }
      }

      // 计算完成后关闭弹窗
      $("advancedModal").classList.add("hidden");
    } catch (e) {
      setVamStatus("请求异常：" + e.message, "error");
    } finally {
    }
  });

  function renderVamResult(data) {
    const { gamble, calcResult, prevSource, prevValues, formulas, monthly, verification } = data;
    let html = "";

    // 对赌表信息
    const gambleStatusText = gamble.hasData ? "" : '<span style="color:#ffc107;margin-left:8px;">（对赌表无匹配数据，期末取历史表值）</span>';
    html += `<div class="adv-info-block">
      <div class="adv-info-title"><span class="adv-icon adv-icon-info"></span>对赌表匹配信息${gambleStatusText}</div>
      <div class="adv-info-grid">
        <span class="adv-kv"><b>项目名称：</b>${gamble.projectName || "-"}</span>
        <span class="adv-kv"><b>统计月份：</b>${gamble.statisticsMonth || "-"}</span>
        <span class="adv-kv"><b>基础股权(basic_stock_rate)：</b>${gamble.basicStockRate != null ? gamble.basicStockRate + "%" : "无（取历史表值）"}</span>
        <span class="adv-kv"><b>应确认股权比例(should_confirmation_stock_rate)：</b>${gamble.shouldConfirmationStockRate != null ? gamble.shouldConfirmationStockRate + "%" : "无（取历史表值）"}</span>
      </div>
    </div>`;

    // 计算结果表格
    html += `<div class="adv-info-block adv-highlight">
      <div class="adv-info-title"><span class="adv-icon adv-icon-calc"></span>计算结果</div>
      <table class="adv-calc-table">
        <thead>
          <tr><th>字段</th><th>计算值</th><th>月度表实际值</th><th>校验</th></tr>
        </thead>
        <tbody>`;

    const fields = [
      { key: "end_period_non_liable", label: "期末_无责股权" },
      { key: "end_period_vam_stock", label: "期末_对赌股权" },
      { key: "time_point_non_liable", label: "时点_无责股权" },
      { key: "time_point_vam_complete", label: "时点_对赌完成" },
    ];

    fields.forEach(f => {
      const calcVal = calcResult[f.key];
      const v = verification[f.key];
      const actualVal = v ? v.actualValue : null;
      let statusIcon = "-";
      let rowClass = "";
      if (v) {
        if (v.match === true) { statusIcon = "✅"; rowClass = ""; }
        else if (v.match === false) { statusIcon = "⚠️ 差异:" + v.diff; rowClass = "adv-row-mismatch"; }
        else { statusIcon = "⏳ 无法校验"; rowClass = ""; }
      }
      html += `<tr class="${rowClass}">
        <td><b>${f.label}</b></td>
        <td>${calcVal != null ? calcVal : "空"}</td>
        <td>${actualVal != null ? actualVal : "空"}</td>
        <td>${statusIcon}</td>
      </tr>`;
    });

    html += `</tbody></table></div>`;

    // 计算公式
    html += `<div class="adv-info-block">
      <div class="adv-info-title"><span class="adv-icon adv-icon-check"></span>计算过程</div>
      <div class="adv-formula-list">
        <div class="adv-formula">① ${formulas.end_period_non_liable}</div>
        <div class="adv-formula">② ${formulas.end_period_vam_stock}</div>
        <div class="adv-formula">③ ${formulas.time_point_non_liable}</div>
        <div class="adv-formula">④ ${formulas.time_point_vam_complete}</div>
      </div>
      <div class="adv-kv" style="margin-top:8px;color:var(--muted);">上年末数据来源：${prevSource || "-"} | 期末_无责=${prevValues.end_period_non_liable != null ? prevValues.end_period_non_liable : "空"} | 期末_对赌=${prevValues.end_period_vam_stock != null ? prevValues.end_period_vam_stock : "空"}</div>
    </div>`;

    // 月度表信息
    if (monthly && monthly.msg && !monthly.recordId) {
      html += `<div class="adv-info-block"><div class="adv-kv" style="color:var(--muted);">${monthly.msg}</div></div>`;
    }

    resultBody.innerHTML = html;
  }

  // 高亮月度表中匹配行
  function tryVamHighlight(recordId, mismatchFields) {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return false;
    const rows = monthlyBody.querySelectorAll("tr[data-record-id]");
    for (const row of rows) {
      if (row.dataset.recordId === String(recordId)) {
        row.classList.add("adv-row-highlight");
        // 高亮四个计算字段
        const targetFields = ["end_period_non_liable", "end_period_vam_stock", "time_point_non_liable", "time_point_vam_complete"];
        targetFields.forEach(f => {
          const cell = row.querySelector(`td[data-field="${f}"]`);
          if (cell) {
            if (mismatchFields.includes(f)) {
              cell.classList.add("adv-cell-mismatch");
            } else {
              cell.classList.add("adv-cell-highlight");
            }
          }
        });
        switchTab("monthly");
        setTimeout(() => row.scrollIntoView({ behavior: "smooth", block: "center" }), 200);
        return true;
      }
    }
    return false;
  }

  // 加载月度表数据后再高亮
  async function loadMonthlyAndVamHighlight(params, recordId, mismatchFields) {
    const filters = {
      projectNo: params.projectNo,
      tjCreditCode: params.holdingSubjectUscc,
    };
    try {
      const resp = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table: "monthly", filters, pageNo: 1, pageSize: 100, sorts: [] }),
      });
      const r = await resp.json();
      if (r.ok) {
        st.monthly.total = r.total;
        st.monthly.records = r.records;
        st.monthly.pageNo = 1;
        renderTable("monthly");
        $("badge-monthly").textContent = r.total;
        switchTab("monthly");
        setTimeout(() => tryVamHighlight(recordId, mismatchFields), 100);
      }
    } catch (e) { /* 忽略 */ }
  }

  // 清除高亮
  function clearVamHighlight() {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return;
    monthlyBody.querySelectorAll(".adv-row-highlight").forEach(r => r.classList.remove("adv-row-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-highlight").forEach(c => c.classList.remove("adv-cell-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-mismatch").forEach(c => c.classList.remove("adv-cell-mismatch"));
  }
})();



// ===== 高级功能：工商比例计算 =====
(function initBizRatioCalc() {
  const calcBtn = $("advBizRatioCalcBtn");
  const resetBtn = $("advBizRatioResetBtn");
  const statusEl = $("advBizRatioStatus");
  const resultWrap = $("advBizRatioResult");
  const resultBody = $("advBizRatioResultBody");

  if (!calcBtn) return;

  let _lastBizRatioSelectValue = "";

  function setBizRatioStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className = "status " + (cls || "");
  }

  // 用月度表已查询的数据填充下拉选择框（自动使用主页面查询条件过滤）
  function populateBizRatioMonthlySelect() {
    const sel = $("advBizRatioMonthlySelect");
    if (!sel) return;
    const records = st.monthly ? st.monthly.records : [];

    // 从主页面获取当前查询条件（项目名称和项目编号）
    const mainProjectName = ($("projectName").value || "").trim().toLowerCase();
    const mainProjectNo = ($("projectNo").value || "").trim().toLowerCase();
    const hasFilter = mainProjectName || mainProjectNo;

    if (!hasFilter) {
      sel.innerHTML = '<option value="">-- 请先在主页面输入项目名称/编号查询 --</option>';
      sel.size = 2;
      return;
    }

    if (!records.length) {
      sel.innerHTML = '<option value="">-- 月度表暂无数据，请先在主页面查询 --</option>';
      sel.size = 2;
      return;
    }

    // 用主页面查询条件过滤月度表数据
    let html = '<option value="">-- 请选择一条记录 --</option>';
    let count = 0;
    records.forEach((r, i) => {
      const no = (r.project_no || "").toLowerCase();
      const name = (r.project_name || "").toLowerCase();
      // 匹配主页面的项目名称或项目编号
      let match = false;
      if (mainProjectName && name.includes(mainProjectName)) match = true;
      if (mainProjectNo && no.includes(mainProjectNo)) match = true;
      if (!match) return;

      const holdSubject = r.tojoy_stock || "-";
      const smRaw = r.statistics_month;
      let smStr = "-";
      if (smRaw) {
        const s = String(smRaw);
        if (/^\d{10,13}$/.test(s)) {
          const d = new Date(Number(s));
          const p = (x) => String(x).padStart(2, "0");
          smStr = `${d.getFullYear()}-${p(d.getMonth() + 1)}`;
        } else if (s.length >= 7) {
          smStr = s.slice(0, 7);
        }
      }
      html += `<option value="${i}">${r.project_name || "-"}(${r.project_no || "-"}) | ${holdSubject} | 统计月:${smStr}</option>`;
      count++;
    });

    if (count === 0) {
      const kw = mainProjectName || mainProjectNo;
      html = `<option value="">-- 未找到匹配「${kw}」的月度数据 --</option>`;
    }
    sel.innerHTML = html;
    // 动态调整 size：无数据时紧凑，有数据时展开（最大10行）
    const optCount = sel.options.length;
    sel.size = Math.min(Math.max(optCount, 2), 10);
    if (_lastBizRatioSelectValue) sel.value = _lastBizRatioSelectValue;
  }

  // 打开高级弹窗时自动刷新下拉
  const advOpenBtn = $("advancedBtn");
  if (advOpenBtn) {
    advOpenBtn.addEventListener("click", () => {
      populateBizRatioMonthlySelect();
    });
  }

  // 下拉选择月度记录后自动填充四要素 + 统计月
  document.addEventListener("change", (e) => {
    if (e.target.id !== "advBizRatioMonthlySelect") return;
    const idx = e.target.value;
    _lastBizRatioSelectValue = idx;
    // 切换选择后重置结果
    resultWrap.classList.add("hidden");
    resultBody.innerHTML = "";
    setBizRatioStatus("", "");

    if (idx === "" || !st.monthly) return;
    const r = st.monthly.records[Number(idx)];
    if (!r) return;
    // 填充四要素
    $("advBizRatioProjectNo").value = r.project_no || "";
    $("advBizRatioProjectCompanyUscc").value = r.project_company_credit_code || "";
    $("advBizRatioHoldingSubjectUscc").value = r.tojoy_stock_credit_code || "";
    $("advBizRatioAgreementCompanyUscc").value = r.agreement_company_credit_code || "";
    // 填充统计月（年月格式）
    const smRaw = r.statistics_month;
    if (smRaw) {
      const s = String(smRaw);
      if (/^\d{10,13}$/.test(s)) {
        const d = new Date(Number(s));
        const p = (x) => String(x).padStart(2, "0");
        $("advBizRatioStatisticsMonth").value = `${d.getFullYear()}-${p(d.getMonth() + 1)}`;
      } else if (s.length >= 7) {
        $("advBizRatioStatisticsMonth").value = s.slice(0, 7);
      } else {
        $("advBizRatioStatisticsMonth").value = s;
      }
    } else {
      $("advBizRatioStatisticsMonth").value = "";
    }
  });

  resetBtn.addEventListener("click", () => {
    $("advBizRatioProjectNo").value = "";
    $("advBizRatioProjectCompanyUscc").value = "";
    $("advBizRatioHoldingSubjectUscc").value = "";
    $("advBizRatioAgreementCompanyUscc").value = "";
    $("advBizRatioStatisticsMonth").value = "";
    const sel = $("advBizRatioMonthlySelect");
    if (sel) sel.value = "";
    _lastBizRatioSelectValue = "";
    setBizRatioStatus("", "");
    resultWrap.classList.add("hidden");
    resultBody.innerHTML = "";
    populateBizRatioMonthlySelect();
  });

  // ===== 计算按钮 =====
  calcBtn.addEventListener("click", async () => {
    if (!checkLogin()) return;

    const params = {
      projectNo: $("advBizRatioProjectNo").value.replace(/\s+/g, ""),
      projectCompanyUscc: $("advBizRatioProjectCompanyUscc").value.replace(/\s+/g, ""),
      holdingSubjectUscc: $("advBizRatioHoldingSubjectUscc").value.replace(/\s+/g, ""),
      agreementCompanyUscc: $("advBizRatioAgreementCompanyUscc").value.replace(/\s+/g, ""),
      statisticsMonth: $("advBizRatioStatisticsMonth").value,
    };

    // 前端校验
    const missing = [];
    if (!params.projectNo) missing.push("项目编号");
    if (!params.projectCompanyUscc) missing.push("项目公司主体统一社会信用代码");
    if (!params.holdingSubjectUscc) missing.push("持股主体统一社会信用代码");
    if (!params.agreementCompanyUscc) missing.push("协议标的公司统一社会信用代码");
    if (!params.statisticsMonth) missing.push("统计月");
    if (missing.length) {
      setBizRatioStatus("缺少：" + missing.join("、"), "error");
      return;
    }

    setBizRatioStatus("计算中…", "");
    calcBtn.disabled = true;
    resultWrap.classList.add("hidden");

    try {
      const resp = await fetch("/api/advanced/biz-ratio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await resp.json();

      if (!data.ok) {
        setBizRatioStatus(data.msg || "计算失败", "error");
        resultWrap.classList.add("hidden");
        return;
      }

      setBizRatioStatus("计算完成", "ok");
      resultWrap.classList.remove("hidden");
      renderBizRatioResult(data);

      // 高亮月度表中匹配的行
      clearBizRatioHighlight();
      if (data.monthly && data.monthly.recordId) {
        const isMismatch = data.verification && data.verification.match === false;
        const found = tryBizRatioHighlight(data.monthly.recordId, isMismatch);
        if (!found) {
          await loadMonthlyAndBizRatioHighlight(params, data.monthly.recordId, isMismatch);
        }
      }

      // 计算完成后关闭弹窗
      $("advancedModal").classList.add("hidden");
    } catch (e) {
      setBizRatioStatus("请求异常：" + e.message, "error");
    } finally {
      calcBtn.disabled = false;
    }
  });

  function renderBizRatioResult(data) {
    const { ledger, calcResult, monthly, verification } = data;
    let html = "";

    // 台账匹配信息
    html += `<div class="adv-info-block">
      <div class="adv-info-title"><span class="adv-icon adv-icon-info"></span>台账匹配信息</div>
      <div class="adv-info-grid">
        <span class="adv-kv"><b>项目编号：</b>${ledger.projectNo}</span>
        <span class="adv-kv"><b>匹配序号：</b>${ledger.seq}</span>
        <span class="adv-kv"><b>持股类型：</b>${ledger.holdingType}</span>
        <span class="adv-kv"><b>工商变更日期：</b>${ledger.bizChangeDate}</span>
        <span class="adv-kv"><b>协议标的公司工商变更后比例(number_e7b076)：</b>${ledger.bizRatioDirect != null ? ledger.bizRatioDirect + "%" : "-"}</span>
        <span class="adv-kv"><b>协议标的公司持有最终标的公司股权(number_500f42)：</b>${ledger.agreementHoldUltimate != null ? ledger.agreementHoldUltimate + "%" : "-"}</span>
        <span class="adv-kv"><b>协议标的公司工商变更后比例(number_47e399)：</b>${ledger.bizChangeAfterRatio != null ? ledger.bizChangeAfterRatio + "%" : "-"}</span>
      </div>
    </div>`;

    // 计算结果
    html += `<div class="adv-info-block adv-highlight">
      <div class="adv-info-title"><span class="adv-icon adv-icon-calc"></span>计算结果：期末工商比例</div>
      <div class="adv-result-value">${calcResult.value != null ? calcResult.value : "无法计算"}</div>
      <div class="adv-formula">${calcResult.formula}</div>
    </div>`;

    // 月度表校验
    html += `<div class="adv-info-block adv-monthly-section">
      <div class="adv-info-title"><span class="adv-icon adv-icon-check"></span>月度表校验（期末_工商比例）</div>`;

    if (monthly && monthly.statisticsMonth) {
      html += `<div class="adv-info-grid">
        <span class="adv-kv"><b>统计月：</b>${monthly.statisticsMonth}</span>
        <span class="adv-kv"><b>月度表期末_工商比例：</b>${monthly.currentValue != null ? monthly.currentValue : "空"}</span>
        <span class="adv-kv"><b>计算值：</b>${calcResult.value != null ? calcResult.value : "-"}</span>
      </div>`;
    } else if (monthly && monthly.msg) {
      html += `<div class="adv-kv" style="color:var(--muted);">${monthly.msg}</div>`;
    }

    if (verification) {
      const vCls = verification.match === true ? "adv-verify-ok" : (verification.match === false ? "adv-verify-fail" : "adv-verify-warn");
      html += `<div class="adv-verify ${vCls}">${verification.msg}</div>`;
    }

    html += `</div>`;

    resultBody.innerHTML = html;
  }

  // 高亮月度表中匹配行的期末_工商比例字段
  function tryBizRatioHighlight(recordId, isMismatch) {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return false;
    const rows = monthlyBody.querySelectorAll("tr[data-record-id]");
    for (const row of rows) {
      if (row.dataset.recordId === String(recordId)) {
        row.classList.add("adv-row-highlight");
        // 高亮期末_工商比例字段
        const targetCell = row.querySelector('td[data-field="end_period_registered_equity_ratio"]');
        if (targetCell) {
          if (isMismatch) {
            targetCell.classList.add("adv-cell-mismatch");
          } else {
            targetCell.classList.add("adv-cell-highlight");
          }
        }
        switchTab("monthly");
        setTimeout(() => row.scrollIntoView({ behavior: "smooth", block: "center" }), 200);
        return true;
      }
    }
    return false;
  }

  // 加载月度表数据后再高亮
  async function loadMonthlyAndBizRatioHighlight(params, recordId, isMismatch) {
    const filters = {
      projectNo: params.projectNo,
      tjCreditCode: params.holdingSubjectUscc,
    };
    try {
      const resp = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table: "monthly", filters, pageNo: 1, pageSize: 100, sorts: [] }),
      });
      const r = await resp.json();
      if (r.ok) {
        st.monthly.total = r.total;
        st.monthly.records = r.records;
        st.monthly.pageNo = 1;
        renderTable("monthly");
        $("badge-monthly").textContent = r.total;
        switchTab("monthly");
        setTimeout(() => tryBizRatioHighlight(recordId, isMismatch), 100);
      }
    } catch (e) { /* 忽略 */ }
  }

  // 清除高亮
  function clearBizRatioHighlight() {
    const monthlyBody = $("body-monthly");
    if (!monthlyBody) return;
    monthlyBody.querySelectorAll(".adv-row-highlight").forEach(r => r.classList.remove("adv-row-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-highlight").forEach(c => c.classList.remove("adv-cell-highlight"));
    monthlyBody.querySelectorAll(".adv-cell-mismatch").forEach(c => c.classList.remove("adv-cell-mismatch"));
  }
})();
