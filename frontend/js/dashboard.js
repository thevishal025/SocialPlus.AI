/**
 * SocialPlus.ai — Complete Dashboard Controller
 */

let currentAnalysisData = null;
let filteredCommentsList = [];
let currentPage = 1;
const PAGE_SIZE = 20;

function renderDashboard(data) {
  if (!data) return;
  currentAnalysisData = data;
  filteredCommentsList = [...(data.comments || [])];
  currentPage = 1;

  // Open dedicated separate Analysis Results page
  if (typeof showView === "function") {
    showView("dashboard");
  } else {
    const homeSection = document.getElementById("section-home");
    const dashSection = document.getElementById("section-dashboard");
    if (homeSection) homeSection.style.display = "none";
    if (dashSection) dashSection.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // 1. Header Information
  document.getElementById("dash-heading-title").textContent = data.title || "Comment Intelligence Analysis";
  document.getElementById("dash-meta-platform").textContent = `Platform: ${(data.platform || "general").toUpperCase()}`;
  document.getElementById("dash-meta-source").textContent = `Mode: ${(data.source_mode || "api").toUpperCase()}`;
  document.getElementById("dash-meta-date").textContent = `Date: ${data.created_at ? data.created_at.split("T")[0] : "Today"}`;
  document.getElementById("dash-meta-time").textContent = `Time: ${data.execution_time_sec || 0.5}s`;

  // 2. Set Report Download Links
  const aid = data.id;
  document.getElementById("btn-dl-pdf").href = `/api/report/${aid}/pdf`;
  document.getElementById("btn-dl-html").href = `/api/report/${aid}/html`;
  document.getElementById("btn-dl-excel").href = `/api/report/${aid}/excel`;
  document.getElementById("btn-dl-csv").href = `/api/report/${aid}/csv`;
  document.getElementById("btn-dl-json").href = `/api/report/${aid}/json`;

  // Render Product Card if product intelligence metadata is present
  const prodData = (data.source_metadata && data.source_metadata.product) ? data.source_metadata.product : null;
  renderProductCard(prodData);

  // 3. Main Statistics Cards
  const summary = data.summary || {};
  const sentDist = summary.sentiment_distribution || {};
  const sentCounts = summary.sentiment_counts || {};

  document.getElementById("stat-total").textContent = data.comment_count || 0;
  document.getElementById("stat-positive").textContent = `${sentDist.Positive || 0}%`;
  document.getElementById("stat-pos-count").textContent = `${sentCounts.Positive || 0} comments`;

  document.getElementById("stat-negative").textContent = `${sentDist.Negative || 0}%`;
  document.getElementById("stat-neg-count").textContent = `${sentCounts.Negative || 0} comments`;

  const neuMixPct = ((sentDist.Neutral || 0) + (sentDist.Mixed || 0)).toFixed(1);
  const neuMixCnt = (sentCounts.Neutral || 0) + (sentCounts.Mixed || 0);
  document.getElementById("stat-neutral").textContent = `${neuMixPct}%`;
  document.getElementById("stat-neu-count").textContent = `${neuMixCnt} comments`;

  const modDist = summary.moderation_distribution || {};
  document.getElementById("stat-spam").textContent = modDist.Spam || 0;
  document.getElementById("stat-toxic").textContent = modDist.Toxic || 0;
  document.getElementById("stat-confidence").textContent = `${Math.round((summary.average_confidence || 0.8) * 100)}%`;

  // Rating card
  const ratingCard = document.getElementById("stat-rating-card");
  if (summary.average_rating) {
    ratingCard.style.display = "block";
    document.getElementById("stat-rating").textContent = `${summary.average_rating} / 5`;
  } else {
    ratingCard.style.display = "none";
  }

  // 4. Sentiment Spectrum Progress Bar
  renderSentimentSpectrumBar(sentDist);

  // 5. Render Chart.js Visuals
  try {
    ChartManager.renderSentimentDonut("chart-sentiment-donut", sentDist);
    ChartManager.renderEmotionsBar("chart-emotions-bar", summary.emotion_distribution || {});
    ChartManager.renderIntentBar("chart-intent-bar", summary.intent_distribution || {});
    ChartManager.renderModerationChart("chart-moderation-doughnut", modDist);
  } catch (err) {
    console.warn("Chart rendering warning:", err);
  }

  // 6. Product Aspects Table
  try { renderAspectsTable(data.aspects || {}); } catch (_) { }

  // 7. Emoji Intelligence Grid
  try { renderEmojiGrid(data.emojis || {}); } catch (_) { }

  // 8. Word Cloud
  try { renderWordCloud(data.keywords || {}); } catch (_) { }

  // 9. Comment Explorer Table
  try { applyCommentFilters(); } catch (_) { }
}

function renderSentimentSpectrumBar(dist) {
  const container = document.getElementById("sentiment-progress-bar");
  const legend = document.getElementById("sentiment-legend");
  container.innerHTML = "";
  legend.innerHTML = "";

  const cats = [
    { key: "Positive", color: "#16a34a", label: "Positive" },
    { key: "Negative", color: "#dc2626", label: "Negative" },
    { key: "Neutral", color: "#94a3b8", label: "Neutral" },
    { key: "Mixed", color: "#f59e0b", label: "Mixed" },
    { key: "Sarcastic", color: "#9333ea", label: "Sarcastic" },
  ];

  cats.forEach(c => {
    const val = dist[c.key] || 0;
    if (val > 0) {
      const seg = document.createElement("div");
      seg.className = `sp-seg ${c.key.toLowerCase()}`;
      seg.style.width = `${val}%`;
      seg.title = `${c.label}: ${val}%`;
      container.appendChild(seg);

      const legItem = document.createElement("div");
      legItem.style.display = "flex";
      legItem.style.alignItems = "center";
      legItem.style.gap = "4px";
      legItem.innerHTML = `<span style="width:10px; height:10px; border-radius:2px; background:${c.color};"></span> ${c.label} (${val}%)`;
      legend.appendChild(legItem);
    }
  });
}

function renderAspectsTable(aspectsData) {
  const tbody = document.getElementById("aspects-table-body");
  const section = document.getElementById("section-aspects");
  const pill = document.getElementById("aspect-satisfaction-pill");
  tbody.innerHTML = "";

  const aspects = aspectsData.aspects || [];
  if (aspects.length === 0) {
    section.style.display = "none";
    return;
  }
  section.style.display = "block";
  pill.textContent = `Satisfaction Index: ${aspectsData.overall_satisfaction_score || 80}%`;

  aspects.forEach(asp => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><b>${asp.aspect}</b></td>
      <td>${asp.mentions}</td>
      <td>
        <div class="aspect-bar-wrap">
          <div class="aspect-bar-fill" style="width: ${asp.positive_pct}%;"></div>
        </div>
      </td>
      <td style="color:#16a34a; font-weight:700;">${asp.positive_pct}%</td>
      <td style="color:#dc2626; font-weight:700;">${asp.negative_pct}%</td>
      <td style="color:var(--text-secondary); max-width:300px; font-size:12px;">
        ${asp.sample_positive ? `"${asp.sample_positive.slice(0, 70)}..."` : (asp.sample_negative ? `"${asp.sample_negative.slice(0, 70)}..."` : "—")}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderEmojiGrid(emojisData) {
  const container = document.getElementById("emoji-grid-container");
  container.innerHTML = "";
  const topList = emojisData.top_emojis || [];

  if (topList.length === 0) {
    container.innerHTML = `<div style="grid-column:1/-1; color:var(--text-muted); font-size:13px;">No emojis found in analyzed comments.</div>`;
    return;
  }

  topList.slice(0, 10).forEach(em => {
    const card = document.createElement("div");
    card.className = "emoji-pill-card";
    card.innerHTML = `
      <span class="emoji-char">${em.emoji}</span>
      <div>
        <div class="emoji-data-name">${em.name}</div>
        <div class="emoji-data-cnt">${em.frequency} (${em.percentage}%)</div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderWordCloud(keywordData) {
  const container = document.getElementById("wordcloud-container");
  container.innerHTML = "";
  const words = keywordData.wordcloud || [];

  if (words.length === 0) {
    container.innerHTML = `<div style="color:var(--text-muted); font-size:13px;">No keywords extracted.</div>`;
    return;
  }

  const maxVal = Math.max(...words.map(w => w.value), 1);
  words.slice(0, 35).forEach(item => {
    const tag = document.createElement("span");
    tag.className = "wordcloud-tag";
    const size = Math.max(12, Math.min(28, 12 + (item.value / maxVal) * 16));
    tag.style.fontSize = `${size}px`;
    tag.textContent = item.text;
    tag.title = `Mentions: ${item.value}`;
    container.appendChild(tag);
  });
}

// ================================================================
// Comment Explorer Table & Filters
// ================================================================
function applyCommentFilters() {
  if (!currentAnalysisData) return;
  const comments = currentAnalysisData.comments || [];

  const query = (document.getElementById("filter-search").value || "").toLowerCase().trim();
  const sentiment = document.getElementById("filter-sentiment").value;
  const emotion = document.getElementById("filter-emotion").value;
  const intent = document.getElementById("filter-intent").value;
  const moderation = document.getElementById("filter-moderation").value;
  const sortBy = document.getElementById("filter-sort").value;

  filteredCommentsList = comments.filter(c => {
    if (query && !c.text.toLowerCase().includes(query) && !c.author.toLowerCase().includes(query)) {
      return false;
    }
    if (sentiment !== "all" && c.sentiment !== sentiment) return false;
    if (emotion !== "all" && c.primary_emotion !== emotion) return false;
    if (intent !== "all" && c.intent !== intent) return false;
    if (moderation !== "all" && c.moderation_status !== moderation) return false;
    return true;
  });

  // Sort
  if (sortBy === "likes") {
    filteredCommentsList.sort((a, b) => (b.likes || 0) - (a.likes || 0));
  } else if (sortBy === "rating") {
    filteredCommentsList.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  } else if (sortBy === "confidence") {
    filteredCommentsList.sort((a, b) => (b.sentiment_confidence || 0) - (a.sentiment_confidence || 0));
  }

  currentPage = 1;
  renderCommentTableRows();
}

function renderCommentTableRows() {
  const tbody = document.getElementById("comments-table-body");
  const countBadge = document.getElementById("explorer-count-badge");
  tbody.innerHTML = "";

  const total = filteredCommentsList.length;
  countBadge.textContent = `Showing ${total} comments`;

  if (total === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:30px;">No comments matching the selected filter criteria.</td></tr>`;
    renderPagination(0);
    return;
  }

  const startIdx = (currentPage - 1) * PAGE_SIZE;
  const pageItems = filteredCommentsList.slice(startIdx, startIdx + PAGE_SIZE);

  pageItems.forEach(c => {
    const tr = document.createElement("tr");

    const sentClass = (c.sentiment || "Neutral").toLowerCase();
    const modClass = (c.moderation_status || "Safe").toLowerCase().replace(/\s+/g, "");

    tr.innerHTML = `
      <td class="comment-author-cell">${escapeHtml(c.author || "Anonymous")}</td>
      <td><span class="badge ${sentClass}">${c.sentiment}</span></td>
      <td><span style="font-size:12px; font-weight:600;">${c.primary_emotion || "Neutral"}</span></td>
      <td><span style="font-size:12px; color:var(--text-secondary);">${c.intent || "General"}</span></td>
      <td><span class="badge ${modClass}">${c.moderation_status || "Safe"}</span></td>
      <td class="comment-text-cell">${escapeHtml(c.text)}</td>
      <td>
        <button class="btn-outline" style="padding:4px 8px; font-size:11px;" onclick="viewCommentDetails('${c.id}')">Inspect</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  renderPagination(total);
}

function renderPagination(total) {
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  document.getElementById("pagination-info").textContent = `Showing page ${currentPage} of ${totalPages} (${total} items)`;

  const prevBtn = document.getElementById("btn-page-prev");
  const nextBtn = document.getElementById("btn-page-next");
  const pagesWrap = document.getElementById("pagination-pages");

  prevBtn.disabled = currentPage <= 1;
  nextBtn.disabled = currentPage >= totalPages;

  pagesWrap.innerHTML = "";
  for (let i = 1; i <= Math.min(totalPages, 5); i++) {
    const pBtn = document.createElement("button");
    pBtn.className = `page-btn ${i === currentPage ? "active" : ""}`;
    pBtn.textContent = i;
    pBtn.onclick = () => { currentPage = i; renderCommentTableRows(); };
    pagesWrap.appendChild(pBtn);
  }
}

function viewCommentDetails(commentId) {
  if (!currentAnalysisData) return;
  const comment = (currentAnalysisData.comments || []).find(c => c.id === commentId);
  if (!comment) return;

  const modalBody = document.getElementById("comment-detail-body");
  modalBody.innerHTML = `
    <div style="background:#f8fafc; padding:14px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:14px;">
      <div style="font-size:11px; color:#64748b; margin-bottom:4px;"><b>AUTHOR:</b> ${escapeHtml(comment.author)} &nbsp;|&nbsp; <b>PLATFORM:</b> ${comment.platform}</div>
      <div style="font-size:14px; color:#0f172a; font-weight:500;">"${escapeHtml(comment.text)}"</div>
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px;">
      <div style="padding:10px; border:1px solid #e2e8f0; border-radius:6px;">
        <span style="font-size:11px; color:#64748b; font-weight:700;">SENTIMENT CLASSIFICATION</span>
        <div style="font-size:16px; font-weight:800; color:#2563eb; margin-top:2px;">${comment.sentiment} (${Math.round((comment.sentiment_confidence || 0) * 100)}% confidence)</div>
        <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Signals:</b> ${(comment.sentiment_signals || []).join(", ") || "Standard polarity weighting"}</div>
      </div>

      <div style="padding:10px; border:1px solid #e2e8f0; border-radius:6px;">
        <span style="font-size:11px; color:#64748b; font-weight:700;">AUTO-MODERATION STATUS</span>
        <div style="font-size:16px; font-weight:800; color:#059669; margin-top:2px;">${comment.moderation_status}</div>
        <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Spam Prob:</b> ${comment.spam_probability} &nbsp;|&nbsp; <b>Toxicity:</b> ${comment.toxicity_score}</div>
      </div>
    </div>

    <div style="padding:10px; border:1px solid #e2e8f0; border-radius:6px;">
      <span style="font-size:11px; color:#64748b; font-weight:700;">INTENT &amp; EMOTION</span>
      <div style="margin-top:4px; font-size:13px;">
        <b>Primary Emotion:</b> ${comment.primary_emotion} &nbsp;|&nbsp; <b>Intent:</b> ${comment.intent}
      </div>
      <div style="font-size:12px; color:#64748b; margin-top:4px;">
        <b>Reasons / Notes:</b> ${(comment.moderation_reasons || []).join("; ") || "Complies with community standards"}
      </div>
    </div>
  `;

  openModal("modal-comment-detail");
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function renderProductCard(product) {
  const card = document.getElementById("dash-product-card");
  if (!card) return;
  if (!product) {
    card.style.display = "none";
    card.innerHTML = "";
    return;
  }

  card.style.display = "block";

  // ── 1. PRODUCT OVERVIEW ──
  const images = (product.product_images && product.product_images.length > 0) ? product.product_images : [];
  const primaryImg = images.length > 0 ? images[0] : null;
  const price = product.current_price != null ? `₹${Number(product.current_price).toLocaleString('en-IN')}` : "Not available";
  const origPrice = product.original_price != null ? `₹${Number(product.original_price).toLocaleString('en-IN')}` : null;
  const discount = product.discount_percent ? `${product.discount_percent}% off` : (product.discount || null);
  const brand = product.brand || "Not available";
  const category = (product.category || "General").toUpperCase();
  const currency = product.currency || "INR";
  const availability = product.availability || "In Stock";
  const rating = product.rating ? `★ ${product.rating} / 5.0` : "Not available";
  const reportedReviews = (product.total_reviews_count || product.review_count) ? Number(product.total_reviews_count || product.review_count).toLocaleString() : "Not available";

  // Gallery Thumbnails
  const thumbsHtml = images.length > 1 ? `
    <div style="display:flex; gap:6px; margin-top:8px; overflow-x:auto; padding-bottom:4px;">
      ${images.map((img, i) => `
        <div onclick="document.getElementById('pdetail-main-img').src='${escapeHtml(img)}'" 
             style="width:44px; height:44px; border:1px solid #cbd5e1; border-radius:4px; overflow:hidden; cursor:pointer; flex-shrink:0; background:#fff; display:flex; align-items:center; justify-content:center;">
          <img src="${escapeHtml(img)}" style="max-width:100%; max-height:100%; object-fit:contain;" onerror="this.parentElement.style.display='none'">
        </div>
      `).join("")}
    </div>
  ` : "";

  // ── 2. PRODUCT DESCRIPTION ──
  const descData = product.description_data || {};
  const fullDesc = descData.description || product.description || "Not available";
  const highlights = (descData.highlights && descData.highlights.length > 0) ? descData.highlights : (descData.features || []);
  const manufacturer = descData.manufacturer || "Not available";

  const highlightsHtml = highlights.length > 0 ? `
    <ul style="margin:6px 0 0 18px; padding:0; font-size:12px; color:#334155; line-height:1.6;">
      ${highlights.map(h => `<li>${escapeHtml(String(h))}</li>`).join("")}
    </ul>
  ` : `<div style="font-size:12px; color:#94a3b8; font-style:italic;">Not available</div>`;

  // ── 3. TECHNICAL SPECIFICATIONS ──
  const rawSpecs = (product.specifications && product.specifications.raw) ? product.specifications.raw : (product.specifications || {});
  const catSpecs = product.category_specific_specs || (product.specifications ? (product.specifications.category_specific || {}) : {});

  function getSpecVal(keys) {
    for (const k of keys) {
      if (catSpecs[k] && String(catSpecs[k]).trim()) return String(catSpecs[k]).trim();
      for (const [rk, rv] of Object.entries(rawSpecs)) {
        if (rk.toLowerCase() === k.toLowerCase() || rk.toLowerCase().includes(k.toLowerCase())) {
          if (String(rv).trim()) return String(rv).trim();
        }
      }
    }
    return "Not available";
  }

  let techSpecsFields = [];
  if (category === "MOBILE" || category === "ELECTRONICS") {
    techSpecsFields = [
      { label: "RAM", val: getSpecVal(["RAM", "Memory"]) },
      { label: "Storage", val: getSpecVal(["ROM", "Storage", "Internal Storage"]) },
      { label: "Processor", val: getSpecVal(["Processor", "CPU", "Chipset"]) },
      { label: "Display", val: getSpecVal(["Display", "Screen", "Resolution"]) },
      { label: "Camera", val: getSpecVal(["Camera", "Primary Camera", "Rear Camera"]) },
      { label: "Battery", val: getSpecVal(["Battery", "Battery Capacity"]) },
      { label: "Operating System", val: getSpecVal(["Operating System", "OS"]) },
      { label: "Connectivity", val: getSpecVal(["Connectivity", "Network Type", "5G"]) },
      { label: "Warranty", val: getSpecVal(["Warranty", "Warranty Summary"]) }
    ];
  } else if (category === "FASHION") {
    techSpecsFields = [
      { label: "Material / Fabric", val: getSpecVal(["Fabric", "Material", "Fabric Care"]) },
      { label: "Size", val: getSpecVal(["Size", "Fit/Shape"]) },
      { label: "Colour", val: getSpecVal(["Color", "Colour", "Shade"]) },
      { label: "Fit", val: getSpecVal(["Fit", "Fit/Shape"]) },
      { label: "Pattern", val: getSpecVal(["Pattern", "Design"]) },
      { label: "Care Instructions", val: getSpecVal(["Care Instructions", "Wash Care", "Fabric Care"]) }
    ];
  } else {
    techSpecsFields = [
      { label: "Dimensions", val: getSpecVal(["Dimensions", "Width", "Height", "Length"]) },
      { label: "Weight", val: getSpecVal(["Weight", "Item Weight"]) },
      { label: "Capacity", val: getSpecVal(["Capacity", "Volume"]) },
      { label: "Material", val: getSpecVal(["Material", "Primary Material"]) },
      { label: "Features", val: getSpecVal(["Features", "Special Features"]) },
      { label: "Additional Specifications", val: getSpecVal(["Model", "Specification", "Type"]) }
    ];
  }

  const techSpecsHtml = techSpecsFields.map(f => `
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 12px;">
      <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase;">${escapeHtml(f.label)}</div>
      <div style="font-size:13px; font-weight:600; color:${f.val === 'Not available' ? '#94a3b8' : '#0f172a'}; margin-top:2px;">${escapeHtml(f.val)}</div>
    </div>
  `).join("");

  // ── 4. PRODUCT VARIANTS ──
  const vData = product.variants_data || {};
  const sizesList = (vData.sizes && vData.sizes.length > 0) ? vData.sizes : (product.size ? [product.size] : []);
  const colorsList = (vData.colors && vData.colors.length > 0) ? vData.colors : (product.color ? [product.color] : []);
  const modelsList = vData.models || [];
  const storageList = vData.storage || [];

  function renderPills(list) {
    if (!list || list.length === 0) return `<span style="font-size:12px; color:#94a3b8; font-style:italic;">Not available</span>`;
    return list.map(item => `
      <span style="display:inline-block; font-size:11px; font-weight:700; padding:3px 8px; background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; border-radius:4px; margin-right:4px; margin-bottom:4px;">
        ${escapeHtml(String(item))}
      </span>
    `).join("");
  }

  // ── 5. EXTRACTION INFORMATION ──
  const extInfo = product.extraction_info || {};
  const extPlatform = extInfo.platform_display || product.platform || "E-commerce";
  const extUrl = extInfo.source_url || product.product_url || "#";
  const extTime = extInfo.extraction_timestamp || product.extraction_timestamp || "Just now";
  const extReported = extInfo.reported_reviews != null ? Number(extInfo.reported_reviews).toLocaleString() : reportedReviews;
  const extExtracted = extInfo.extracted_reviews != null ? extInfo.extracted_reviews : ((currentAnalysisData && currentAnalysisData.comments) ? currentAnalysisData.comments.length : 0);
  const extUnique = extInfo.unique_reviews != null ? extInfo.unique_reviews : extExtracted;
  const extStatus = (extInfo.status || "extracted").toUpperCase();

  // ── Completeness Badges ──
  const comp = product.completeness || {};
  const compColors = { "FOUND": "#16a34a", "PARTIAL": "#d97706", "NOT AVAILABLE": "#64748b", "FAILED": "#dc2626" };
  const compBadges = Object.entries(comp).map(([f, s]) => {
    const col = compColors[s] || "#64748b";
    return `<span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:3px; background:${col}15; color:${col}; margin-right:4px; margin-bottom:4px; display:inline-block;">${f.replace('_', ' ').toUpperCase()}: ${s}</span>`;
  }).join("");

  card.innerHTML = `
    <div style="border-bottom:2px solid #e2e8f0; padding-bottom:12px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:18px;">&#128722;</span>
        <h3 style="font-size:18px; font-weight:800; color:#0f172a; margin:0;">Product Details Intelligence</h3>
        <span style="font-size:11px; font-weight:700; background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:12px;">Universal Scraper Engine</span>
      </div>
      <div style="font-size:12px; color:#64748b;">
        Platform: <b style="color:#0f172a;">${escapeHtml(extPlatform)}</b> &nbsp;|&nbsp; Status: <span style="font-weight:700; color:#16a34a;">${extStatus}</span>
      </div>
    </div>

    <!-- SECTION 1: PRODUCT OVERVIEW -->
    <div style="display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap; margin-bottom:20px;">
      <!-- Left: Image Gallery -->
      <div style="width:160px; flex-shrink:0;">
        <div style="width:160px; height:160px; border-radius:10px; border:1px solid #e2e8f0; display:flex; align-items:center; justify-content:center; overflow:hidden; background:#fafafa;">
          ${primaryImg ? `<img id="pdetail-main-img" src="${escapeHtml(primaryImg)}" alt="Product" style="max-width:100%; max-height:100%; object-fit:contain;" onerror="this.parentElement.style.display='none'">` : `<div style="font-size:12px; color:#94a3b8;">No Image Available</div>`}
        </div>
        ${thumbsHtml}
      </div>

      <!-- Right: Main Metadata -->
      <div style="flex:1; min-width:280px;">
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:6px;">
          <span style="font-size:12px; font-weight:800; color:#2563eb; text-transform:uppercase; letter-spacing:0.5px; background:#eff6ff; padding:2px 8px; border-radius:4px;">${escapeHtml(brand)}</span>
          <span style="font-size:11px; font-weight:700; background:#f3e8ff; color:#7c3aed; padding:2px 6px; border-radius:4px;">${escapeHtml(category)}</span>
          <span style="font-size:11px; font-weight:700; background:${availability === 'In Stock' ? '#dcfce7' : '#fee2e2'}; color:${availability === 'In Stock' ? '#15803d' : '#b91c1c'}; padding:2px 6px; border-radius:4px;">${escapeHtml(availability)}</span>
        </div>

        <h2 style="font-size:18px; font-weight:800; margin:0 0 10px 0; color:#0f172a; line-height:1.4;">
          ${escapeHtml(product.product_name)}
        </h2>

        <!-- Pricing Row -->
        <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:12px; flex-wrap:wrap;">
          <span style="font-size:24px; font-weight:900; color:#0f172a;">${price}</span>
          ${origPrice ? `<span style="font-size:14px; text-decoration:line-through; color:#94a3b8;">${origPrice}</span>` : ""}
          ${discount ? `<span style="font-size:12px; font-weight:800; color:#15803d; background:#dcfce7; padding:2px 8px; border-radius:4px;">${discount}</span>` : ""}
          <span style="font-size:11px; color:#64748b; font-weight:600;">(${currency})</span>
        </div>

        <!-- Rating & Total Reported Reviews -->
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px; flex-wrap:wrap;">
          <span style="font-size:13px; font-weight:800; color:#ea580c; background:#ffedd5; padding:3px 8px; border-radius:4px;">${rating}</span>
          <span style="font-size:13px; color:#475569;"><b>Reported Reviews / Ratings:</b> ${reportedReviews}</span>
        </div>

        <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
          <span style="font-size:11px; color:#64748b; font-weight:700;">Extraction Quality:</span>
          ${compBadges}
        </div>
      </div>
    </div>

    <!-- SECTION 2: DESCRIPTION & HIGHLIGHTS -->
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:16px;">
      <h4 style="font-size:13px; font-weight:800; color:#0f172a; margin:0 0 8px 0; text-transform:uppercase; letter-spacing:0.5px;">Product Description &amp; Highlights</h4>
      <div style="font-size:13px; color:#334155; line-height:1.5; margin-bottom:10px;">${escapeHtml(fullDesc)}</div>
      
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:10px;">
        <div>
          <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase;">Key Features &amp; Highlights</div>
          ${highlightsHtml}
        </div>
        <div>
          <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase;">Manufacturer Information</div>
          <div style="font-size:12px; color:#334155; margin-top:6px;">${escapeHtml(manufacturer)}</div>
        </div>
      </div>
    </div>

    <!-- SECTION 3: TECHNICAL SPECIFICATIONS -->
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:16px;">
      <h4 style="font-size:13px; font-weight:800; color:#0f172a; margin:0 0 10px 0; text-transform:uppercase; letter-spacing:0.5px;">Technical Specifications (${escapeHtml(category)})</h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
        ${techSpecsHtml}
      </div>
    </div>

    <!-- SECTION 4: PRODUCT VARIANTS -->
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:16px;">
      <h4 style="font-size:13px; font-weight:800; color:#0f172a; margin:0 0 10px 0; text-transform:uppercase; letter-spacing:0.5px;">Product Variants &amp; Accessible Options</h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px;">
        <div>
          <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">Available Sizes</div>
          ${renderPills(sizesList)}
        </div>
        <div>
          <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">Available Colours</div>
          ${renderPills(colorsList)}
        </div>
        <div>
          <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">Storage / Models</div>
          ${renderPills(storageList.length > 0 ? storageList : modelsList)}
        </div>
      </div>
    </div>

    <!-- SECTION 5: EXTRACTION INFORMATION -->
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; font-size:12px;">
        <div><b>Platform:</b> ${escapeHtml(extPlatform)}</div>
        <div><b>Extraction Timestamp:</b> ${escapeHtml(extTime)}</div>
        <div><b>Reported Reviews:</b> ${extReported}</div>
        <div><b>Extracted Reviews:</b> ${extExtracted}</div>
        <div><b>Unique Reviews:</b> ${extUnique}</div>
        <div><b>Status:</b> <span style="font-weight:700; color:#16a34a;">${escapeHtml(extStatus)}</span></div>
        ${extUrl && extUrl !== '#' ? `<div><a href="${escapeHtml(extUrl)}" target="_blank" style="color:#2563eb; text-decoration:underline;">View Source Listing &rarr;</a></div>` : ''}
      </div>
    </div>
  `;
}

