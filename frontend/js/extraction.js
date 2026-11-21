/**
 * SocialPlus.ai — Universal Multi-Engine Extraction Controller
 * Coordinates live full-screen monitoring, engine state tracking, and SSE streaming.
 */

let currentExtractionTaskId = null;
let extractionEventSource = null;
let extractionTimerInterval = null;
let extractionStartTime = 0;
let latestExtractionData = null;

function formatElapsed(seconds) {
  return seconds.toFixed(1) + "s";
}

function truncateUrl(url, maxLen = 65) {
  if (!url) return "—";
  if (url.length <= maxLen) return url;
  return url.substring(0, maxLen - 3) + "...";
}

function resetMonitorUI(url, platform = "Detecting...") {
  // Reset source info
  document.getElementById("mon-url-val").textContent = truncateUrl(url);
  document.getElementById("mon-url-val").title = url;
  document.getElementById("mon-platform-val").textContent = platform.toUpperCase();
  document.getElementById("mon-taskid-val").textContent = currentExtractionTaskId || "Generating...";
  document.getElementById("mon-timer-val").textContent = "0.0s";

  // Reset Progress
  document.getElementById("mon-progress-bar").style.width = "5%";
  document.getElementById("mon-progress-pct").textContent = "5%";
  document.getElementById("mon-stage-desc").textContent = "Initializing Universal Extraction Engine...";

  // Reset Stage Pills
  ["stage-p-detect", "stage-p-engine", "stage-p-extract", "stage-p-validate", "stage-p-analysis"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.className = "stage-pill";
  });
  const firstPill = document.getElementById("stage-p-detect");
  if (firstPill) firstPill.className = "stage-pill active";

  // Reset 4 Engine Cards
  const engines = ["crawl4ai", "playwright", "scrapy", "beautifulsoup"];
  engines.forEach(eng => {
    updateEngineCardUI(eng, {
      status: "WAITING",
      records_extracted: 0,
      execution_time_sec: 0.0,
      last_operation: "Waiting for scheduler...",
      failure_reason: null
    });
  });

  // Reset Stats
  ["stat-m-total", "stat-m-unique", "stat-m-dups", "stat-m-valid", "stat-m-invalid", "stat-m-pages", "stat-m-attempted", "stat-m-success"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = "0";
  });

  // Clear Terminal Logs
  const terminalBody = document.getElementById("mon-terminal-body");
  if (terminalBody) terminalBody.innerHTML = "";

  // Hide Banners
  document.getElementById("mon-completion-banner").style.display = "none";
  document.getElementById("mon-failure-banner").style.display = "none";
  document.getElementById("btn-mon-cancel").style.display = "inline-flex";
  document.getElementById("btn-mon-cancel").disabled = false;
}

function appendTerminalLog(logEntry) {
  const terminalBody = document.getElementById("mon-terminal-body");
  if (!terminalBody) return;

  const div = document.createElement("div");
  div.className = "log-entry";

  const lvl = logEntry.level || "info";
  div.innerHTML = `
    <span class="log-time">[${logEntry.timestamp || ""}]</span>
    <span class="log-msg ${lvl}">${logEntry.engine ? `<b>[${logEntry.engine.toUpperCase()}]</b> ` : ""}${logEntry.message || ""}</span>
  `;
  terminalBody.appendChild(div);
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

function updateEngineCardUI(engineKey, data) {
  const card = document.getElementById(`engine-card-${engineKey}`);
  if (!card) return;

  const statusBadge = document.getElementById(`eng-status-${engineKey}`);
  const recordsEl = document.getElementById(`eng-records-${engineKey}`);
  const timeEl = document.getElementById(`eng-time-${engineKey}`);
  const lastOpEl = document.getElementById(`eng-op-${engineKey}`);
  const errorBox = document.getElementById(`eng-err-${engineKey}`);

  const status = (data.status || "WAITING").toLowerCase();

  if (statusBadge) {
    statusBadge.textContent = data.status || "WAITING";
    statusBadge.className = `engine-status-badge status-${status}`;
  }

  if (recordsEl) recordsEl.textContent = data.records_extracted || 0;
  if (timeEl) timeEl.textContent = (data.execution_time_sec ? data.execution_time_sec.toFixed(1) : "0.0") + "s";
  if (lastOpEl) lastOpEl.textContent = data.last_operation || "—";

  if (errorBox) {
    if (data.failure_reason) {
      errorBox.style.display = "block";
      errorBox.textContent = data.failure_reason;
    } else {
      errorBox.style.display = "none";
    }
  }
}

function updateStageBreadcrumbs(progress) {
  const p = parseFloat(progress);
  const stages = [
    { id: "stage-p-detect", min: 10, max: 25 },
    { id: "stage-p-engine", min: 25, max: 50 },
    { id: "stage-p-extract", min: 50, max: 85 },
    { id: "stage-p-validate", min: 85, max: 92 },
    { id: "stage-p-analysis", min: 92, max: 100 }
  ];

  stages.forEach(s => {
    const el = document.getElementById(s.id);
    if (!el) return;
    if (p >= s.max) {
      el.className = "stage-pill done";
    } else if (p >= s.min) {
      el.className = "stage-pill active";
    } else {
      el.className = "stage-pill";
    }
  });
}

async function startUniversalExtraction(url, maxRecords = 200) {
  if (!url || !url.trim()) {
    showToast("Please provide a valid URL.", "warning");
    return;
  }

  // Switch to Full-Screen Monitoring View
  document.getElementById("section-home").style.display = "none";
  document.getElementById("section-dashboard").style.display = "none";
  const monitorSection = document.getElementById("section-extraction-monitor");
  monitorSection.style.display = "block";
  window.scrollTo({ top: 0, behavior: "smooth" });

  resetMonitorUI(url);

  extractionStartTime = Date.now();
  if (extractionTimerInterval) clearInterval(extractionTimerInterval);
  extractionTimerInterval = setInterval(() => {
    const elapsed = (Date.now() - extractionStartTime) / 1000;
    const timerEl = document.getElementById("mon-timer-val");
    if (timerEl) timerEl.textContent = formatElapsed(elapsed);
  }, 100);

  appendTerminalLog({ timestamp: new Date().toLocaleTimeString(), message: "Contacting SocialPlus Universal Extraction Orchestrator...", level: "info" });

  try {
    const startRes = await apiPost("/api/extraction/start", {
      url: url.trim(),
      max_records: maxRecords
    });

    if (!startRes.success) {
      clearInterval(extractionTimerInterval);
      showToast(startRes.message || "Failed to start extraction task.", "error");
      return;
    }

    currentExtractionTaskId = startRes.task_id;
    document.getElementById("mon-taskid-val").textContent = currentExtractionTaskId.substring(0, 13) + "...";
    document.getElementById("mon-platform-val").textContent = (startRes.platform || "general").toUpperCase();

    // Connect Server-Sent Events (SSE) Stream
    if (extractionEventSource) {
      extractionEventSource.close();
    }

    const sseUrl = `/api/extraction/${currentExtractionTaskId}/events`;
    extractionEventSource = new EventSource(sseUrl);

    extractionEventSource.addEventListener("init", (e) => {
      const data = JSON.parse(e.data);
      latestExtractionData = data;
    });

    extractionEventSource.addEventListener("platform_detected", (e) => {
      const data = JSON.parse(e.data).data;
      if (data && data.platform) {
        document.getElementById("mon-platform-val").textContent = data.platform.toUpperCase();
      }
    });

    extractionEventSource.addEventListener("progress", (e) => {
      const pData = JSON.parse(e.data).data;
      const pct = pData.progress || 0;
      document.getElementById("mon-progress-bar").style.width = `${pct}%`;
      document.getElementById("mon-progress-pct").textContent = `${pct}%`;
      document.getElementById("mon-stage-desc").textContent = pData.stage || "";
      updateStageBreadcrumbs(pct);
    });

    extractionEventSource.addEventListener("engine_status", (e) => {
      const engData = JSON.parse(e.data).data;
      if (engData && engData.engine) {
        updateEngineCardUI(engData.engine, engData);
      }
    });

    extractionEventSource.addEventListener("log", (e) => {
      const logData = JSON.parse(e.data).data;
      if (logData) appendTerminalLog(logData);
    });

    extractionEventSource.addEventListener("stats", (e) => {
      const s = JSON.parse(e.data).data;
      if (s) {
        if (s.total_records !== undefined) document.getElementById("stat-m-total").textContent = s.total_records;
        if (s.unique_records !== undefined) document.getElementById("stat-m-unique").textContent = s.unique_records;
        if (s.duplicates_removed !== undefined) document.getElementById("stat-m-dups").textContent = s.duplicates_removed;
        if (s.valid_records !== undefined) document.getElementById("stat-m-valid").textContent = s.valid_records;
        if (s.invalid_records !== undefined) document.getElementById("stat-m-invalid").textContent = s.invalid_records;
        if (s.pages_processed !== undefined) document.getElementById("stat-m-pages").textContent = s.pages_processed;
        if (s.engines_attempted !== undefined) document.getElementById("stat-m-attempted").textContent = s.engines_attempted;
        if (s.engines_successful !== undefined) document.getElementById("stat-m-success").textContent = s.engines_successful;
      }
    });

    extractionEventSource.addEventListener("completed", (e) => {
      clearInterval(extractionTimerInterval);
      extractionEventSource.close();
      const finalTask = JSON.parse(e.data);
      latestExtractionData = finalTask;

      document.getElementById("btn-mon-cancel").style.display = "none";
      const finalProgress = Number.isFinite(Number(finalTask.progress))
        ? Number(finalTask.progress)
        : (finalTask.status === "COMPLETED" && finalTask.comments_count > 0 ? 100 : 95);
      document.getElementById("mon-progress-bar").style.width = `${finalProgress}%`;
      document.getElementById("mon-progress-pct").textContent = `${finalProgress}%`;
      updateStageBreadcrumbs(finalProgress);

      // Check if we retrieved actual reviews
      if (finalTask.status === "COMPLETED" && finalTask.has_analysis) {
        const compBanner = document.getElementById("mon-completion-banner");
        compBanner.style.display = "block";
        document.getElementById("comp-count-val").textContent = finalTask.stats.unique_records || finalTask.comments_count || 0;
        document.getElementById("comp-platform-val").textContent = (finalTask.platform || "Platform").toUpperCase();
        showToast("Universal Extraction Completed Successfully!", "success");
      } else {
        // Partial or Failed
        const failBanner = document.getElementById("mon-failure-banner");
        failBanner.style.display = "block";
        document.getElementById("fail-reason-val").textContent = finalTask.error || "No customer reviews could be retrieved automatically from this source.";
        showToast("Review extraction restricted by platform bot-controls.", "warning");
      }
    });

    extractionEventSource.addEventListener("error", (e) => {
      clearInterval(extractionTimerInterval);
      try {
        const errObj = JSON.parse(e.data || "{}");
        appendTerminalLog({ timestamp: new Date().toLocaleTimeString(), message: errObj.error || "Stream connection interrupted.", level: "error" });
      } catch (_) {}
    });

  } catch (err) {
    clearInterval(extractionTimerInterval);
    showToast(`Extraction request failed: ${err.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Cancel Button
  const btnCancel = document.getElementById("btn-mon-cancel");
  if (btnCancel) {
    btnCancel.addEventListener("click", async () => {
      if (currentExtractionTaskId) {
        btnCancel.disabled = true;
        btnCancel.textContent = "Cancelling...";
        try {
          await apiPost(`/api/extraction/${currentExtractionTaskId}/cancel`, {});
          showToast("Extraction task cancelled.", "info");
        } catch (e) {
          showToast("Error sending cancel request.", "error");
        }
      }
    });
  }

  // Return to Analyzers Button
  const btnReturn = document.getElementById("btn-mon-return");
  if (btnReturn) {
    btnReturn.addEventListener("click", () => {
      if (extractionEventSource) extractionEventSource.close();
      if (extractionTimerInterval) clearInterval(extractionTimerInterval);
      document.getElementById("section-extraction-monitor").style.display = "none";
      document.getElementById("section-home").style.display = "block";
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Continue to AI Analysis Button
  const btnProceed = document.getElementById("btn-mon-proceed-analysis");
  if (btnProceed) {
    btnProceed.addEventListener("click", async () => {
      if (!currentExtractionTaskId) return;

      showProgress("Loading AI Intelligence Dashboard", "Formatting charts and sentiment spectrum...");
      try {
        const res = await apiGet(`/api/extraction/${currentExtractionTaskId}/result`);
        hideProgress();
        if (res.success && res.analysis) {
          document.getElementById("section-extraction-monitor").style.display = "none";
          renderDashboard(res.analysis);
        } else {
          showToast(res.message || "Failed to load analysis.", "error");
        }
      } catch (err) {
        hideProgress();
        showToast(`Error loading dashboard: ${err.message}`, "error");
      }
    });
  }

  // Switch to Upload File from Failure Banner
  const btnFailUpload = document.getElementById("btn-mon-fail-upload");
  if (btnFailUpload) {
    btnFailUpload.addEventListener("click", () => {
      document.getElementById("section-extraction-monitor").style.display = "none";
      document.getElementById("section-home").style.display = "block";
      const targetPanel = latestExtractionData?.platform === "youtube" ? "panel-youtube" : (latestExtractionData?.platform === "instagram" || latestExtractionData?.platform === "facebook" ? "panel-meta" : "panel-ecommerce");
      
      // Activate correct panel and switch to upload tab
      if (targetPanel === "panel-ecommerce") {
        document.querySelectorAll(".panel-container").forEach(p => p.style.display = "none");
        document.getElementById("panel-ecommerce").style.display = "block";
        switchTab("ecom-tabs", "upload");
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Retry Button from Failure Banner
  const btnFailRetry = document.getElementById("btn-mon-fail-retry");
  if (btnFailRetry) {
    btnFailRetry.addEventListener("click", async () => {
      if (currentExtractionTaskId) {
        try {
          const res = await apiPost(`/api/extraction/${currentExtractionTaskId}/retry`, {});
          if (res.success) {
            startUniversalExtraction(latestExtractionData?.url || "", latestExtractionData?.max_records || 200);
          }
        } catch (e) {
          showToast("Error retrying task.", "error");
        }
      }
    });
  }
});
