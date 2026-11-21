
function renderEcommerceProductDetails(product, response = {}) {
  const host = document.getElementById("ecom-product-details");
  if (!host) return;
  const esc = (v) => String(v ?? "Not available").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const reviews = Array.isArray(response.reviews) ? response.reviews : [];
  const safeProductUrl = (() => { try { const u=new URL(product?.product_url || response.source_url || ""); return ["http:","https:"].includes(u.protocol) ? u.href : "#"; } catch (_) { return "#"; } })();
  const reported = response.reported_review_count ?? product?.total_reviews_count ?? product?.review_count ?? null;
  const retrieved = reviews.length;
  const unique = Number(response.unique_reviews_count ?? product?.extraction_info?.unique_reviews ?? retrieved);
  const specs = product?.technical_specifications?.length ? product.technical_specifications : (product?.category_specific_specs || product?.specifications?.category_specific || product?.specifications || {});
  const specEntries = Object.entries(specs || {}).filter(([,v]) => v !== null && v !== "" && typeof v !== "object");
  const variants = product?.variants_data || {};
  const descriptionData = product?.description_data || {};
  const images = (product?.product_images || []).filter(Boolean);
  const ratingCounts = [5,4,3,2,1].reduce((a,n) => (a[n]=reviews.filter(r=>Math.round(Number(r.rating||0))===n).length,a),{});
  const money = v => v === null || v === undefined || v === "" ? "Not available" : `${esc(product?.currency || "INR")} ${esc(Number(v).toLocaleString())}`;
  const reviewCards = reviews.map(review => {
    const rating = Number(review.rating || 0);
    const stars = rating ? "★".repeat(Math.max(1,Math.min(5,Math.round(rating)))) + "☆".repeat(5-Math.max(1,Math.min(5,Math.round(rating)))) : "No rating";
    const search = [review.reviewer_name,review.review_title,review.review_text,review.review_date].join(" ").toLowerCase();
    return `<article class="ecom-review-card" data-rating="${rating}" data-date="${esc(review.review_date || "")}" data-search="${esc(search)}">
      <div class="ecom-review-card-head"><div><strong>${esc(review.reviewer_name || "Customer")}</strong><span class="ecom-review-date">${esc(review.review_date || "Date not provided")}</span></div><span class="ecom-stars">${stars}</span></div>
      ${review.review_title ? `<h4>${esc(review.review_title)}</h4>` : ""}
      <p class="ecom-review-text">${esc(review.review_text || review.text || "Review text unavailable")}</p>
      <div class="ecom-review-meta"><span>${review.verified_purchase ? "✓ Verified purchase" : "Purchase verification not provided"}</span><span>Helpful: ${esc(review.helpful_votes ?? 0)}</span>${review.product_variant ? `<span>Variant: ${esc(review.product_variant)}</span>` : ""}</div>
    </article>`;
  }).join("");
  host.style.display = "block";
  host.innerHTML = `
    <section class="ecom-result-summary">
      <div class="ecom-result-summary-copy"><span class="ecom-eyebrow">EXTRACTION RESULT</span><h2>${esc(product?.product_name || "Product extraction")}</h2><p>${esc(product?.brand || "Brand not available")} <span>·</span> ${esc(product?.category || "Category not available")} <span>·</span> ${esc(response.platform_display || response.platform || product?.platform || "E-commerce")}</p></div>
      <a class="ecom-source-link" href="${esc(safeProductUrl)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>
    </section>
    <div class="ecom-metric-grid">
      <div class="ecom-metric"><span>Current price</span><strong>${money(product?.current_price)}</strong></div>
      <div class="ecom-metric"><span>Product rating</span><strong>${esc(product?.rating ?? "Not available")}${product?.rating ? " / 5" : ""}</strong></div>
      <div class="ecom-metric"><span>Reported reviews</span><strong>${esc(reported ?? "Not available")}</strong></div>
      <div class="ecom-metric"><span>Reviews collected</span><strong>${retrieved.toLocaleString()}</strong></div>
    </div>
    <section class="ecom-product-panel">
      <div class="ecom-section-title"><div><span class="ecom-eyebrow">PRODUCT INTELLIGENCE</span><h3>Product details</h3></div><span class="ecom-section-tag">${esc(product?.platform || response.platform || "Product")}</span></div>
      <div class="ecom-product-overview">
        <div class="ecom-gallery">${images.length ? images.map(src=>`<img src="${esc(src)}" alt="Product image" loading="lazy">`).join("") : `<div class="ecom-image-placeholder">No product image</div>`}</div>
        <div class="ecom-product-summary">
          <h4>${esc(product?.product_name)}</h4>
          <p>${esc(descriptionData.description || product?.description || "Description not available")}</p>
          <div class="ecom-price-line"><strong>${money(product?.current_price)}</strong><del>${money(product?.original_price)}</del><span>${esc(product?.discount || (product?.discount_percent ? `${product.discount_percent}% off` : ""))}</span></div>
          <div class="ecom-product-meta"><span>Brand: <b>${esc(product?.brand)}</b></span><span>Availability: <b>${esc(product?.availability)}</b></span></div>
        </div>
      </div>
      <div class="ecom-detail-grid">
        <div class="ecom-detail-block"><h4>Specifications</h4>${specEntries.length ? `<dl>${specEntries.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>` : `<p class="ecom-muted">Specifications were not exposed by the source page.</p>`}</div>
        <div class="ecom-detail-block"><h4>Variants & highlights</h4><p><b>Sizes:</b> ${esc((variants.sizes || []).join(", ") || "Not available")}</p><p><b>Colours:</b> ${esc((variants.colors || []).join(", ") || "Not available")}</p><p><b>Models / Storage:</b> ${esc([...(variants.models || []),...(variants.storage || [])].join(", ") || "Not available")}</p><p><b>Highlights:</b> ${esc((descriptionData.highlights || descriptionData.features || []).join(" · ") || "Not available")}</p></div>
      </div>
    </section>
    <section class="ecom-reviews-panel">
      <div class="ecom-section-title"><div><span class="ecom-eyebrow">CUSTOMER VOICE</span><h3>Customer reviews</h3><p class="ecom-section-subtitle">${retrieved.toLocaleString()} unique reviews collected${reported !== null ? ` · Website reports ${Number(reported).toLocaleString()}` : " · Website total not available"}</p></div><div class="ecom-export-actions"><button type="button" id="ecom-export-csv" class="ecom-secondary-btn">Export CSV</button><button type="button" id="ecom-export-json" class="ecom-secondary-btn">Export JSON</button></div></div>
      <div class="ecom-review-filterbar"><button type="button" class="ecom-filter-chip active" data-rating-filter="all">All <b>${retrieved}</b></button>${[5,4,3,2,1].map(n=>`<button type="button" class="ecom-filter-chip" data-rating-filter="${n}">${n} ★ <b>${ratingCounts[n]}</b></button>`).join("")}<select id="ecom-review-sort" aria-label="Sort reviews"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="highest">Highest rating</option><option value="lowest">Lowest rating</option></select><input id="ecom-review-search" type="search" placeholder="Search reviewer or review text…" aria-label="Search reviews"></div>
      <div class="ecom-review-list" id="ecom-review-list">${reviewCards || `<div class="ecom-no-reviews"><strong>No reviews were returned by this extraction.</strong><p>Product details were available, but the source did not expose review records to the current public extraction session. The website's reported total is not counted as retrieved reviews.</p></div>`}</div>
      <div class="ecom-extraction-footnote"><span>Collection mode: all accessible reviews</span><span>Status: ${esc(response.status || "unknown")}</span><span>Unique: ${unique.toLocaleString()}</span>${response.review_collection?.stop_reason ? `<span>Stopped: ${esc(response.review_collection.stop_reason.replaceAll("_"," "))}</span>` : ""}</div>
    </section>`;

  let activeRating = "all";
  const apply = () => {
    const query=(host.querySelector("#ecom-review-search")?.value||"").toLowerCase().trim();
    const sort=host.querySelector("#ecom-review-sort")?.value||"newest";
    const list=host.querySelector("#ecom-review-list");
    const cards=Array.from(host.querySelectorAll(".ecom-review-card"));
    cards.forEach(card=>card.style.display=(activeRating==="all" || String(Math.round(Number(card.dataset.rating)))===activeRating) && (!query || card.dataset.search.includes(query)) ? "" : "none");
    const time=v=>{const n=Date.parse(v||"");return Number.isFinite(n)?n:0;};
    cards.sort((a,b)=>sort==="highest"?Number(b.dataset.rating)-Number(a.dataset.rating):sort==="lowest"?Number(a.dataset.rating)-Number(b.dataset.rating):sort==="oldest"?time(a.dataset.date)-time(b.dataset.date):time(b.dataset.date)-time(a.dataset.date)).forEach(card=>list.appendChild(card));
  };
  host.querySelectorAll("[data-rating-filter]").forEach(btn=>btn.addEventListener("click",()=>{activeRating=btn.dataset.ratingFilter;host.querySelectorAll("[data-rating-filter]").forEach(x=>x.classList.toggle("active",x===btn));apply();}));
  host.querySelector("#ecom-review-sort")?.addEventListener("change",apply);
  host.querySelector("#ecom-review-search")?.addEventListener("input",apply);
  const download=(filename,content,type)=>{const blob=new Blob([content],{type});const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=filename;link.click();URL.revokeObjectURL(link.href);};
  host.querySelector("#ecom-export-json")?.addEventListener("click",()=>download("socialplus-product-reviews.json",JSON.stringify(reviews,null,2),"application/json"));
  host.querySelector("#ecom-export-csv")?.addEventListener("click",()=>{const cols=["review_id","reviewer_name","review_title","review_text","rating","review_date","verified_purchase","helpful_votes","product_variant"];const cell=v=>'"'+String(v??"").replace(/"/g,'""')+'"';const csv=[cols.join(","),...reviews.map(r=>cols.map(c=>cell(r[c])).join(","))].join("\r\n");download("socialplus-product-reviews.csv",csv,"text/csv;charset=utf-8;");});
}

/**
 * SocialPlus.ai — E-commerce Deep Intelligence Controller
 * Supports Amazon marketplaces, Flipkart, Meesho, AJIO, and Myntra.
 */

const ECOM_PLATFORMS = {
  "amazon.in":        { key: "amazon",   name: "Amazon",  color: "#d97706", bg: "#fef3c7" },
  "amzn.in":          { key: "amazon",   name: "Amazon",  color: "#d97706", bg: "#fef3c7" },
  "amzn.to":          { key: "amazon",   name: "Amazon",  color: "#d97706", bg: "#fef3c7" },
  "amazon.com":       { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.co.uk":     { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.ca":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.de":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.co.jp":     { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.com.au":    { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.com.br":    { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.com.mx":    { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.com.tr":    { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.pl":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.se":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.sg":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.ae":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "amazon.sa":        { key: "amazon",   name: "Amazon",        color: "#d97706", bg: "#fef3c7" },
  "flipkart.com":     { key: "flipkart", name: "Flipkart",      color: "#2563eb", bg: "#dbeafe" },
  "dl.flipkart.com":  { key: "flipkart", name: "Flipkart",      color: "#2563eb", bg: "#dbeafe" },
  "fkrt.it":          { key: "flipkart", name: "Flipkart",      color: "#2563eb", bg: "#dbeafe" },
  "meesho.com":       { key: "meesho",   name: "Meesho",        color: "#7c3aed", bg: "#ede9fe" },
  "ajio.com":         { key: "ajio",     name: "AJIO",          color: "#059669", bg: "#d1fae5" },
  "myntra.com":       { key: "myntra",   name: "Myntra",        color: "#ec4899", bg: "#fce7f3" },
};

function detectEcomPlatform(url) {
  if (!url) return null;
  let hostname = "";
  try { hostname = new URL(url).hostname.toLowerCase(); } catch (_) { return null; }
  for (const [domain, info] of Object.entries(ECOM_PLATFORMS)) {
    if (hostname === domain || hostname.endsWith("." + domain)) return { domain, ...info };
  }
  return null;
}

document.addEventListener("DOMContentLoaded", () => {
  // Tabs: Fetch from URL vs Upload File
  setupSegmentedTabs("ecom-tabs", (mode) => {
    const searchView = document.getElementById("ecom-view-search");
    const uploadView = document.getElementById("ecom-view-upload");
    if (searchView) searchView.style.display = mode === "search" ? "block" : "none";
    if (uploadView) uploadView.style.display = mode === "upload" ? "block" : "none";
  });

  const urlInput        = document.getElementById("ecom-url-input");
  const detectedWrap    = document.getElementById("ecom-platform-detected");
  const detectedBadge   = document.getElementById("ecom-detected-badge");
  const maxReviewsSelect = document.getElementById("ecom-max-reviews"); // optional advanced limit; absent means collect all accessible

  // Live URL input listener
  if (urlInput && detectedWrap && detectedBadge) {
    urlInput.addEventListener("input", () => {
      const val = urlInput.value.trim();
      const detected = detectEcomPlatform(val);
      if (detected && val) {
        detectedWrap.style.display = "inline-flex";
        detectedBadge.textContent  = detected.name;
        detectedBadge.style.color  = detected.color;
        detectedBadge.style.background = detected.bg;
      } else {
        detectedWrap.style.display = "none";
      }
    });
  }

  // Fetch Reviews & Analyze button
  const btnFetchUrl = document.getElementById("btn-ecom-fetch-url");
  let isEcomFetching = false;

  if (btnFetchUrl) {
    btnFetchUrl.addEventListener("click", async () => {
      if (isEcomFetching) return;

      const url = urlInput ? urlInput.value.trim() : "";
      if (!url) {
        showToast("Please paste a product URL from Amazon, Flipkart, Meesho, AJIO, or Myntra.", "warning");
        return;
      }
      if (!url.startsWith("http://") && !url.startsWith("https://")) {
        showToast("Please enter a valid URL starting with https://", "warning");
        return;
      }

      isEcomFetching = true;
      btnFetchUrl.disabled = true;
      const origText = btnFetchUrl.textContent;
      btnFetchUrl.textContent = "Extracting Reviews…";

      const detected = detectEcomPlatform(url);
      const platformName = detected ? detected.name : "E-commerce Platform";
      const maxReviews = maxReviewsSelect && maxReviewsSelect.value ? parseInt(maxReviewsSelect.value, 10) : null;

      // Show progressive loading modal
      showProgress(
        `Extracting from ${platformName}`,
        "Connecting to platform and extracting product details, specs, and reviews..."
      );

      try {
        const res = await apiPost("/api/ecommerce/fetch-from-url", {
          url: url,
          max_reviews: maxReviews
        });

        if (res.product) renderEcommerceProductDetails(res.product, res);

        if (res.success && res.analysis) {
          if (res.product) {
            res.analysis.source_metadata = res.analysis.source_metadata || {};
            res.analysis.source_metadata.product = res.product;
          }
          showToast(res.message || `Extracted ${res.reviews_count || 0} reviews successfully!`, "success");
          renderDashboard(res.analysis);
        } else if (res.success && res.product) {
          // Product extracted, but reviews were empty or unavailable (e.g. status: "partial")
          showToast(res.message || `Extracted "${res.product.product_name}". No customer reviews were returned by the source.`, "warning");
        } else {
          const msg = res.message || "Could not retrieve product details or reviews from this URL.";
          if (typeof showErrorPopup === "function") {
            showErrorPopup("E-Commerce Notice", msg, () => btnFetchUrl.click());
          } else {
            showToast(msg, "error");
          }
        }
      } catch (err) {
        if (typeof showErrorPopup === "function") {
          showErrorPopup("Extraction Failed", err.message || "Connection error while extracting product reviews.", () => btnFetchUrl.click());
        } else {
          showToast(`Extraction failed: ${err.message}`, "error");
        }
      } finally {
        hideProgress();
        isEcomFetching = false;
        btnFetchUrl.disabled = false;
        btnFetchUrl.textContent = origText;
      }
    });
  }
});
