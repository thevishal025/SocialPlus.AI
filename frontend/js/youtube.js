/**
 * SocialPlus.ai — YouTube Analyzer Controller
 * Uses SSE streaming for real-time fetch progress.
 */

let selectedYtQuantity = 500;
let _ytEventSource = null; // active SSE connection

// Allow cancel from progress overlay button
window.cancelCurrentFetch = function () {
  if (_ytEventSource) {
    _ytEventSource.close();
    _ytEventSource = null;
  }
  hideProgress();
  showToast("Fetch cancelled.", "info");
};

document.addEventListener("DOMContentLoaded", () => {
  // ── Tab switching ─────────────────────────────────────────────────────────
  setupSegmentedTabs("yt-tabs", (mode) => {
    const apiView = document.getElementById("yt-view-api");
    const pubView = document.getElementById("yt-view-public");
    const uplView = document.getElementById("yt-view-upload");
    if (apiView) apiView.style.display = mode === "api" ? "block" : "none";
    if (pubView) pubView.style.display = mode === "public" ? "block" : "none";
    if (uplView) uplView.style.display = mode === "upload" ? "block" : "none";
  });

  // ── Quantity pills ────────────────────────────────────────────────────────
  const qtyPills      = document.querySelectorAll("#yt-qty-wrap .qty-pill");
  const customQtyInput = document.getElementById("yt-custom-qty");

  qtyPills.forEach(pill => {
    pill.addEventListener("click", () => {
      qtyPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const val = pill.getAttribute("data-val");
      if (val === "custom") {
        customQtyInput.style.display = "block";
        selectedYtQuantity = parseInt(customQtyInput.value) || 1000;
      } else if (val === "all") {
        customQtyInput.style.display = "none";
        selectedYtQuantity = 10000;
      } else {
        customQtyInput.style.display = "none";
        selectedYtQuantity = parseInt(val) || 500;
      }
    });
  });
  customQtyInput.addEventListener("input", (e) => {
    selectedYtQuantity = parseInt(e.target.value) || 500;
  });

  // ── 1. With API — SSE streaming ───────────────────────────────────────────
  const btnFetchApi = document.getElementById("btn-yt-fetch-api");
  let isYtFetching = false;

  if (btnFetchApi) {
    btnFetchApi.addEventListener("click", () => {
      if (isYtFetching) return;

      const input = document.getElementById("yt-video-input").value.trim();
      if (!input) {
        showToast("Please enter a YouTube video URL or ID.", "warning");
        return;
      }

      isYtFetching = true;
      btnFetchApi.disabled = true;
      const originalBtnText = btnFetchApi.textContent;
      btnFetchApi.textContent = "Connecting to YouTube…";

      const cleanup = () => {
        isYtFetching = false;
        btnFetchApi.disabled = false;
        btnFetchApi.textContent = originalBtnText;
        hideProgress();
        if (_ytEventSource) {
          try { _ytEventSource.close(); } catch (_) {}
          _ytEventSource = null;
        }
      };

      // Show progress with cancel button
      showProgressSteps("Connecting to YouTube Data API", "Initialising…");
      updateProgressCount("");

      const url = `/api/youtube/api/fetch-stream?url_or_id=${encodeURIComponent(input)}&max_comments=${selectedYtQuantity}&include_replies=true`;
      let es;
      try {
        es = new EventSource(url);
        _ytEventSource = es;
      } catch (err) {
        cleanup();
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Connection Failed", `Failed to initiate streaming connection: ${err.message}`, () => btnFetchApi.click());
        } else {
          showToast(`Connection failed: ${err.message}`, "error");
        }
        return;
      }

      es.addEventListener("progress", (e) => {
        try {
          const d = JSON.parse(e.data);
          const stageLabels = {
            validating: "Validating URL…",
            metadata:   "Fetching video metadata…",
            fetching:   "Fetching comment pages…",
            analyzing:  "Running AI/ML analysis…",
          };
          updateProgressStep(stageLabels[d.stage] || d.message);
          if (d.count > 0) updateProgressCount(`${d.count} comments fetched so far`);
          if (d.metadata && d.metadata.title) {
            updateProgressTitle(`📺 ${d.metadata.title.slice(0, 60)}`);
          }
          markProgressStage(d.stage);
        } catch (_) {}
      });

      es.addEventListener("done", (e) => {
        cleanup();
        try {
          const d = JSON.parse(e.data);
          if (d.success && d.analysis) {
            showToast(d.message || "Analysis complete!", "success");
            renderDashboard(d.analysis);
          } else {
            const msg = d.message || "Analysis could not be completed for this video.";
            if (typeof showErrorPopup === "function") {
              showErrorPopup("YouTube Analysis Notice", msg, () => btnFetchApi.click());
            } else {
              showToast(msg, "error");
            }
          }
        } catch (err) {
          if (typeof showErrorPopup === "function") {
            showErrorPopup("Processing Error", `Failed to display analysis: ${err.message}`, () => btnFetchApi.click());
          } else {
            showToast(`Error rendering results: ${err.message}`, "error");
          }
        }
      });

      es.addEventListener("error", (e) => {
        cleanup();
        let errMsg = "An error occurred while communicating with YouTube Data API.";
        try {
          if (e.data) {
            const d = JSON.parse(e.data);
            if (d.status_code === "not_configured") {
              const banner = document.getElementById("yt-api-banner");
              if (banner) {
                banner.style.display = "flex";
                const bmsg = document.getElementById("yt-api-banner-msg");
                if (bmsg) {
                  bmsg.innerHTML = `<b>API Key Missing:</b> ${d.message}<br><button class="btn-outline" style="margin-top:6px; padding:4px 8px; font-size:11px;" onclick="switchTab('yt-tabs','upload')">Switch to Upload File Mode</button>`;
                }
              }
            }
            errMsg = d.message || errMsg;
          }
        } catch (_) {}

        if (typeof showErrorPopup === "function") {
          showErrorPopup("YouTube API Notice", errMsg, () => btnFetchApi.click());
        } else {
          showToast(errMsg, "error");
        }
      });

      // Native EventSource error (network level)
      es.onerror = () => {
        if (es.readyState === EventSource.CLOSED) return;
        cleanup();
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Connection Interrupted", "The connection to YouTube extraction was interrupted or closed unexpectedly. Please retry.", () => btnFetchApi.click());
        } else {
          showToast("Connection error. Please check the backend server.", "error");
        }
      };
    });
  }

  // ── 2. Without API ────────────────────────────────────────────────────────
  const btnFetchPublic = document.getElementById("btn-yt-fetch-public");
  if (btnFetchPublic) {
    btnFetchPublic.addEventListener("click", async () => {
      const input = document.getElementById("yt-public-input").value.trim();
      if (!input) {
        showToast("Please enter a YouTube URL.", "warning");
        return;
      }

      showProgress("Checking Public Route", "Querying available public metadata…");
      try {
        const res = await apiPost("/api/youtube/public/fetch", {
          url_or_id: input,
          max_comments: 100,
        });

        hideProgress();
        const resBox = document.getElementById("yt-public-result-box");
        resBox.style.display = "block";

        // Show video metadata if available
        const meta = res.metadata || {};
        const metaHtml = meta.title
          ? `<div style="margin-bottom:10px; padding:10px; background:#f8fafc; border-radius:8px; font-size:13px;">
               <strong>📺 ${meta.title}</strong><br>
               <span style="color:var(--text-secondary);">Channel: ${meta.author_name || "—"}</span>
             </div>`
          : "";

        resBox.innerHTML = `
          <div class="status-banner ${res.success ? "info" : "warning"}" style="display:block;">
            ${metaHtml}
            <h4 style="font-weight:700; margin-bottom:6px;">Public Access: ${res.success ? "Available" : "Not Available"}</h4>
            <p style="margin-bottom:10px; white-space:pre-line;">${res.message}</p>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <button class="btn-primary" style="padding:6px 12px; font-size:12px;" onclick="switchTab('yt-tabs','api')">1. Use With API</button>
              <button class="btn-outline" style="padding:6px 12px; font-size:12px;" onclick="switchTab('yt-tabs','upload')">2. Upload Comments File</button>
            </div>
          </div>
        `;
      } catch (err) {
        hideProgress();
        showToast(`Error: ${err.message}`, "error");
      }
    });
  }
});

// ── Progress UI helpers (supplement app.js) ──────────────────────────────────

const STAGE_ORDER = ["validating", "metadata", "fetching", "analyzing", "done"];
const STAGE_LABELS = {
  validating: "Validate URL",
  metadata:   "Fetch Metadata",
  fetching:   "Fetch Comments",
  analyzing:  "AI Analysis",
  done:       "Complete",
};

function showProgressSteps(title, step) {
  document.getElementById("progress-title").textContent = title;
  document.getElementById("progress-step").textContent  = step;

  // Render step list
  const list = document.getElementById("progress-steps-list");
  if (list) {
    list.innerHTML = STAGE_ORDER.slice(0, 4).map((s, i) => `
      <div id="pstep-${s}" style="display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text-secondary);">
        <span id="pstep-icon-${s}" style="width:18px; height:18px; border-radius:50%; border:2px solid #cbd5e1; display:flex; align-items:center; justify-content:center; font-size:10px; flex-shrink:0;">
          ${i + 1}
        </span>
        <span>${STAGE_LABELS[s]}</span>
      </div>
    `).join("");
  }

  // Show cancel button
  const cancelBtn = document.getElementById("btn-progress-cancel");
  if (cancelBtn) cancelBtn.style.display = "inline-block";

  document.getElementById("progress-overlay").style.display = "flex";
}

function updateProgressTitle(title) {
  document.getElementById("progress-title").textContent = title;
}

function updateProgressStep(step) {
  document.getElementById("progress-step").textContent = step;
}

function updateProgressCount(text) {
  const el = document.getElementById("progress-count");
  if (!el) return;
  el.style.display = text ? "block" : "none";
  el.textContent = text;
}

function markProgressStage(currentStage) {
  STAGE_ORDER.forEach((s, i) => {
    const icon = document.getElementById(`pstep-icon-${s}`);
    if (!icon) return;
    const idx = STAGE_ORDER.indexOf(currentStage);
    if (i < idx) {
      // Completed
      icon.style.background = "#16a34a";
      icon.style.borderColor = "#16a34a";
      icon.style.color = "#fff";
      icon.textContent = "✓";
    } else if (s === currentStage) {
      // Active
      icon.style.background = "#2563eb";
      icon.style.borderColor = "#2563eb";
      icon.style.color = "#fff";
      icon.textContent = "●";
    } else {
      // Pending
      icon.style.background = "";
      icon.style.borderColor = "#cbd5e1";
      icon.style.color = "var(--text-secondary)";
      icon.textContent = i + 1;
    }
  });
}
