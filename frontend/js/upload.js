/**
 * SocialPlus.ai — File Upload & Manual Input Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // Setup all 4 drop zones
  setupDropZone("yt-drop-zone", "yt-file-input", "yt-file-meta", "btn-yt-upload-analyze", "youtube");
  setupDropZone("ig-drop-zone", "ig-file-input", "ig-file-meta", "btn-ig-upload-analyze", "instagram");
  setupDropZone("fb-drop-zone", "fb-file-input", "fb-file-meta", "btn-fb-upload-analyze", "facebook");
  setupDropZone("ecom-drop-zone", "ecom-file-input", "ecom-file-meta", "btn-ecom-upload-analyze", "ecommerce");

  // Manual Analysis Submit Button
  const btnManual = document.getElementById("btn-run-manual-analysis");
  if (btnManual) {
    btnManual.addEventListener("click", async () => {
      const text = document.getElementById("manual-text-input").value.trim();
      const title = document.getElementById("manual-title-input").value.trim() || "Manual Analysis";

      if (!text) {
        showToast("Please enter at least one comment.", "warning");
        return;
      }

      closeModal("modal-manual");
      showProgress("Analyzing Comments", "Running AI/ML Intelligence Pipeline...");

      try {
        const res = await apiPost("/api/analysis/manual", {
          title: title,
          platform: "manual",
          raw_text: text
        });

        if (res.success && res.analysis) {
          showToast(res.message, "success");
          renderDashboard(res.analysis);
        } else {
          showToast(res.message || "Failed to analyze comments.", "error");
        }
      } catch (err) {
        showToast(`Analysis failed: ${err.message}`, "error");
      } finally {
        hideProgress();
      }
    });
  }
});

function setupDropZone(dropZoneId, fileInputId, metaId, uploadBtnId, platform) {
  const dropZone = document.getElementById(dropZoneId);
  const fileInput = document.getElementById(fileInputId);
  const metaDisplay = document.getElementById(metaId);
  const uploadBtn = document.getElementById(uploadBtnId);

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0], metaDisplay, uploadBtn);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0], metaDisplay, uploadBtn);
    }
  });

  if (uploadBtn) {
    uploadBtn.addEventListener("click", async () => {
      if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a file to upload.", "warning");
        return;
      }

      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file);
      formData.append("platform", platform);
      formData.append("auto_analyze", "true");

      showProgress("Uploading & Parsing File", `Reading ${file.name} and executing AI intelligence pipeline...`);
      uploadBtn.disabled = true;
      try {
        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData
        });

        const res = await response.json();

        if (res.success && res.analysis) {
          showToast(res.message, "success");
          renderDashboard(res.analysis);
        } else {
          showToast(res.message || "Upload processing failed.", "error");
        }
      } catch (err) {
        showToast(`Upload failed: ${err.message}`, "error");
      } finally {
        hideProgress();
        uploadBtn.disabled = false;
      }
    });
  }
}

function handleFileSelected(file, metaDisplay, uploadBtn) {
  if (!file) return;
  const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
  metaDisplay.innerHTML = `<b>Selected:</b> ${file.name} (${sizeMb} MB)`;
  if (uploadBtn) {
    uploadBtn.disabled = false;
  }
}

