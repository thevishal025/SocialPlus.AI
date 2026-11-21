"""Shared, browser-visible review collector for public review sections.

This collector only reads content rendered to an ordinary public browser session.
It does not authenticate, evade CAPTCHA, call private endpoints, or bypass access controls.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from backend.ecommerce.browser_manager import BrowserManager
from backend.ecommerce.review_extractor import CustomerReview

logger = logging.getLogger("ecommerce.review_collection")

EXTRACT_JS = r"""(platform) => {
  const cardSelectors = {
    amazon: [
      'div[data-hook="review"]',
      'div[id^="customer_review-"]',
      'div[data-review-id]'
    ],
    flipkart: [
      'div._16PBlm',
      'div._27M-vq',
      'div.col._2wzgFH',
      'div.cPHDOP',
      'div.RcXBOT',
      'div.EPCmJX',
      'div[class*="EPCmJX"]',
      'div[class*="_2wzgFH"]',
      'div[class*="cPHDOP"]',
      'div[data-testid*="review"]',
      'div[class*="ReviewCard"]'
    ],
    meesho: [
      'div[class*="ReviewCard"]',
      'div[class*="Card__CardWrapper"]',
      'div[class*="ReviewStyled"]',
      'div[class*="CommentCard"]',
      'div[class*="Card-sc-"]',
      'div[data-testid*="review"]',
      'div[class*="review-card"]'
    ],
    ajio: [
      'div.review-card',
      'div[class*="reviewItem"]',
      'div[class*="ReviewCard"]',
      'div.review-list-item',
      'div.prod-rating-reviews .review',
      'div[class*="review-row"]',
      'div[data-testid*="review"]'
    ],
    myntra: [
      'div.user-review-main',
      'div.detailed-reviews-userReviewsContainer > div',
      'div[class*="userReviewsContainer"] > div',
      'div.user-review-userReviewWrapper',
      'div[data-testid*="review"]'
    ]
  };

  const text = (el) => (el?.innerText || el?.textContent || '').replace(/\s+/g, ' ').trim();
  const pick = (root, sels) => {
    for (const s of sels) {
      try {
        const el = root.querySelector(s);
        if (el && text(el)) return el;
      } catch(e) {}
    }
    return null;
  };

  const out = [];
  const seen = new Set();
  const targetSelectors = cardSelectors[platform] || ['[data-review-id]', 'div[class*="review"]'];

  for (const sel of targetSelectors) {
    let elements = [];
    try {
      elements = [...document.querySelectorAll(sel)];
    } catch(e) {
      continue;
    }

    for (const card of elements) {
      // 1. Review Body Text
      const bodyEl = pick(card, [
        // Amazon
        '[data-hook="reviewRichContentContainer"] span',
        '[data-hook="reviewRichContentContainer"] p',
        '[data-hook="reviewText"] p',
        '[data-hook="reviewText"]',
        'span[data-hook="review-body"] span',
        'div[data-hook="review-collapsed"]',
        'span[data-hook="review-body"]',
        '[data-hook="review-body"]',
        // Flipkart
        'div.t-ZTKy div div',
        'div.t-ZTKy',
        'div._6K-7Co',
        'div.ZmyHeo div div',
        'div.ZmyHeo',
        // Meesho
        'p[class*="ReviewDescription"]',
        'span[class*="ReviewDescription"]',
        'div[class*="ReviewDescription"]',
        // AJIO
        'div.review-text',
        'p.review-text',
        'div.review-desc',
        '[class*="reviewText"]',
        // Myntra
        'div.user-review-reviewTextWrapper',
        'div.review-text',
        'p[class*="user-review-reviewText"]',
        // Fallbacks
        '[data-testid*="review-text"]',
        'p[class*="review"]'
      ]);

      let reviewText = text(bodyEl);
      if (!reviewText) {
        // Fallback candidate search inside card
        const candidates = [...card.querySelectorAll('p, span, div')]
          .filter(el => el.children.length === 0)
          .map(text)
          .filter(t => t.length >= 20 && t.length <= 4000);
        if (candidates.length > 0) {
          reviewText = candidates.sort((a, b) => b.length - a.length)[0] || '';
        }
      }

      // Strip Amazon expander teaser prefixes
      reviewText = reviewText.replace(/^(?:Brief content visible, double tap to read full content\.\s*|Full content visible, double tap to read brief content\.\s*)+/gi, '').trim();

      // Strip trailing "read more" / "see more" artifact text from the body
      reviewText = reviewText.replace(/\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$/i, '').trim();
      if (!reviewText || reviewText.length < 3) continue;

      // 2. Author Name
      const authorEl = pick(card, [
        // Amazon
        '[data-hook="genome-widget"] span.a-profile-name',
        'span.a-profile-name',
        // Flipkart
        'p._2sc7ZR._2V5EHH',
        'p._2sc7ZR',
        'p._2NsDsF',
        'p._2V5EHH',
        // Meesho
        'span[class*="Author"]',
        'p[class*="Author"]',
        'div[class*="Author"]',
        // AJIO
        'span.user-name',
        'div[class*="reviewer"]',
        'div.author',
        'span[class*="author"]',
        // Myntra
        'div.user-review-left span',
        'span.user-review-userName',
        'div.user-review-userName',
        // Generic
        '[data-testid*="author"]',
        '[class*="reviewer"]',
        '[class*="userName"]'
      ]);
      let authorName = text(authorEl);
      if (!authorName || authorName.length < 2) {
        authorName = 'Customer';
      }

      // 3. Review Title / Headline
      const titleEl = pick(card, [
        '[data-hook="reviewTitle"] span:not([class])',
        '[data-hook="reviewTitle"]',
        'a[data-hook="review-title"] span:not([class])',
        'a[data-hook="review-title"]',
        'span[data-hook="review-title"]',
        '[data-hook="review-title"]',
        'p._2-N8zT',
        'p.z9E0IG',
        'p._2Us4fl',
        'p[class*="Headline"]',
        'p.review-title',
        '[data-testid*="review-title"]',
        '[class*="reviewTitle"]'
      ]);
      const titleText = text(titleEl);

      // 4. Rating (1.0 to 5.0)
      const ratingEl = pick(card, [
        'i[data-hook="review-star-rating"] span',
        'i[data-hook="cmps-review-star-rating"] span',
        'span.a-icon-alt',
        'div.XQDdHH',
        'div._3LWZlK',
        'div[class*="XQDdHH"]',
        'div[class*="_3LWZlK"]',
        'span[class*="Badge__BadgeStyled"]',
        'div[class*="Badge__BadgeStyled"]',
        'div.star-rating',
        'span[class*="rating"]',
        'div.user-review-starRating span',
        'span.user-review-rating',
        'div.user-review-starRating',
        '[aria-label*="out of 5"]',
        '[title*="out of 5"]',
        '[aria-label*="star"]'
      ]);
      let ratingVal = null;
      if (ratingEl) {
        const rawRate = text(ratingEl) || ratingEl.getAttribute('aria-label') || ratingEl.getAttribute('title') || '';
        const m = rawRate.match(/([1-5](?:\.\d+)?)/);
        if (m) ratingVal = parseFloat(m[1]);
      }

      // 5. Date
      let dateText = '';
      if (platform === 'flipkart') {
        // On Flipkart, date is usually the second p._2sc7ZR / p._2NsDsF in the card
        const pCandidates = [...card.querySelectorAll('p._2sc7ZR, p._2NsDsF')];
        if (pCandidates.length > 1) {
          dateText = text(pCandidates[1]);
        }
      }
      if (!dateText) {
        const dateEl = pick(card, [
          'span[data-hook="review-date"]',
          'div.user-review-reviewDate',
          'span.user-review-reviewDate',
          'span.review-date',
          'span.date',
          '[class*="reviewDate"]',
          '[class*="Date"]'
        ]);
        dateText = text(dateEl);
      }
      if (!dateText) {
        // Regex search for date pattern in small texts
        for (const el of card.querySelectorAll('p, span')) {
          const t = text(el);
          if (/(?:reviewed in|posted on|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*,?\s+\d{4}|\d+\s+(?:months?|days?|years?|weeks?|hours?)\s+ago)/i.test(t) && t.length < 60) {
            dateText = t;
            break;
          }
        }
      }

      // 6. Verified Purchase Status
      let isVerified = false;
      const verifiedEl = card.querySelector(
        '[data-hook="avp-badge"], p._2mcFHG, div._1eDkuJ, p._2-5W3i, ' +
        'div.user-review-verifiedBuyer, [class*="verified"], [class*="Verified"]'
      );
      if (verifiedEl) {
        isVerified = true;
      } else {
        const cardAllText = card.innerText || '';
        if (/verified purchase|certified buyer|verified buyer/i.test(cardAllText)) {
          isVerified = true;
        }
      }

      // 7. Helpful Votes
      let helpfulVotes = 0;
      const helpfulEl = pick(card, [
        'span[data-hook="helpful-vote-statement"]',
        'span.cr-vote-text',
        'span._3c3Px5',
        'div._1LmwT9 span',
        'div._2Z07dn span',
        'span.user-review-upvoteCount',
        'div.user-review-upvoteContainer',
        'span.helpful-count',
        '[class*="helpful"]'
      ]);
      if (helpfulEl) {
        const helpText = text(helpfulEl);
        if (/one person/i.test(helpText)) {
          helpfulVotes = 1;
        } else {
          const mHelp = helpText.match(/\d+/);
          if (mHelp) helpfulVotes = parseInt(mHelp[0], 10);
        }
      }

      // 8. Product Variant / Attributes
      const variantEl = pick(card, [
        'a[data-hook="format-strip"]',
        '[data-hook="format-strip"]',
        'div._2V5EHH span',
        'span.user-review-userSize',
        'div.user-review-userSize',
        '[class*="variant"]'
      ]);
      const variantText = text(variantEl);

      // Stable key for in-browser deduplication
      const cardId = card.getAttribute('data-review-id') || card.id || '';
      const dedupKey = (cardId || `${authorName}|${titleText}|${reviewText}`).toLowerCase();
      if (seen.has(dedupKey)) continue;
      seen.add(dedupKey);

      out.push({
        id: cardId,
        author: authorName,
        title: titleText,
        text: reviewText,
        rating: ratingVal,
        date: dateText,
        verified: isVerified,
        helpful: helpfulVotes,
        variant: variantText
      });
    }
  }

  return out;
}"""

EXPAND_REVIEWS_JS = r"""() => {
  let count = 0;
  // Clicks Amazon collapsed buttons, Flipkart READ MORE, and generic read-more spans
  const triggers = document.querySelectorAll(
    'a[data-hook="review-collapsed-text-toggle"], ' +
    'a[data-hook="review-collapse"], ' +
    'span._1BWfIk, span[class*="_1BWfIk"], ' +
    'span[class*="readMore"], button[class*="readMore"], ' +
    'button, a, [role="button"], span'
  );
  for (const el of triggers) {
    const label = (el.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().toLowerCase();
    const isExpand = /^(read more|show full review|see more|more|\.\.\.more|\+ more)$/.test(label) ||
                     el.matches('a[data-hook*="collapse"], span._1BWfIk, span[class*="_1BWfIk"]');
    if (!isExpand) continue;
    try {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0 && !el.disabled) {
        el.click();
        count++;
      }
    } catch(e) {}
  }
  return count;
}"""

NEXT_CLICK_JS = r"""() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();

  // 1. Direct pagination link with href
  // Amazon: li.a-last:not(.a-disabled) a
  // Flipkart: a._1LKTO3, a._9QVEST, nav._2OZ7Nm a:last-child
  // Standard: a[rel="next"], link[rel="next"]
  const directLink = document.querySelector(
    'li.a-last:not(.a-disabled) a, ' +
    'a[rel="next"], ' +
    'a._1LKTO3, a._9QVEST, nav._2OZ7Nm a:last-child'
  );
  if (directLink && directLink.href && !directLink.classList.contains('disabled')) {
    const txt = norm(directLink.innerText);
    if (!/prev|previous/.test(txt)) {
      return { href: directLink.href, label: txt || 'next_link' };
    }
  }

  // 2. Visible button or link with Next / Load More / View More text
  const candidates = [...document.querySelectorAll('a, button, [role="button"], div[class*="load-more"] button')];
  const patterns = [
    /^next(?: page)?$/i,
    /^next\s*›?$/i,
    /^load more(?: reviews)?$/i,
    /^show more(?: reviews)?$/i,
    /^view more(?: reviews)?$/i,
    /^more reviews$/i,
    /^see more reviews$/i,
    /^view all (?:[\d,]+ )?reviews$/i
  ];

  for (const el of candidates) {
    const label = norm(el.innerText || el.getAttribute('aria-label') || el.getAttribute('title'));
    if (!patterns.some(p => p.test(label))) continue;
    if (el.disabled || el.getAttribute('aria-disabled') === 'true' || el.classList.contains('disabled')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;

    if (el.tagName.toLowerCase() === 'a' && el.href && !el.href.startsWith('javascript:') && !el.href.includes('#')) {
      return { href: el.href, label };
    }
    el.click();
    return { clicked: true, label };
  }

  return { clicked: false };
}"""

PLATFORM_LIMITATIONS = {
  "amazon": "Amazon publicly displays a sample of top customer reviews on product listings and serves paginated recent reviews via /product-reviews/. Unauthenticated public requests may trigger anti-bot challenges ('Robot Check').",
  "flipkart": "Flipkart renders reviews across paginated /product-reviews/ routes (10 reviews per page). All publicly accessible pages are parsed until pagination ends.",
  "meesho": "Meesho uses Next.js single-page application rendering. Reviews are extracted from embedded page state and dynamically loaded review cards via the public UI.",
  "ajio": "AJIO renders reviews dynamically within the Ratings & Reviews section. Many apparel catalog entries only carry aggregate star ratings without written customer reviews.",
  "myntra": "Myntra exposes extended customer reviews via its dedicated /reviews/{style_id} interface with dynamic scroll loading."
}


def _stable_id(item: Dict[str, Any], platform: str) -> str:
    raw_id = item.get("id")
    if raw_id and len(str(raw_id).strip()) > 3:
        return f"{platform}_{str(raw_id).strip()}"
    raw = "|".join(str(item.get(k) or "").strip().lower() for k in ("author", "title", "text", "date"))
    return f"{platform}_{hashlib.sha256(raw.encode('utf-8', 'ignore')).hexdigest()[:24]}"


def _to_model(item: Dict[str, Any], platform: str) -> Optional[CustomerReview]:
    body = str(item.get("text") or "").strip()
    if len(body) < 3:
        return None
    try:
        rating = float(item["rating"]) if item.get("rating") is not None else None
    except (TypeError, ValueError):
        rating = None
    try:
        helpful = int(item["helpful"]) if item.get("helpful") is not None else 0
    except (TypeError, ValueError):
        helpful = 0

    return CustomerReview(
        review_id=_stable_id(item, platform),
        reviewer_name=str(item.get("author") or "Customer").strip() or "Customer",
        review_title=str(item.get("title") or "").strip() or None,
        review_text=body,
        rating=rating,
        review_date=str(item.get("date") or "").strip() or None,
        verified_purchase=bool(item.get("verified")),
        helpful_votes=helpful,
        product_variant=str(item.get("variant") or "").strip() or None,
        platform=platform,
        source="public_browser_dom",
    )


async def collect_public_reviews(
    url: str,
    platform: str,
    initial_reviews: Optional[Sequence[CustomerReview]] = None,
    max_reviews: Optional[int] = None,
    progress_callback=None,
    idle_round_limit: int = 3,
    review_page_url: Optional[str] = None
) -> Tuple[List[CustomerReview], Dict[str, Any]]:
    """Collect every review exposed through the page's public UI until pagination ends.

    max_reviews=None means no application-level review cap. Collection ends when the
    public page has no next/load-more control and scrolling produces no new reviews.
    """
    collected: List[CustomerReview] = list(initial_reviews or [])
    seen = {r.review_id for r in collected if r.review_id}
    for r in collected:
        if not r.review_id:
            seen.add(hashlib.sha256((r.reviewer_name + r.review_text).encode()).hexdigest())

    total_raw_retrieved = len(collected)
    duplicates_count = 0

    stats: Dict[str, Any] = {
        "pages_scanned": 0,
        "browser_used": False,
        "stop_reason": "browser_unavailable",
        "retrieved_reviews": total_raw_retrieved,
        "unique_reviews": len(collected),
        "duplicates_found": duplicates_count,
        "review_source_url": review_page_url or url,
        "failure_reason": None,
        "platform_limitations": PLATFORM_LIMITATIONS.get(platform, "Public review extraction operates on publicly rendered web content.")
    }

    try:
        manager = await BrowserManager.get_instance()
        async with manager.get_page(timeout=30000) as page:
            stats["browser_used"] = True

            # Start directly at review_page_url if provided, otherwise start at product url
            target_start_url = review_page_url or url
            stats["review_source_url"] = target_start_url

            response = await page.goto(target_start_url, wait_until="domcontentloaded", timeout=30000)
            if response and response.status in (401, 403, 429):
                stats["stop_reason"] = f"http_{response.status}"
                stats["failure_reason"] = f"HTTP {response.status} returned by {platform.upper()} public endpoint."
                return collected, stats

            try:
                await page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass

            # Detect anti-bot security challenges immediately
            body_content = await page.content()
            current_nav_url = page.url.lower()

            # If a dedicated review URL redirected to a login wall or home page, fallback to product URL
            if review_page_url and ("/ap/signin" in current_nav_url or "/login" in current_nav_url or (platform == "flipkart" and "/p/" not in current_nav_url and "/product-reviews/" not in current_nav_url)):
                logger.info(f"Review URL redirected to {page.url}. Falling back to product page: {url}")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    await page.wait_for_timeout(1200)
                    body_content = await page.content()
                    current_nav_url = page.url.lower()
                    stats["review_source_url"] = url
                except Exception as fb_err:
                    logger.warning(f"Fallback navigation to product URL failed: {fb_err}")

            if "Robot Check" in body_content or "Enter the characters you see below" in body_content or "api-services-support@amazon.com" in body_content:
                stats["stop_reason"] = "anti_bot_challenge_detected"
                stats["failure_reason"] = "Access restricted by Amazon anti-bot security challenge ('Robot Check') on unauthenticated public session."
                return collected, stats

            if "Access Denied" in body_content and len(body_content) < 2000:
                stats["stop_reason"] = "access_restricted_by_platform"
                stats["failure_reason"] = f"Access denied by {platform.upper()} security gateway."
                return collected, stats

            # If we started at product url, attempt to navigate to dedicated review page if link is visible
            if not review_page_url:
                try:
                    review_link_href = await page.evaluate(r"""() => {
                      // Check for dedicated review page link
                      const links = [...document.querySelectorAll('a[href*="/product-reviews/"], a[href*="/reviews/"]')];
                      if (links.length > 0 && links[0].href) return links[0].href;
                      return null;
                    }""")
                    if review_link_href and urlparse(review_link_href).netloc == urlparse(page.url).netloc:
                        await page.goto(review_link_href, wait_until="domcontentloaded", timeout=25000)
                        stats["review_source_url"] = review_link_href
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass

            # Also ensure in-page review section/accordion is active (e.g. on AJIO, Meesho)
            try:
                await page.evaluate(r"""() => {
                  const els = [...document.querySelectorAll('a, button, [role="button"], div[class*="tab"]')];
                  const e = els.find(x => /ratings?|reviews?/i.test((x.innerText || x.getAttribute('aria-label') || '').trim()) && x.getBoundingClientRect().height > 0);
                  if (e) e.click();
                }""")
                await page.wait_for_timeout(500)
            except Exception:
                pass

            idle_rounds = 0
            last_url = page.url

            while True:
                stats["pages_scanned"] += 1

                # 1. Expand truncated reviews
                try:
                    expanded = await page.evaluate(EXPAND_REVIEWS_JS)
                    if expanded:
                        await page.wait_for_timeout(300)
                except Exception:
                    pass

                # 2. Extract review cards from current DOM
                try:
                    raw_items = await page.evaluate(EXTRACT_JS, platform)
                except Exception:
                    raw_items = []

                total_raw_retrieved += len(raw_items or [])
                added_this_round = 0

                for item in raw_items or []:
                    model = _to_model(item, platform)
                    if not model:
                        continue
                    key = model.review_id
                    if key in seen:
                        duplicates_count += 1
                        continue
                    seen.add(key)
                    collected.append(model)
                    added_this_round += 1

                    if max_reviews is not None and len(collected) >= max_reviews:
                        stats["stop_reason"] = "requested_limit_reached"
                        stats["retrieved_reviews"] = total_raw_retrieved
                        stats["unique_reviews"] = len(collected[:max_reviews])
                        stats["duplicates_found"] = duplicates_count
                        return collected[:max_reviews], stats

                if progress_callback:
                    try:
                        await progress_callback(
                            min(95, 45 + stats["pages_scanned"] * 5),
                            f"Collected {len(collected)} unique reviews (page/round {stats['pages_scanned']})..."
                        )
                    except Exception:
                        pass

                if added_this_round > 0:
                    idle_rounds = 0
                else:
                    idle_rounds += 1

                # 3. Try Next Page or Load More action
                action = await page.evaluate(NEXT_CLICK_JS)
                if action.get("href"):
                    target_href = action["href"]
                    if urlparse(target_href).netloc == urlparse(page.url).netloc and target_href != page.url:
                        try:
                            await page.goto(target_href, wait_until="domcontentloaded", timeout=25000)
                            idle_rounds = 0
                            last_url = page.url
                            await page.wait_for_timeout(800)
                            continue
                        except Exception:
                            pass
                elif action.get("clicked"):
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(900)
                    if page.url != last_url:
                        last_url = page.url
                        idle_rounds = 0
                    if idle_rounds >= idle_round_limit:
                        stats["stop_reason"] = "pagination_control_no_longer_advances"
                        break
                    continue

                # 4. Infinite scroll fallback if no next button
                before_height = await page.evaluate("document.body.scrollHeight")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                after_height = await page.evaluate("document.body.scrollHeight")

                if after_height > before_height and idle_rounds < idle_round_limit:
                    continue

                if idle_rounds >= idle_round_limit:
                    if len(collected) == 0:
                        stats["stop_reason"] = "no_reviews_available_on_platform"
                        stats["failure_reason"] = f"No publicly accessible reviews were found on this {platform.upper()} product page."
                    else:
                        stats["stop_reason"] = "all_accessible_reviews_extracted"
                    break

            stats["retrieved_reviews"] = total_raw_retrieved
            stats["unique_reviews"] = len(collected)
            stats["duplicates_found"] = duplicates_count
            return collected, stats

    except Exception as exc:
        logger.info("Public review collection unavailable for %s: %s", platform, exc)
        stats["stop_reason"] = f"browser_error: {type(exc).__name__}"
        stats["failure_reason"] = f"Browser automation error: {str(exc)}"
        stats["retrieved_reviews"] = total_raw_retrieved
        stats["unique_reviews"] = len(collected)
        stats["duplicates_found"] = duplicates_count
        return collected, stats
