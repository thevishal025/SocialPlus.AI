"""SocialPlus.ai — Flipkart Platform Extraction Adapter.

Extracts complete product metadata, technical specifications, variants, and customer reviews
for flipkart.com, dl.flipkart.com, and fkrt.it short links.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from backend.ecommerce.base_adapter import BaseEcommerceAdapter
from backend.ecommerce.browser_manager import BrowserManager
from backend.ecommerce.data_normalizer import DataNormalizer
from backend.ecommerce.data_validator import DataValidator
from backend.ecommerce.logging_helper import log_ecom, log_zero_reviews_reason
from backend.ecommerce.pagination_manager import PaginationManager
from backend.ecommerce.product_extractor import ProductInfo, SpecificationParser
from backend.ecommerce.review_collection import collect_public_reviews
from backend.ecommerce.review_extractor import CustomerReview
from backend.utils.security import resolve_safe_redirects


class FlipkartAdapter(BaseEcommerceAdapter):
    """Deep extraction adapter for Flipkart."""

    platform_key = "flipkart"
    display_name = "Flipkart"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    }

    @classmethod
    def extract_product_identifiers(cls, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extracts (item_id, pid, slug) from Flipkart URL."""
        item_id = None
        pid = None
        slug = None

        m_item = re.search(r"/p/(itm[a-zA-Z0-9]+)", url)
        if m_item:
            item_id = m_item.group(1)

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "pid" in qs and qs["pid"]:
            pid = qs["pid"][0]

        parts = parsed.path.strip("/").split("/")
        if parts:
            slug = parts[0]

        return item_id, pid, slug

    @classmethod
    def extract_ids(cls, url: str) -> Dict[str, Optional[str]]:
        item_id, pid, slug = cls.extract_product_identifiers(url)
        return {"item_id": item_id, "pid": pid, "slug": slug}

    @classmethod
    def resolve_product_url(cls, url: str) -> Tuple[bool, str, str]:
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            return False, "", err_msg or "URL rejected by safety filter."
        return True, resolved_url, ""

    @classmethod
    def navigate_to_reviews(cls, product_url: str, **identifiers) -> Optional[str]:
        item_id = identifiers.get("item_id")
        pid = identifiers.get("pid")
        slug = identifiers.get("slug")
        if not (item_id or pid):
            extracted_item, extracted_pid, extracted_slug = cls.extract_product_identifiers(product_url)
            item_id = item_id or extracted_item
            pid = pid or extracted_pid
            slug = slug or extracted_slug

        base_slug = slug or "product"
        if item_id or pid:
            return f"https://www.flipkart.com/{base_slug}/product-reviews/{item_id or ''}?pid={pid or ''}&page=1"
        return None

    @classmethod
    def discover_review_container(cls, soup: BeautifulSoup) -> List[Any]:
        return soup.select(
            "div._16PBlm, div._27M-vq, div.col._2wzgFH, div.cPHDOP, div.RcXBOT, "
            "div.EPCmJX, div[class*='EPCmJX'], div[class*='_2wzgFH'], div[class*='cPHDOP'], "
            "div[data-testid*='review'], div[class*='review-card'], div[class*='ReviewCard']"
        )

    @classmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        # Handle structured Flipkart state review dict
        if "text" in raw_item or "reviewBody" in raw_item:
            body = raw_item.get("text") or raw_item.get("reviewBody") or ""
            author = raw_item.get("author") or "Flipkart Customer"
            if isinstance(author, dict):
                author = author.get("name") or "Flipkart Customer"
            title = raw_item.get("title") or raw_item.get("name") or ""
            rating_val = raw_item.get("rating") or raw_item.get("reviewRating")
            if isinstance(rating_val, dict):
                rating_val = rating_val.get("ratingValue")
            try:
                rating = float(rating_val) if rating_val is not None else None
            except Exception:
                rating = None
            date_str = raw_item.get("created") or raw_item.get("datePublished")
            is_verified = bool(raw_item.get("certifiedBuyer") or (raw_item.get("reviewPropertyMap") or {}).get("VERIFIED_PURCHASE"))
            helpful = raw_item.get("helpfulCount") or (raw_item.get("upvote") or {}).get("value", {}).get("count") or 0
            try:
                helpful = int(helpful)
            except Exception:
                helpful = 0

            attrs = raw_item.get("productAttributeList") or []
            variant = ", ".join(f"{a.get('name')}: {a.get('value')}" for a in attrs if a.get("name") and a.get("value")) or None

            r_id = raw_item.get("id") or ""
            if not r_id:
                r_id = hashlib.sha256(f"{author}|{title}|{body}".encode("utf-8")).hexdigest()[:24]
            if not str(r_id).startswith("flipkart_"):
                r_id = f"flipkart_{r_id}"

            clean_body = re.sub(r"\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$", "", str(body), flags=re.IGNORECASE).strip()
            if len(clean_body) < 3:
                return None

            return CustomerReview(
                review_id=r_id,
                reviewer_name=str(author).strip() or "Flipkart Customer",
                review_title=str(title).strip() or None,
                review_text=clean_body,
                rating=rating,
                review_date=str(date_str).strip() if date_str else None,
                verified_purchase=is_verified,
                helpful_votes=helpful,
                product_variant=variant,
                platform="flipkart",
                source="embedded_initial_state"
            )
        return None

    @classmethod
    def _parse_product_page(cls, soup: BeautifulSoup, product_url: str, html_text: str = "") -> Optional[ProductInfo]:
        # Step 1: Try structured state extraction if available
        title = None
        brand = None
        price_val = None
        orig_val = None
        discount = None
        images = []
        raw_specs = {}
        desc = None
        rating = None
        reviews_cnt = None

        m_state = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>", html_text, re.DOTALL)
        if m_state:
            try:
                state_data = json.loads(m_state.group(1))
                pdr = state_data.get("pageDataResponse", {}) or state_data.get("multiWidgetState", {}).get("pageDataResponse", {})
                seo_schema = pdr.get("seoData", {}).get("schema", [])
                for s in seo_schema:
                    if s.get("@type") == "Product":
                        title = s.get("name")
                        brand = (s.get("brand") or {}).get("name") if isinstance(s.get("brand"), dict) else s.get("brand")
                        desc = s.get("description")
                        offers = s.get("offers") or {}
                        if isinstance(offers, dict):
                            price_val = DataNormalizer.parse_price(offers.get("price"))
                        agg = s.get("aggregateRating") or {}
                        if isinstance(agg, dict):
                            rating = float(agg.get("ratingValue")) if agg.get("ratingValue") else None
                            reviews_cnt = int(agg.get("reviewCount")) if agg.get("reviewCount") else None
            except Exception as st_err:
                log_ecom("Flipkart INITIAL_STATE metadata parsing notice", level="DEBUG", details=str(st_err))

        # Title fallback
        if not title:
            title_el = soup.select_one("span.B_NuCI, h1._6EBuvT span, h1.VU-ZEz, h1.yhB1nd")
            if title_el:
                title = title_el.get_text().strip()
        if not title:
            meta_t = soup.select_one("meta[property='og:title'], meta[name='twitter:title']")
            if meta_t and meta_t.get("content"):
                title = meta_t["content"].strip()
        if not title or title.lower() in ["flipkart", "online shopping"]:
            return None

        # Brand fallback
        if not brand:
            brand_el = soup.select_one("span.G6XhRU, span._2J4LW6")
            if brand_el:
                brand = brand_el.get_text().strip()
            elif " " in title:
                brand = title.split()[0]
            else:
                brand = "Flipkart Brand"

        # Price fallback
        if price_val is None:
            price_el = soup.select_one("div.Nx9bqj._4b5DiR, div._30jeq3._16Jk6d, div.Nx9bqj")
            if price_el:
                price_val = DataNormalizer.parse_price(price_el.get_text())

        # Original Price
        orig_el = soup.select_one("div.yRaY8j.A68rqH, div._3I9_wc._2p6lqe, div.yRaY8j")
        if orig_el:
            orig_val = DataNormalizer.parse_price(orig_el.get_text())

        # Discount
        disc_el = soup.select_one("div.UkUFwK span, div._3Ay6Sb._31daqi span, div.UkUFwK")
        if disc_el:
            discount = disc_el.get_text().strip()

        # Images
        for img in soup.select("img._396cs4, img.DByuf4, img._2r_T1I, img[src*='rukminim']"):
            src = img.get("src")
            if src and "http" in src and src not in images and "placeholder" not in src:
                src_hi = re.sub(r"/image/\d+/\d+/", "/image/832/832/", src)
                images.append(src_hi)

        # Specifications
        for row in soup.select("tr._1s_Smc, div._1s_Smc, div.row._1s_Smc, div.GND1H- div.row"):
            label_el = row.select_one("td._1hKmbr, col._1hKmbr, div.col-3-12, div._2H87wv")
            val_el = row.select_one("td._21lJbe, li._21lJbe, div.col-9-12, div._2vZVnT")
            if label_el and val_el:
                k = label_el.get_text().strip()
                v = val_el.get_text().strip()
                if k and v:
                    raw_specs[k] = v

        category = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(category, raw_specs)

        # Description
        if not desc:
            desc_el = soup.select_one("div._1mXcCf, div.RmoJUa")
            desc = desc_el.get_text().strip() if desc_el else "Description available on Flipkart listing."

        description_data = {
            "description": desc or "Not available",
            "features": [v for k, v in list(raw_specs.items())[:5]],
            "highlights": [li.get_text().strip() for li in soup.select("div._2418kt li, div._2c2kV- li")],
            "manufacturer": raw_specs.get("Manufacturer") or "Not available"
        }

        # Variants
        colors = [el.get_text().strip() for el in soup.select("li._3V2wfe, a._1fGeJ5") if el.get_text().strip()]
        storage = [el.get_text().strip() for el in soup.select("a.CDDksN") if any(k in el.get_text().lower() for k in ["gb", "tb"])]
        variants_data = {
            "sizes": [el.get_text().strip() for el in soup.select("a.CDDksN") if not any(k in el.get_text().lower() for k in ["gb", "tb"])],
            "colors": colors or ([raw_specs["Color"]] if "Color" in raw_specs else []),
            "models": [raw_specs["Model Number"]] if "Model Number" in raw_specs else [],
            "storage": storage,
            "options": []
        }

        # Rating fallback
        if rating is None:
            rate_el = soup.select_one("div.XQDdHH, div._3LWZlK")
            if rate_el:
                m = re.search(r"(\d+(\.\d+)?)", rate_el.get_text())
                if m:
                    try:
                        rating = float(m.group(1))
                    except Exception:
                        pass

        # Reviews count fallback
        if reviews_cnt is None:
            cnt_el = soup.select_one("span.Wphh3N, span._2_R_DZ")
            if cnt_el:
                m = re.search(r"([\d,]+)\s+Reviews?", cnt_el.get_text(), re.IGNORECASE)
                if m:
                    try:
                        reviews_cnt = int(m.group(1).replace(",", ""))
                    except Exception:
                        pass

        return ProductInfo(
            product_name=title,
            brand=brand,
            product_images=images[:6],
            current_price=price_val,
            original_price=orig_val,
            discount=discount,
            currency="INR",
            description=desc,
            category=category,
            specifications=specs,
            rating=rating,
            total_reviews_count=reviews_cnt,
            product_url=product_url,
            platform="flipkart",
            description_data=description_data,
            variants_data=variants_data
        )

    @classmethod
    async def extract_product_details(
        cls, url: str, html_content: Optional[str] = None
    ) -> Tuple[Optional[ProductInfo], Optional[str]]:
        valid, resolved_url, err = cls.resolve_product_url(url)
        if not valid:
            return None, err

        html_text = html_content or ""
        if not html_text:
            async with httpx.AsyncClient(timeout=20.0, headers=cls.HEADERS, follow_redirects=True) as client:
                try:
                    resp = await client.get(resolved_url)
                    if resp.status_code == 200:
                        html_text = resp.text
                except Exception as ex:
                    log_ecom("HTTP GET failed on Flipkart product page", level="WARN", details=str(ex))

            if not html_text or len(html_text) < 1000 or "Access Denied" in html_text:
                log_ecom("Launching Playwright browser session for Flipkart page hydration...")
                try:
                    b_mgr = await BrowserManager.get_instance()
                    async with b_mgr.get_page() as page:
                        await page.goto(resolved_url, wait_until="domcontentloaded", timeout=25000)
                        await page.wait_for_timeout(1000)
                        html_text = await page.content()
                except Exception as b_ex:
                    log_ecom("Playwright navigation error on Flipkart PDP", level="ERROR", details=str(b_ex), exc=b_ex)

        if not html_text:
            return None, "Failed to retrieve Flipkart product page content."

        soup = BeautifulSoup(html_text, "lxml")
        product = cls._parse_product_page(soup, resolved_url, html_text)
        return product, html_text

    @classmethod
    def extract_next_page(cls, current_page: int, soup: Optional[BeautifulSoup] = None, **kwargs) -> Optional[str]:
        slug = kwargs.get("slug") or "product"
        item_id = kwargs.get("item_id")
        pid = kwargs.get("pid")
        next_p = current_page + 1
        return f"https://www.flipkart.com/{slug}/product-reviews/{item_id or ''}?pid={pid or ''}&page={next_p}"

    @classmethod
    def _parse_reviews_from_soup(cls, soup: BeautifulSoup) -> List[CustomerReview]:
        items: List[CustomerReview] = []
        cards = cls.discover_review_container(soup)
        seen_card_text = set()
        for card in cards:
            card_text = card.get_text(" ", strip=True)
            if not card_text or card_text in seen_card_text:
                continue
            seen_card_text.add(card_text)

            body_el = card.select_one(
                "div.t-ZTKy div div, div.t-ZTKy, div._6K-7Co, div.ZmyHeo div div, div.ZmyHeo, "
                "[data-testid*='review-text'], div[class*='reviewText'], div[class*='ReviewText']"
            )
            body = body_el.get_text(separator=" ").strip() if body_el else ""
            if not body:
                candidates = card.select("div, p, span")
                long_texts = [
                    el.get_text(" ", strip=True) for el in candidates
                    if len(el.get_text(" ", strip=True)) >= 25
                    and len(el.find_all(["div", "p", "span"], recursive=False)) == 0
                ]
                if long_texts:
                    body = max(long_texts, key=len)

            if body:
                body = re.sub(r"\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$", "", body, flags=re.IGNORECASE).strip()

            title_el = card.select_one("p._2-N8zT, p.z9E0IG, p._2Us4fl, [data-testid*='review-title']")
            title = title_el.get_text().strip() if title_el else ""

            author_el = card.select_one("p._2sc7ZR._2V5EHH, p._2sc7ZR, p._2NsDsF, p._2V5EHH, [data-testid*='review-author']")
            author = author_el.get_text().strip() if author_el else "Flipkart Customer"

            rating_val = None
            rate_el = card.select_one("div._3LWZlK, div.XQDdHH, div[class*='XQDdHH'], div[class*='_3LWZlK']")
            if rate_el:
                m = re.search(r"(\d+(\.\d+)?)", rate_el.get_text())
                if m:
                    try:
                        rating_val = float(m.group(1))
                    except Exception:
                        pass

            date_str = None
            date_candidates = card.select("p._2sc7ZR, p._2NsDsF")
            if len(date_candidates) > 1:
                date_str = date_candidates[1].get_text().strip()
            if not date_str:
                for el in card.find_all(["p", "span"]):
                    t = el.get_text(" ", strip=True)
                    if re.search(r"(?:\d+\s+(?:months?|days?|years?|weeks?|hours?)\s+ago|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*,?\s+\d{4})", t, re.IGNORECASE) and len(t) < 50:
                        date_str = t
                        break

            is_verified = bool(card.select_one("div._1eDkuJ, p._2mcFHG, p._2-5W3i")) or "certified buyer" in card.get_text().lower()

            helpful = 0
            help_el = card.select_one("span._3c3Px5, div._1LmwT9 span, div._2Z07dn span, div[class*='_1LmwT9'] span")
            if help_el:
                m_help = re.search(r"\d+", help_el.get_text())
                if m_help:
                    try:
                        helpful = int(m_help.group(0))
                    except Exception:
                        pass

            variant_el = card.select_one("div._2V5EHH span, div[class*='_2V5EHH']")
            variant = variant_el.get_text().strip() if variant_el else None

            if body and len(body) > 3:
                review_id = f"flipkart_{hashlib.sha256(f'{author}|{title}|{body}'.encode('utf-8')).hexdigest()[:24]}"
                items.append(CustomerReview(
                    review_id=review_id,
                    reviewer_name=author,
                    review_title=title,
                    review_text=body,
                    rating=rating_val,
                    review_date=date_str,
                    verified_purchase=is_verified,
                    helpful_votes=helpful,
                    product_variant=variant,
                    platform="flipkart"
                ))
        return items

    @classmethod
    def _extract_state_reviews(cls, data: Any) -> List[Dict[str, Any]]:
        """Recursively search Flipkart state JSON for review dictionaries."""
        found: List[Dict[str, Any]] = []

        def recurse(obj):
            if isinstance(obj, dict):
                if "text" in obj and "author" in obj and ("rating" in obj or "title" in obj):
                    found.append(obj)
                elif "reviewBody" in obj and "author" in obj:
                    found.append(obj)
                for v in obj.values():
                    recurse(v)
            elif isinstance(obj, list):
                for item in obj:
                    recurse(item)

        recurse(data)
        return found

    @classmethod
    async def extract_reviews(
        cls,
        product_url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None,
        initial_soup: Optional[BeautifulSoup] = None,
        initial_html: str = ""
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        item_id, pid, slug = cls.extract_product_identifiers(product_url)
        base_slug = slug or "product"
        reviews: List[CustomerReview] = []
        paginator = PaginationManager(max_reviews=max_reviews, max_pages=None)

        stats: Dict[str, Any] = {
            "pages_scanned": 0,
            "browser_used": False,
            "stop_reason": "pagination_exhausted",
            "retrieved_reviews": 0,
            "unique_reviews": 0,
            "duplicates_found": 0,
            "review_source_url": product_url,
            "failure_reason": None,
            "platform_limitations": "Flipkart renders reviews across paginated /product-reviews/ routes (10 reviews per page). All publicly accessible pages are parsed until pagination ends."
        }

        # Step 1: Fast direct HTTP pagination on Flipkart's /product-reviews/ endpoint
        if item_id or pid:
            headers = dict(cls.HEADERS)
            headers["Referer"] = f"https://www.flipkart.com/{base_slug}/p/{item_id or ''}?pid={pid or ''}"

            async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
                while paginator.should_continue():
                    page = paginator.current_page
                    rev_url = f"https://www.flipkart.com/{base_slug}/product-reviews/{item_id or ''}?pid={pid or ''}&page={page}"
                    stats["pages_scanned"] += 1
                    stats["review_source_url"] = rev_url

                    if progress_callback:
                        await progress_callback(40 + min(40, page * 6), f"Fetching Flipkart review page {page}...")

                    try:
                        resp = await client.get(rev_url)
                        if resp.status_code != 200:
                            stats["stop_reason"] = f"http_{resp.status_code}"
                            break

                        # Extract structured reviews from window.__INITIAL_STATE__
                        page_reviews: List[CustomerReview] = []
                        m_state = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>", resp.text, re.DOTALL)
                        if m_state:
                            try:
                                state_dict = json.loads(m_state.group(1))
                                raw_review_dicts = cls._extract_state_reviews(state_dict)
                                for r_raw in raw_review_dicts:
                                    norm = cls.normalize_review(r_raw)
                                    if norm:
                                        page_reviews.append(norm)

                                # Check hasMorePages flag in pageDataResponse
                                pdr = state_dict.get("pageDataResponse", {}) or state_dict.get("multiWidgetState", {}).get("pageDataResponse", {})
                                has_more_pages = pdr.get("hasMorePages", True)
                            except Exception as parse_err:
                                log_ecom("Flipkart state JSON parse error", level="WARN", details=str(parse_err))
                                has_more_pages = False
                        else:
                            has_more_pages = False

                        # If state had no reviews, fallback to DOM parsing
                        if not page_reviews:
                            page_soup = BeautifulSoup(resp.text, "lxml")
                            page_reviews = cls._parse_reviews_from_soup(page_soup)
                            has_more_pages = bool(page_soup.select("a._1LKTO3 span, a._9QVEST span, nav._2OZ7Nm a")) or len(page_reviews) >= 8

                        if not page_reviews:
                            stats["stop_reason"] = "no_more_reviews_visible"
                            paginator.record_page_results(0, has_more=False)
                            break

                        known = {r.review_id for r in reviews if r.review_id}
                        fresh = [r for r in page_reviews if r.review_id not in known]
                        if not fresh:
                            stats["stop_reason"] = "duplicate_page_reached"
                            paginator.record_page_results(0, has_more=False)
                            break

                        remaining = (max_reviews - len(reviews)) if max_reviews is not None else len(fresh)
                        selected = fresh[:remaining]
                        reviews.extend(selected)
                        stats["retrieved_reviews"] += len(page_reviews)

                        log_ecom(f"Flipkart review page {page}: parsed {len(selected)} new reviews (total so far: {len(reviews)})")
                        paginator.record_page_results(len(selected), has_more=has_more_pages and (len(fresh) >= 8))

                        if not has_more_pages:
                            stats["stop_reason"] = "pagination_complete"
                            break

                        await asyncio.sleep(0.2)
                    except Exception as pg_err:
                        log_ecom("Flipkart paginated review step error", level="WARN", details=str(pg_err))
                        break

        # Step 2: If no reviews retrieved yet, parse initial product page state & DOM
        if not reviews and initial_html:
            m_init = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>", initial_html, re.DOTALL)
            if m_init:
                try:
                    init_data = json.loads(m_init.group(1))
                    raw_revs = cls._extract_state_reviews(init_data)
                    for r_raw in raw_revs:
                        norm = cls.normalize_review(r_raw)
                        if norm:
                            reviews.append(norm)
                    if reviews:
                        log_ecom(f"Extracted {len(reviews)} reviews from Flipkart initial product state")
                except Exception:
                    pass

        if not reviews and initial_soup:
            pdp_dom_reviews = cls._parse_reviews_from_soup(initial_soup)
            if pdp_dom_reviews:
                reviews.extend(pdp_dom_reviews)
                log_ecom(f"Extracted {len(pdp_dom_reviews)} reviews from Flipkart product page DOM")

        # Step 3: Browser fallback if still zero reviews
        if not reviews:
            rev_url = f"https://www.flipkart.com/{base_slug}/product-reviews/{item_id or ''}?pid={pid or ''}&page=1" if (item_id or pid) else None
            browser_reviews, browser_stats = await collect_public_reviews(
                product_url, "flipkart", initial_reviews=reviews, max_reviews=max_reviews,
                progress_callback=progress_callback, review_page_url=rev_url
            )
            reviews = browser_reviews
            stats = browser_stats

        unique_reviews, dup_count = DataValidator.deduplicate_reviews(reviews)
        stats["unique_reviews"] = len(unique_reviews)
        stats["retrieved_reviews"] = max(stats["retrieved_reviews"], len(reviews))
        stats["duplicates_found"] = dup_count

        return unique_reviews, stats

    @classmethod
    async def extract_product_and_reviews(
        cls,
        url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[Optional[ProductInfo], List[CustomerReview], str]:
        log_ecom("E-commerce extraction started", details=f"URL: {url}")
        log_ecom("Platform detected: Flipkart")

        valid, resolved_url, err_msg = cls.resolve_product_url(url)
        if not valid:
            log_ecom(f"Flipkart URL rejected: {err_msg}", level="ERROR")
            return None, [], f"Security filter rejected URL: {err_msg}"

        item_id, pid, slug = cls.extract_product_identifiers(resolved_url)
        log_ecom(f"Identifiers: item_id={item_id}, pid={pid}, slug={slug}")

        if progress_callback:
            await progress_callback(15, f"Fetching Flipkart product listing ({item_id or pid or 'direct'})...")

        product, html_text = await cls.extract_product_details(resolved_url)
        if not product:
            log_zero_reviews_reason("Could not extract product metadata from Flipkart", "flipkart", resolved_url)
            return None, [], "Could not extract valid product details from Flipkart page."

        log_ecom("Product page loaded")
        log_ecom(f"Product details extracted: {product.product_name[:50]} (Price: ₹{product.current_price or 'N/A'})")

        if progress_callback:
            await progress_callback(40, f"Extracted product: {product.product_name[:40]}... (Price: ₹{product.current_price or 'N/A'})")

        soup = BeautifulSoup(html_text or "", "lxml")
        log_ecom("Review section detected")

        unique_reviews, collection_stats = await cls.extract_reviews(
            resolved_url, max_reviews=max_reviews, progress_callback=progress_callback,
            initial_soup=soup, initial_html=html_text or ""
        )

        log_ecom(f"Review cards discovered: {collection_stats.get('retrieved_reviews', len(unique_reviews))}")
        log_ecom(f"Valid reviews parsed: {len(unique_reviews)}")
        log_ecom(f"Pagination: {'next page available' if collection_stats.get('pages_scanned', 0) > 1 else 'completed'}")
        log_ecom(f"Total unique reviews collected: {len(unique_reviews)}")

        reported_count = cls.get_reported_review_count(product)
        collection_stats["reported_reviews"] = reported_count
        collection_stats["retrieved_reviews"] = len(unique_reviews)

        product.completeness = DataValidator.evaluate_product_completeness(product)
        product.extraction_info = {
            **(product.extraction_info or {}),
            "review_collection": collection_stats,
            "diagnostics": collection_stats,
            "reported_reviews": reported_count,
            "retrieved_reviews": len(unique_reviews),
            "unique_reviews": len(unique_reviews),
            "duplicates_found": collection_stats.get("duplicates_found", 0),
            "stop_reason": collection_stats.get("stop_reason"),
            "failure_reason": collection_stats.get("failure_reason"),
            "collection_mode": "all_accessible" if max_reviews is None else "limited",
            "requested_limit": max_reviews
        }

        if unique_reviews:
            msg = f"Extracted product details and {len(unique_reviews)} customer reviews from Flipkart."
        elif reported_count == 0:
            msg = "Product details extracted successfully. No customer reviews have been published for this item on Flipkart."
            log_zero_reviews_reason("No public reviews published on Flipkart", "flipkart", resolved_url)
        else:
            msg = collection_stats.get("failure_reason") or "Extracted product details from Flipkart, but customer reviews could not be retrieved from public session."
            log_zero_reviews_reason(msg, "flipkart", resolved_url)

        return product, unique_reviews, msg

