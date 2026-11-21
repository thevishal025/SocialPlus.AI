/**
 * SocialPlus.ai — Meta Analyzer Controller (Instagram & Facebook)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Platform selector: Instagram vs Facebook
  setupSegmentedTabs("meta-platform-tabs", (platform) => {
    const igView = document.getElementById("meta-view-instagram");
    const fbView = document.getElementById("meta-view-facebook");
    if (igView) igView.style.display = platform === "instagram" ? "block" : "none";
    if (fbView) fbView.style.display = platform === "facebook" ? "block" : "none";
  });

  document.querySelectorAll("[data-platform-choice]").forEach(card => {
    card.addEventListener("click", () => {
      const platform = card.dataset.platformChoice;
      const hiddenTab = document.querySelector(`#meta-platform-tabs [data-platform="${platform}"]`);
      if (hiddenTab) hiddenTab.click();
      document.querySelectorAll("[data-platform-choice]").forEach(el =>
        el.classList.toggle("active", el === card)
      );
    });
  });

  // Instagram Sub-tabs
  setupSegmentedTabs("ig-tabs", (mode) => {
    const apiV = document.getElementById("ig-view-api");
    const pubV = document.getElementById("ig-view-public");
    const uplV = document.getElementById("ig-view-upload");
    if (apiV) apiV.style.display = mode === "api" ? "block" : "none";
    if (pubV) pubV.style.display = mode === "public" ? "block" : "none";
    if (uplV) uplV.style.display = mode === "upload" ? "block" : "none";
  });

  // Facebook Sub-tabs
  setupSegmentedTabs("fb-tabs", (mode) => {
    const apiV = document.getElementById("fb-view-api");
    const pubV = document.getElementById("fb-view-public");
    const uplV = document.getElementById("fb-view-upload");
    if (apiV) apiV.style.display = mode === "api" ? "block" : "none";
    if (pubV) pubV.style.display = mode === "public" ? "block" : "none";
    if (uplV) uplV.style.display = mode === "upload" ? "block" : "none";
  });

  // 1. Instagram API Fetch
  const btnIgFetchApi = document.getElementById("btn-ig-fetch-api");
  let isIgApiFetching = false;
  if (btnIgFetchApi) {
    btnIgFetchApi.addEventListener("click", async () => {
      if (isIgApiFetching) return;
      const postUrl = document.getElementById("ig-post-input").value.trim();
      const token = (document.getElementById("ig-token-input") || {value: ""}).value.trim();

      if (!postUrl) {
        showToast("Please enter an Instagram post URL or Media ID.", "warning");
        return;
      }

      isIgApiFetching = true;
      btnIgFetchApi.disabled = true;
      const origText = btnIgFetchApi.textContent;
      btnIgFetchApi.textContent = "Fetching Comments…";

      showProgress("Connecting to Instagram API", "Fetching comments from Meta Graph API...");
      try {
        const res = await apiPost("/api/instagram/api/fetch", {
          post_url_or_id: postUrl,
          access_token: token || null,
          max_comments: 200
        });

        if (res.success && res.analysis) {
          showToast(res.message || "Comments fetched successfully!", "success");
          renderDashboard(res.analysis);
        } else {
          const msg = res.message || "Could not retrieve Instagram comments.";
          if (typeof showErrorPopup === "function") {
            showErrorPopup("Instagram Extraction Notice", msg, () => btnIgFetchApi.click());
          } else {
            showToast(msg, "error");
          }
        }
      } catch (err) {
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Instagram Request Failed", err.message || "Failed to connect to Meta API.", () => btnIgFetchApi.click());
        } else {
          showToast(`Error: ${err.message}`, "error");
        }
      } finally {
        hideProgress();
        isIgApiFetching = false;
        btnIgFetchApi.disabled = false;
        btnIgFetchApi.textContent = origText;
      }
    });
  }

  // 2. Instagram Public Fetch
  const btnIgFetchPublic = document.getElementById("btn-ig-fetch-public");
  let isIgPubFetching = false;
  if (btnIgFetchPublic) {
    btnIgFetchPublic.addEventListener("click", async () => {
      if (isIgPubFetching) return;
      const postUrl = document.getElementById("ig-public-input").value.trim();
      if (!postUrl) {
        showToast("Enter Instagram URL.", "warning");
        return;
      }

      isIgPubFetching = true;
      btnIgFetchPublic.disabled = true;
      const origText = btnIgFetchPublic.textContent;
      btnIgFetchPublic.textContent = "Checking Route…";

      showProgress("Universal Scraper Engine", "Extracting post details and public comments from Instagram...");
      try {
        const res = await apiPost("/api/instagram/public/fetch", {
          post_url_or_id: postUrl,
          max_comments: 50
        });

        if (res.success && res.analysis) {
          showToast(res.message || "Comments extracted successfully!", "success");
          renderDashboard(res.analysis);
        } else {
          const box = document.getElementById("ig-public-result-box");
          if (box) {
            box.style.display = "block";
            box.innerHTML = `
              <div class="status-banner warning" style="display:block;">
                <h4 style="font-weight:700; margin-bottom:4px;">Instagram Extraction Notice</h4>
                <p style="margin-bottom:8px;">${res.message}</p>
                ${res.post_metadata && res.post_metadata.caption ? `<div style="font-size:12px; margin-bottom:10px; padding:8px; background:rgba(255,255,255,0.04); border-radius:4px;"><b>Caption:</b> ${escapeHtml(res.post_metadata.caption.slice(0, 160))}...</div>` : ""}
                <button class="btn-primary" style="padding:6px 12px; font-size:12px;" onclick="switchTab('ig-tabs', 'upload')">Upload Instagram File</button>
              </div>
            `;
          }
          if (typeof showErrorPopup === "function") {
            showErrorPopup("Instagram Public Notice", res.message || "Direct public retrieval restricted.", () => btnIgFetchPublic.click());
          } else {
            showToast(res.message || "Public extraction restricted.", "warning");
          }
        }
      } catch (err) {
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Extraction Failed", err.message || "Failed to inspect public post.", () => btnIgFetchPublic.click());
        } else {
          showToast(`Error: ${err.message}`, "error");
        }
      } finally {
        hideProgress();
        isIgPubFetching = false;
        btnIgFetchPublic.disabled = false;
        btnIgFetchPublic.textContent = origText;
      }
    });
  }

  // 3. Facebook API Fetch
  const btnFbFetchApi = document.getElementById("btn-fb-fetch-api");
  let isFbApiFetching = false;
  if (btnFbFetchApi) {
    btnFbFetchApi.addEventListener("click", async () => {
      if (isFbApiFetching) return;
      const postUrl = document.getElementById("fb-post-input").value.trim();
      const token = (document.getElementById("fb-token-input") || {value: ""}).value.trim();

      if (!postUrl) {
        showToast("Please enter a Facebook Post URL or ID.", "warning");
        return;
      }

      isFbApiFetching = true;
      btnFbFetchApi.disabled = true;
      const origText = btnFbFetchApi.textContent;
      btnFbFetchApi.textContent = "Fetching Comments…";

      showProgress("Connecting to Facebook Page API", "Retrieving comments via Graph API...");
      try {
        const res = await apiPost("/api/facebook/api/fetch", {
          post_url_or_id: postUrl,
          access_token: token || null,
          max_comments: 200
        });

        if (res.success && res.analysis) {
          showToast(res.message || "Facebook comments analyzed successfully!", "success");
          renderDashboard(res.analysis);
        } else {
          const msg = res.message || "Failed to fetch Facebook comments.";
          if (typeof showErrorPopup === "function") {
            showErrorPopup("Facebook API Notice", msg, () => btnFbFetchApi.click());
          } else {
            showToast(msg, "error");
          }
        }
      } catch (err) {
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Facebook Request Failed", err.message || "Failed to connect to Facebook API.", () => btnFbFetchApi.click());
        } else {
          showToast(`Error: ${err.message}`, "error");
        }
      } finally {
        hideProgress();
        isFbApiFetching = false;
        btnFbFetchApi.disabled = false;
        btnFbFetchApi.textContent = origText;
      }
    });
  }

  // 4. Facebook Public Fetch
  const btnFbFetchPublic = document.getElementById("btn-fb-fetch-public");
  let isFbPubFetching = false;
  if (btnFbFetchPublic) {
    btnFbFetchPublic.addEventListener("click", async () => {
      if (isFbPubFetching) return;
      const postUrl = document.getElementById("fb-public-input").value.trim();
      if (!postUrl) {
        showToast("Enter Facebook Post URL.", "warning");
        return;
      }

      isFbPubFetching = true;
      btnFbFetchPublic.disabled = true;
      const origText = btnFbFetchPublic.textContent;
      btnFbFetchPublic.textContent = "Checking Route…";

      showProgress("Universal Scraper Engine", "Extracting post details and public comments from Facebook...");
      try {
        const res = await apiPost("/api/facebook/public/fetch", {
          post_url_or_id: postUrl,
          max_comments: 50
        });

        if (res.success && res.analysis) {
          showToast(res.message || "Comments extracted successfully!", "success");
          renderDashboard(res.analysis);
        } else {
          const box = document.getElementById("fb-public-result-box");
          if (box) {
            box.style.display = "block";
            box.innerHTML = `
              <div class="status-banner warning" style="display:block;">
                <h4 style="font-weight:700; margin-bottom:4px;">Facebook Extraction Notice</h4>
                <p style="margin-bottom:8px;">${(res.message || "").replace(/\n/g, "<br>")}</p>
                ${res.post_metadata && res.post_metadata.caption ? `<div style="font-size:12px; margin-bottom:10px; padding:8px; background:rgba(255,255,255,0.04); border-radius:4px;"><b>Caption:</b> ${escapeHtml(res.post_metadata.caption.slice(0, 160))}...</div>` : ""}
                <button class="btn-primary" style="padding:6px 12px; font-size:12px;" onclick="switchTab('fb-tabs', 'upload')">Upload Facebook File</button>
              </div>
            `;
          }
          if (typeof showErrorPopup === "function") {
            showErrorPopup("Facebook Public Notice", res.message || "Public extraction restricted.", () => btnFbFetchPublic.click());
          } else {
            showToast(res.message || "Public extraction restricted.", "warning");
          }
        }
      } catch (err) {
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Extraction Failed", err.message || "Failed to inspect public post.", () => btnFbFetchPublic.click());
        } else {
          showToast(`Error: ${err.message}`, "error");
        }
      } finally {
        hideProgress();
        isFbPubFetching = false;
        btnFbFetchPublic.disabled = false;
        btnFbFetchPublic.textContent = origText;
      }
    });
  }

  // 5. Connect OAuth Buttons
  const btnIgConnect = document.getElementById("btn-ig-connect-oauth");
  if (btnIgConnect) {
    btnIgConnect.addEventListener("click", async () => {
      try {
        const res = await apiPost("/api/instagram/api/connect", {});
        if (res.connected && res.auth_url) {
          window.open(res.auth_url, "_blank");
        } else {
          showToast(res.message || "Configure META_APP_ID in .env first.", "warning");
        }
      } catch (e) {
        showToast("Could not generate OAuth connection.", "error");
      }
    });
  }

  const btnFbConnect = document.getElementById("btn-fb-connect-oauth");
  if (btnFbConnect) {
    btnFbConnect.addEventListener("click", async () => {
      try {
        const res = await apiPost("/api/facebook/api/connect", {});
        if (res.connected && res.auth_url) {
          window.open(res.auth_url, "_blank");
        } else {
          showToast(res.message || "Configure META_APP_ID in .env first.", "warning");
        }
      } catch (e) {
        showToast("Could not generate OAuth connection.", "error");
      }
    });
  }
});

