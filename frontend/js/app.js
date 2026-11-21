/**
 * SocialPlus.ai — Core Application & Navigation Controller
 * Master View Router, Glass Modals, History, and Multilingual Support
 */

let currentView = "home";
let previousView = "home";
let pendingConfirmCallback = null;
let pendingRetryCallback = null;

document.addEventListener("DOMContentLoaded", () => {
  setupViewRouting();
  setupHistory();
  setupConfirmModal();
  setupErrorModal();
  setupFiltersListeners();
  initHowToUseSection();
});

// ================================================================
// 1. View Routing & Navigation
// ================================================================
function showView(viewName) {
  const views = {
    "home": "section-home",
    "youtube": "section-youtube",
    "meta": "section-meta",
    "ecommerce": "section-ecommerce",
    "history": "section-history",
    "howtouse": "section-howtouse",
    "dashboard": "section-dashboard",
    "extraction-monitor": "section-extraction-monitor"
  };

  if (viewName !== "dashboard" && viewName !== "extraction-monitor" && viewName !== "history" && viewName !== "howtouse") {
    previousView = viewName;
  }

  // Hide all sections
  Object.values(views).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });

  // Reveal requested view
  const targetId = views[viewName] || "section-home";
  const targetEl = document.getElementById(targetId);
  if (targetEl) {
    targetEl.style.display = "block";
  }

  currentView = viewName;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupViewRouting() {
  // Brand Logo -> Home
  const brandHome = document.getElementById("nav-brand-home");
  if (brandHome) {
    brandHome.addEventListener("click", () => showView("home"));
    brandHome.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") showView("home");
    });
  }

  // Nav: History
  const btnOpenHistory = document.getElementById("btn-open-history");
  if (btnOpenHistory) {
    btnOpenHistory.addEventListener("click", () => {
      showView("history");
      loadHistoryPageList();
    });
  }

  // Nav: How to Use
  const btnOpenHowToUse = document.getElementById("btn-open-howtouse");
  if (btnOpenHowToUse) {
    btnOpenHowToUse.addEventListener("click", () => {
      showView("howtouse");
      if (window.initHowToUse) window.initHowToUse();
    });
  }

  // Analyzer Cards on Home
  const cardYoutube = document.getElementById("card-youtube");
  if (cardYoutube) {
    cardYoutube.addEventListener("click", () => showView("youtube"));
    cardYoutube.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") showView("youtube");
    });
  }

  const cardMeta = document.getElementById("card-meta");
  if (cardMeta) {
    cardMeta.addEventListener("click", () => showView("meta"));
    cardMeta.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") showView("meta");
    });
  }

  const cardEcommerce = document.getElementById("card-ecommerce");
  if (cardEcommerce) {
    cardEcommerce.addEventListener("click", () => showView("ecommerce"));
    cardEcommerce.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") showView("ecommerce");
    });
  }

  // Back Buttons
  const backButtons = [
    { id: "btn-yt-back", target: "home" },
    { id: "btn-meta-back", target: "home" },
    { id: "btn-ecom-back", target: "home" },
    { id: "btn-history-back", target: "home" },
    { id: "btn-howtouse-back", target: "home" },
  ];

  backButtons.forEach(({ id, target }) => {
    const btn = document.getElementById(id);
    if (btn) btn.addEventListener("click", () => showView(target));
  });

  // Dashboard Back Button returns to the previous analyzer
  const btnDashBack = document.getElementById("btn-dash-back");
  if (btnDashBack) {
    btnDashBack.addEventListener("click", () => {
      showView(previousView || "home");
    });
  }

  // Monitor Return Button
  const btnMonReturn = document.getElementById("btn-mon-return");
  if (btnMonReturn) {
    btnMonReturn.addEventListener("click", () => {
      showView(previousView || "home");
    });
  }
}

// ================================================================
// 2. Segmented Tab Helper
// ================================================================
function setupSegmentedTabs(containerId, onChangeCallback) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const tabs = container.querySelectorAll(".seg-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const val = tab.getAttribute("data-mode") || tab.getAttribute("data-platform");
      if (onChangeCallback) onChangeCallback(val);
    });
  });
}

function switchTab(containerId, targetVal) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const targetTab = container.querySelector(`[data-mode="${targetVal}"], [data-platform="${targetVal}"]`);
  if (targetTab) {
    targetTab.click();
  }
}

// ================================================================
// 3. History Page & Persistence (Strictly Latest 20)
// ================================================================
function setupHistory() {
  const searchInput = document.getElementById("history-page-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      loadHistoryPageList(e.target.value.trim());
    });
  }
}

async function loadHistoryPageList(searchTerm = "") {
  const container = document.getElementById("history-page-container");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align:center; padding:40px; color:var(--text-muted); font-size:14px;">
      <span class="progress-spinner" style="width:20px; height:20px; margin-bottom:12px; display:inline-block;"></span>
      <p>Loading analysis history records...</p>
    </div>
  `;

  try {
    const url = searchTerm ? `/api/history?search=${encodeURIComponent(searchTerm)}&limit=20` : "/api/history?limit=20";
    const res = await apiGet(url);

    container.innerHTML = "";
    const items = Array.isArray(res.items) ? res.items : [];

    // Strictly enforce latest 20 records
    const latest20 = items.slice(0, 20);

    if (latest20.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding:48px 24px; color:var(--text-muted); font-size:14px; background:rgba(255,255,255,0.02); border:1px dashed var(--glass-border); border-radius:var(--radius-lg);">
          <div style="font-size:32px; margin-bottom:12px;">📊</div>
          <strong style="color:var(--text-primary); font-size:16px; display:block; margin-bottom:6px;">No analysis records found</strong>
          <p>Extract comments using YouTube, Meta, or E-commerce Analyzer to view saved reports here.</p>
        </div>
      `;
      return;
    }

    latest20.forEach(item => {
      const card = document.createElement("div");
      card.className = "history-card";
      const dateStr = item.created_at ? item.created_at.split("T")[0] : "Recent";
      const platformName = (item.platform || "GENERAL").toUpperCase();

      card.innerHTML = `
        <div class="history-card-info">
          <div class="history-card-title">${escapeHtml(item.title || "Untitled Analysis")}</div>
          <div class="history-card-meta">
            <span class="history-pill platform-${(item.platform || '').toLowerCase()}">${platformName}</span>
            <span>&bull;</span>
            <span>${Number(item.comment_count || 0).toLocaleString()} comments</span>
            <span>&bull;</span>
            <span>${dateStr}</span>
          </div>
        </div>
        <div class="history-card-actions">
          <button type="button" class="btn-primary" style="padding:7px 14px; font-size:12px;" onclick="loadHistoryItem('${item.id}')">View Report</button>
          <button type="button" class="btn-outline btn-delete" style="padding:7px 12px; font-size:12px; color:var(--accent-rose); border-color:rgba(244,63,94,0.3);" onclick="confirmDeleteHistoryItem('${item.id}', '${escapeHtml(item.title || '')}')">Delete</button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `
      <div style="color:var(--accent-rose); padding:24px; text-align:center; background:rgba(244,63,94,0.08); border-radius:var(--radius-md); border:1px solid rgba(244,63,94,0.2);">
        Failed to load history: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

async function loadHistoryItem(id) {
  showProgress("Loading Saved Report", "Fetching intelligence record from database...");
  try {
    const data = await apiGet(`/api/analysis/${id}`);
    hideProgress();
    renderDashboard(data);
    showView("dashboard");
  } catch (err) {
    hideProgress();
    showToast(`Error opening report: ${err.message}`, "error");
  }
}

function confirmDeleteHistoryItem(id, title) {
  showConfirmModal(
    "Delete Analysis Record",
    `Are you sure you want to delete "${title || 'this report'}"? This action cannot be undone.`,
    async () => {
      try {
        await apiDelete(`/api/history/${id}`);
        showToast("Analysis record deleted successfully.", "info");
        loadHistoryPageList();
      } catch (err) {
        showToast(`Delete failed: ${err.message}`, "error");
      }
    }
  );
}

// ================================================================
// 4. Glass Confirmation Modal (Replaces browser confirm)
// ================================================================
function setupConfirmModal() {
  const btnClose = document.getElementById("btn-modal-confirm-close");
  const btnCancel = document.getElementById("btn-modal-confirm-cancel");
  const btnOk = document.getElementById("btn-modal-confirm-ok");

  if (btnClose) btnClose.addEventListener("click", closeConfirmModal);
  if (btnCancel) btnCancel.addEventListener("click", closeConfirmModal);

  if (btnOk) {
    btnOk.addEventListener("click", () => {
      if (typeof pendingConfirmCallback === "function") {
        const cb = pendingConfirmCallback;
        closeConfirmModal();
        cb();
      } else {
        closeConfirmModal();
      }
    });
  }
}

function showConfirmModal(title, message, onConfirm) {
  const modal = document.getElementById("modal-confirm");
  const titleEl = document.getElementById("modal-confirm-title");
  const msgEl = document.getElementById("modal-confirm-message");

  if (titleEl) titleEl.textContent = title || "Confirm Action";
  if (msgEl) msgEl.textContent = message || "Are you sure you want to proceed?";

  pendingConfirmCallback = onConfirm;
  if (modal) modal.style.display = "flex";
}

function closeConfirmModal() {
  const modal = document.getElementById("modal-confirm");
  if (modal) modal.style.display = "none";
  pendingConfirmCallback = null;
}

// ================================================================
// 4b. Glass Error & Retry Modal
// ================================================================
function setupErrorModal() {
  const closeBtn = document.getElementById("btn-modal-error-close");
  const dismissBtn = document.getElementById("btn-modal-error-dismiss");
  const retryBtn = document.getElementById("btn-modal-error-retry");

  if (closeBtn) closeBtn.addEventListener("click", closeErrorPopup);
  if (dismissBtn) dismissBtn.addEventListener("click", closeErrorPopup);

  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      const cb = pendingRetryCallback;
      closeErrorPopup();
      if (typeof cb === "function") cb();
    });
  }
}

function showErrorPopup(title, message, onRetry = null) {
  hideProgress();
  const modal = document.getElementById("modal-error");
  const titleEl = document.getElementById("modal-error-title");
  const msgEl = document.getElementById("modal-error-message");
  const retryBtn = document.getElementById("btn-modal-error-retry");

  if (titleEl) titleEl.textContent = title || "Extraction Notice";
  if (msgEl) msgEl.textContent = message || "An unexpected error occurred. Please try again.";

  pendingRetryCallback = onRetry;
  if (retryBtn) {
    retryBtn.style.display = (typeof onRetry === "function") ? "inline-flex" : "none";
  }

  if (modal) modal.style.display = "flex";
}

function closeErrorPopup() {
  const modal = document.getElementById("modal-error");
  if (modal) modal.style.display = "none";
  pendingRetryCallback = null;
}

window.showErrorPopup = showErrorPopup;
window.closeErrorPopup = closeErrorPopup;

// ================================================================
// 5. How to Use Section (Multilingual Setup)
// ================================================================
function initHowToUseSection() {
  const langSelect = document.getElementById("howtouse-lang-select");
  if (langSelect) {
    langSelect.addEventListener("change", (e) => {
      if (window.renderHowToUseLanguage) {
        window.renderHowToUseLanguage(e.target.value);
      }
    });
  }

  // Pre-render default English on load
  if (window.initHowToUse) {
    window.initHowToUse();
  }
}

// ================================================================
// 6. Filter Listeners for Explorer Table
// ================================================================
function setupFiltersListeners() {
  const ids = ["filter-search", "filter-sentiment", "filter-emotion", "filter-intent", "filter-moderation", "filter-sort"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener(el.tagName === "INPUT" ? "input" : "change", () => {
        if (typeof applyCommentFilters === "function") applyCommentFilters();
      });
    }
  });

  const btnPrev = document.getElementById("btn-page-prev");
  const btnNext = document.getElementById("btn-page-next");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        if (typeof renderCommentTableRows === "function") renderCommentTableRows();
      }
    });
  }
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      currentPage++;
      if (typeof renderCommentTableRows === "function") renderCommentTableRows();
    });
  }
}

// ================================================================
// 7. Modals
// ================================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.style.display = "flex";
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.style.display = "none";
}

// ================================================================
// 8. Progress Overlay
// ================================================================
function showProgress(title, step) {
  const overlay = document.getElementById("progress-overlay");
  if (!overlay) return;
  const titleEl = document.getElementById("progress-title");
  const stepEl = document.getElementById("progress-step");
  if (titleEl) titleEl.textContent = title || "Analyzing Comments";
  if (stepEl) stepEl.textContent = step || "Processing AI intelligence...";

  const stepsList = document.getElementById("progress-steps-list");
  if (stepsList) stepsList.innerHTML = "";
  const cancelBtn = document.getElementById("btn-progress-cancel");
  if (cancelBtn) cancelBtn.style.display = "none";
  const countEl = document.getElementById("progress-count");
  if (countEl) { countEl.style.display = "none"; countEl.textContent = ""; }
  overlay.style.display = "flex";
}

function hideProgress() {
  const overlay = document.getElementById("progress-overlay");
  if (overlay) overlay.style.display = "none";
  const cancelBtn = document.getElementById("btn-progress-cancel");
  if (cancelBtn) cancelBtn.style.display = "none";
}

if (typeof window.cancelCurrentFetch === "undefined") {
  window.cancelCurrentFetch = function () { hideProgress(); };
}

// ================================================================
// 9. Premium Animated Toast Notifications
// ================================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icons = {
    success: `<span style="color:var(--accent-emerald, #10b981); font-weight:bold; font-size:16px;">&#10003;</span>`,
    error: `<span style="color:var(--accent-rose, #f43f5e); font-weight:bold; font-size:16px;">&#9888;</span>`,
    warning: `<span style="color:var(--accent-gold, #f59e0b); font-weight:bold; font-size:16px;">&#9888;</span>`,
    info: `<span style="color:var(--accent-blue, #38bdf8); font-weight:bold; font-size:16px;">&#8505;</span>`
  };

  toast.innerHTML = `
    ${icons[type] || icons.info}
    <div style="flex-grow:1; font-size:13px; line-height:1.4;">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

// ================================================================
// 10. API Fetch Helpers
// ================================================================
async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiDelete(url) {
  const res = await fetch(url, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
