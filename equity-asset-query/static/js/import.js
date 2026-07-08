// ===== 导入台账功能 =====
(function initImport() {
  const importSection = $("importSection");
  const fileInput = $("importFileInput");
  const fileName = $("importFileName");
  const fileRemove = $("importFileRemove");
  const uploadBtn = $("importUploadBtn");
  const statusEl = $("importStatus");
  const progressWrap = $("importProgress");
  const progressBar = $("importProgressBar");
  const notSupported = $("importNotSupported");
  const importPanel = $("importPanel");
  const toggleBtn = $("importToggleBtn");
  const statusWrap = $("importStatusWrap");

  if (!fileInput || !importSection) return;

  let selectedFile = null;

  // 支持导入的表
  const IMPORT_SUPPORTED_TABLES = ["ledger", "holding_subject", "history"];

  // 各表对应的模板文件和导入接口
  const IMPORT_CONFIG = {
    ledger: { tpl: "/static/股权变更台账辅助表.xlsx", uploadUrl: "/api/import/upload", executeUrl: "/api/import/execute" },
    holding_subject: { tpl: "/static/天九持股主体公司管理.xlsx", uploadUrl: "/api/import/holding-subject/upload", executeUrl: "/api/import/holding-subject/execute" },
    history: { tpl: "/static/股权资产管理历史数据（25年之前的项目股权资产数据）.xlsx", uploadUrl: "/api/import/history/upload", executeUrl: "/api/import/history/execute" },
  };

  // 环境 + 表类型判断
  function checkImportEnv() {
    const toggle = $("envToggle");
    const isProd = toggle && toggle.checked;
    const isSupported = IMPORT_SUPPORTED_TABLES.includes(activeKey);

    if (!isSupported) {
      notSupported.textContent = "⏳ " + tableName(activeKey) + "导入模板准备中，敬请期待";
      notSupported.classList.remove("hidden");
      importPanel.classList.add("hidden");
    } else if (isProd) {
      notSupported.textContent = "⚠️ 导入功能仅测试环境支持，当前为生产环境";
      notSupported.classList.remove("hidden");
      importPanel.classList.add("hidden");
    } else {
      notSupported.classList.add("hidden");
      importPanel.classList.remove("hidden");
      // 更新模板下载链接
      const tplLink = importPanel.querySelector(".import-tpl-link");
      if (tplLink) {
        const cfg = IMPORT_CONFIG[activeKey];
        if (cfg) tplLink.href = cfg.tpl;
      }
    }
  }

  // 点击"导入"按钮展开/收起
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isHidden = importSection.classList.toggle("hidden");
      if (!isHidden) checkImportEnv();
    });
  }
  // 环境切换时也更新状态
  const envToggle = $("envToggle");
  if (envToggle) {
    envToggle.addEventListener("change", () => {
      if (!importSection.classList.contains("hidden")) checkImportEnv();
    });
  }

  // 点击"选择文件"按钮，显式触发 file input
  const chooseBtn = $("importChooseLabel");
  if (chooseBtn) {
    chooseBtn.addEventListener("click", () => {
      fileInput.click();
    });
  }

  // 文件选择
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
  });

  function handleFile(file) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["xlsx", "xls"].includes(ext)) {
      setImportStatus("仅支持 .xlsx / .xls 格式", "error");
      return;
    }
    selectedFile = file;
    fileName.textContent = `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileName.classList.add("has-file");
    fileRemove.style.display = "";
    uploadBtn.disabled = false;
    setImportStatus("", "");
  }

  // 移除文件
  fileRemove.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    fileName.textContent = "未选择文件";
    fileName.classList.remove("has-file");
    fileRemove.style.display = "none";
    uploadBtn.disabled = true;
    setImportStatus("", "");
    progressWrap.classList.add("hidden");
  });

  function setImportStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className = "status " + (cls || "");
    // 清除之前的详情
    if (statusWrap) {
      const oldDetail = statusWrap.querySelector(".import-detail");
      if (oldDetail) oldDetail.remove();
    }
  }

  // 上传并导入
  uploadBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    if (!isLoggedIn) {
      setImportStatus("请先登录", "error");
      return;
    }

    uploadBtn.disabled = true;
    setImportStatus("上传中…", "");
    progressWrap.classList.remove("hidden");
    progressBar.style.width = "30%";

    try {
      // 步骤1：上传文件
      const formData = new FormData();
      formData.append("file", selectedFile);

      // 根据当前表选择对应的导入接口
      const cfg = IMPORT_CONFIG[activeKey] || IMPORT_CONFIG.ledger;
      const uploadResp = await fetch(cfg.uploadUrl, { method: "POST", body: formData });
      const uploadData = await uploadResp.json();

      if (!uploadData.ok) {
        setImportStatus(uploadData.msg || "上传失败", "error");
        progressWrap.classList.add("hidden");
        uploadBtn.disabled = false;
        return;
      }

      progressBar.style.width = "60%";
      setImportStatus("上传成功，正在导入…", "");

      // 从上传响应中获取 batchNo
      const batchNo = uploadData.batchNo;
      if (!batchNo) {
        setImportStatus("上传成功但未获得 batchNo", "error");
        progressWrap.classList.add("hidden");
        uploadBtn.disabled = false;
        return;
      }

      // 步骤2：执行导入
      const importResp = await fetch(cfg.executeUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batchNo }),
      });
      const importData = await importResp.json();

      progressBar.style.width = "100%";

      if (importData.ok) {
        setImportStatus("✅ " + (importData.msg || "导入成功"), "ok");
        // 清除已选文件
        selectedFile = null;
        fileInput.value = "";
        fileName.textContent = "未选择文件";
        fileName.classList.remove("has-file");
        fileRemove.style.display = "none";
        uploadBtn.disabled = true;
      } else {
        setImportStatus(importData.msg || "导入失败", "error");
        // 如果有详情（失败文件下载链接），显示在下方
        if (importData.detail) {
          const d = importData.detail;
          let detailHtml = `<div class="import-detail">`;
          detailHtml += `<div class="import-detail-summary">共 ${d.totalNum} 行，通过 ${d.sucNum} 行，失败 ${d.failNum} 行</div>`;
          // 显示失败原因列表
          if (d.failReasons && d.failReasons.length) {
            detailHtml += `<div class="import-fail-reasons">`;
            detailHtml += `<div class="import-fail-reasons-title">失败原因：</div>`;
            detailHtml += `<ul class="import-fail-list">`;
            d.failReasons.forEach((reason, i) => {
              detailHtml += `<li>第${i + 1}行：${reason.replace(/</g, "&lt;")}</li>`;
            });
            detailHtml += `</ul></div>`;
          }
          if (d.failFileUrl) {
            detailHtml += `<a class="import-detail-link" href="${d.failFileUrl}" target="_blank" rel="noopener">📥 下载完整失败详情文件</a>`;
          }
          detailHtml += `</div>`;
          // 插入到详情区域
          if (statusWrap) statusWrap.innerHTML = detailHtml;
        }
      }
    } catch (e) {
      setImportStatus("请求异常：" + e.message, "error");
    } finally {
      uploadBtn.disabled = false;
      setTimeout(() => { progressWrap.classList.add("hidden"); progressBar.style.width = "0%"; }, 2000);
    }
  });
})();
