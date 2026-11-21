"""SocialPlus.ai — Myntra Platform Extraction Adapter.

Extracts complete product metadata, technical specifications, variants, and customer reviews
for myntra.com using product page data and the dedicated /reviews/{style_id} interface.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

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


class MyntraAdapter(BaseEcommerceAdapter):
    """Deep extraction adapter for Myntra."""

    platform_key = "myntra"
    display_name = "Myntra"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    }

    @classmethod
    def extract_style_id(cls, url: str) -> Optional[str]:
        m = re.search(r"/(\d+)(?:/buy|\?|$)", url)
        if m:
            return m.group(1)
        return None

    @classmethod
    def resolve_product_url(cls, url: str) -> Tuple[bool, str, str]:
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            return False, "", err_msg or "URL rejected by safety filter."
        return True, resolved_url, ""

    @classmethod
    def navigate_to_reviews(cls, product_url: str, **identifiers) -> Optional[str]:
        style_id = identifiers.get("style_id") or cls.extract_style_id(product_url)
        if style_id:
            return f"https://www.myntra.com/reviews/{style_id}"
        return product_url

    @classmethod
    def discover_review_container(cls, soup: BeautifulSoup) -> List[Any]:
        return soup.select("div.user-review-main, div.detailed-reviews-userReviewsContainer, div[class*='userReviewWrapper']")

    @classmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        return CustomerReview(**raw_item)

    @classmethod
    def _parse_product(cls, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        title = None
        brand = None
        price = None
        orig_price = None
        discount = None
        desc = None
        rating = None
        rev_count = None
        images = []
        raw_specs = {}

        # 1. Check window.__myx script state
        myx_script = soup.find("script", text=re.compile(r"pdpData"))
        if myx_script and myx_script.string:
            try:
                m_json = re.search(r"pdpData\s*=\s*(\{.*?\});", myx_script.string)
                if m_json:
                    pdp_json = json.loads(m_json.group(1))
                    data = pdp_json.get("data", {})
                    title = data.get("name")
                    brand = (data.get("brand") or {}).get("name") if isinstance(data.get("brand"), dict) else data.get("brand")
                    price_data = data.get("price", {})
                    price = float(price_data.get("discounted") or price_data.get("mrp") or 0) or None
                    orig_price = float(price_data.get("mrp") or 0) or None
                    discount = f"{price_data.get('discountPercent')}% off" if price_data.get("discountPercent") else None
                    desc = (data.get("productDetails") or [{}])[0].get("description")
                    ratings_data = data.get("ratings", {})
                    rating = float(ratings_data.get("averageRating") or 0) or None
                    rev_count = int(ratings_data.get("totalCount") or 0) or None
                    for media in data.get("media", {}).get("albums", []):
                        for img_obj in media.get("images", []):
                            if img_obj.get("src"):
                                images.append(img_obj["src"])
                    for spec in data.get("articleAttributes", {}).items():
                        raw_specs[spec[0]] = str(spec[1])
            except Exception as e:
                log_ecom("Myntra pdpData parsing notice", level="DEBUG", details=str(e))

        # DOM fallbacks
        if not title:
            title_el = soup.select_one("h1.pdp-name, h1.pdp-title")
            brand_el = soup.select_one("h1.pdp-title, a.pdp-brand")
            title = title_el.get_text().strip() if title_el else None
            brand = brand_el.get_text().strip() if brand_el else "Myntra Fashion"

        if not title:
            return None

        if price is None:
            price_el = soup.select_one("span.pdp-price strong, span.pdp-price")
            price = DataNormalizer.parse_price(price_el.get_text()) if price_el else None

        if orig_price is None:
            mrp_el = soup.select_one("span.pdp-mrp s")
            orig_price = DataNormalizer.parse_price(mrp_el.get_text()) if mrp_el else None

        if not discount:
            disc_el = soup.select_one("span.pdp-discount")
            discount = disc_el.get_text().strip() if disc_el else None

        if not images:
            for img in soup.select("div.image-grid-image, img[src*='myntassets']"):
                src = img.get("src") or img.get("style")
                if src and "http" in src:
                    m_url = re.search(r"https?://[^\s'\"\)]+", src)
                    if m_url and m_url.group(0) not in images:
                        images.append(m_url.group(0))

        if not raw_specs:
            for row in soup.select("div.index-row"):
                k_el = row.select_one("div.index-rowKey")
                v_el = row.select_one("div.index-rowValue")
                if k_el and v_el:
                    raw_specs[k_el.get_text().strip()] = v_el.get_text().strip()

        cat = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(cat, raw_specs)

        if rating is None:
            rate_el = soup.select_one("div.index-overallRating div")
            if rate_el:
                try:
                    rating = float(rate_el.get_text().strip())
                except Exception:
                    pass

        if rev_count is None:
            cnt_el = soup.select_one("div.index-ratingsCount")
            if cnt_el:
                m_c = re.search(r"([\d,]+)", cnt_el.get_text())
                if m_c:
                    try:
                        rev_count = int(m_c.group(1).replace(",", ""))
                    except Exception:
                        pass

        return ProductInfo(
            product_name=title,
            brand=brand,
            product_images=images[:6],
            current_price=price,
            original_price=orig_price,
            discount=discount,
            currency="INR",
            description=desc,
            category=cat,
            specifications=specs,
            rating=rating,
            total_reviews_count=rev_count,
            product_url=product_url,
            platform="myntra"
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
                    log_ecom("HTTP GET failed on Myntra product page", level="WARN", details=str(ex))

            if not html_text or len(html_text) < 1000 or "Access Denied" in html_text:
                log_ecom("Launching Playwright browser session for Myntra...")
                try:
                    b_mgr = await BrowserManager.get_instance()
                    async with b_mgr.get_page() as page:
                        await page.goto(resolved_url, wait_until="domcontentloaded", timeout=25000)
                        await page.wait_for_timeout(1000)
                        html_text = await page.content()
                except Exception as b_ex:
                    log_ecom("Playwright navigation error on Myntra PDP", level="ERROR", details=str(b_ex), exc=b_ex)

        if not html_text:
            return None, "Failed to retrieve Myntra product page."

        soup = BeautifulSoup(html_text, "lxml")
        product = cls._parse_product(soup, resolved_url)
        return product, html_text

    @classmethod
    def extract_next_page(cls, current_page: int, soup: Optional[BeautifulSoup] = None, **kwargs) -> Optional[str]:
        return None

    @classmethod
    async def extract_reviews(
        cls,
        product_url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None,
        initial_soup: Optional[BeautifulSoup] = None
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        reviews: List[CustomerReview] = []
        if initial_soup:
            cards = cls.discover_review_container(initial_soup)
            for card in cards:
                text_el = card.select_one("div.user-review-reviewTextWrapper, div.review-text, p")
                author_el = card.select_one("div.user-review-left span, span.user-review-userName, span.author")
                rate_el = card.select_one("div.user-review-starRating, span.user-review-rating")
                date_el = card.select_one("div.user-review-reviewDate, span.user-review-reviewDate")
                verified_el = card.select_one("div.user-review-verifiedBuyer")
                upvote_el = card.select_one("span.user-review-upvoteCount")
                size_el = card.select_one("span.user-review-userSize")

                body = text_el.get_text(" ", strip=True) if text_el else ""
                if not body or len(body) < 3:
                    continue

                body = re.sub(r"\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$", "", body, flags=re.IGNORECASE).strip()
                rating = None
                if rate_el:
                    match = re.search(r"([1-5](?:\.\d+)?)", rate_el.get_text(" ", strip=True))
                    if match:
                        rating = float(match.group(1))

                helpful = 0
                if upvote_el:
                    m_up = re.search(r"\d+", upvote_el.get_text())
                    if m_up:
                        try:
                            helpful = int(m_up.group(0))
                        except Exception:
                            pass

                author = author_el.get_text(" ", strip=True) if author_el else "Myntra Customer"
                rid = f"myntra_{hashlib.sha256(f'{author}|{body}'.encode('utf-8')).hexdigest()[:24]}"
                reviews.append(CustomerReview(
                    review_id=rid,
                    reviewer_name=author,
                    review_text=body,
                    rating=rating,
                    review_date=date_el.get_text(" ", strip=True) if date_el else None,
                    verified_purchase=bool(verified_el) or "verified" in card.get_text().lower(),
                    helpful_votes=helpful,
                    product_variant=size_el.get_text(" ", strip=True) if size_el else None,
                    platform="myntra",
                    source="public_product_html"
                ))

        style_id = cls.extract_style_id(product_url)
        review_url = f"https://www.myntra.com/reviews/{style_id}" if style_id else None

        browser_reviews, browser_stats = await collect_public_reviews(
            product_url, "myntra", initial_reviews=reviews, max_reviews=max_reviews,
            progress_callback=progress_callback, review_page_url=review_url
        )
        unique_reviews, dup_count = DataValidator.deduplicate_reviews(browser_reviews)
        browser_stats["unique_reviews"] = len(unique_reviews)
        browser_stats["duplicates_found"] = dup_count
        return unique_reviews, browser_stats

    @classmethod
    async def extract_product_and_reviews(
        cls,
        url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[Optional[ProductInfo], List[CustomerReview], str]:
        log_ecom("E-commerce extraction started", details=f"URL: {url}")
        log_ecom("Platform detected: Myntra")

        valid, resolved_url, err_msg = cls.resolve_product_url(url)
        if not valid:
            log_ecom(f"Myntra URL rejected: {err_msg}", level="ERROR")
            return None, [], f"Security filter rejected URL: {err_msg}"

        style_id = cls.extract_style_id(resolved_url)
        if progress_callback:
            await progress_callback(15, f"Connecting to Myntra catalog ({style_id or 'direct URL'})...")

        product, html_text = await cls.extract_product_details(resolved_url)
        if not product:
            log_zero_reviews_reason("Could not extract product metadata from Myntra", "myntra", resolved_url)
            return None, [], "Could not extract valid product details from Myntra page."

        log_ecom("Product page loaded")
        log_ecom(f"Product details extracted: {product.product_name[:50]} (Price: ₹{product.current_price or 'N/A'})")

        if progress_callback:
            await progress_callback(40, f"Extracted product: {product.product_name[:40]}... (Price: ₹{product.current_price or 'N/A'})")

        soup = BeautifulSoup(html_text or "", "lxml")
        log_ecom("Review section detected")

        unique_reviews, collection_stats = await cls.extract_reviews(
            resolved_url, max_reviews=max_reviews, progress_callback=progress_callback, initial_soup=soup
        )

        log_ecom(f"Review cards discovered: {collection_stats.get('retrieved_reviews', len(unique_reviews))}")
        log_ecom(f"Valid reviews parsed: {len(unique_reviews)}")
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
            msg = f"Extracted product details and {len(unique_reviews)} customer reviews from Myntra."
        elif reported_count == 0:
            msg = "Product details extracted successfully. No customer reviews have been published for this item on Myntra."
            log_zero_reviews_reason("No public reviews published on Myntra", "myntra", resolved_url)
        else:
            msg = collection_stats.get("failure_reason") or "Extracted product details from Myntra, but customer reviews could not be retrieved from public session."
            log_zero_reviews_reason(msg, "myntra", resolved_url)

        return product, unique_reviews, msg

