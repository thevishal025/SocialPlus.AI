"""SocialPlus.ai — AJIO Platform Extraction Adapter.

Extracts complete product metadata, technical specifications, variants, and customer reviews
for ajio.com using the public catalog endpoints and dynamic review hydration.
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


class AjioAdapter(BaseEcommerceAdapter):
    """Deep extraction adapter for AJIO."""

    platform_key = "ajio"
    display_name = "AJIO"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    }

    @classmethod
    def extract_product_code(cls, url: str) -> Optional[str]:
        m = re.search(r"/p/([a-zA-Z0-9_-]+)", url)
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
        return product_url

    @classmethod
    def discover_review_container(cls, soup: BeautifulSoup) -> List[Any]:
        return soup.select(
            "div.review-card, div[class*='reviewItem'], div[class*='ReviewCard'], "
            "div.review-list-item, div.prod-rating-reviews .review, div[class*='review-row'], div[data-testid*='review']"
        )

    @classmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        return CustomerReview(**raw_item)

    @classmethod
    def _parse_product_api(cls, data: dict, product_url: str) -> Optional[ProductInfo]:
        if not data:
            return None
        title = data.get("name") or data.get("fn")
        brand = (data.get("brandName") or (data.get("brand") or {}).get("name")) if isinstance(data.get("brand"), dict) else data.get("brandName")
        if not title:
            return None

        price = None
        if "price" in data and isinstance(data["price"], dict):
            price = data["price"].get("value")
        elif "price" in data:
            price = DataNormalizer.parse_price(data["price"])

        orig_price = None
        if "wasPriceData" in data and isinstance(data["wasPriceData"], dict):
            orig_price = data["wasPriceData"].get("value")

        disc = data.get("discountPercent") or data.get("discount")
        if disc and not str(disc).endswith("%"):
            disc = f"{disc}% off"

        images = []
        for img in data.get("images", []):
            if isinstance(img, dict) and "url" in img:
                images.append(img["url"])
            elif isinstance(img, str):
                images.append(img)

        raw_specs = {}
        for entry in data.get("featureData", []):
            if isinstance(entry, dict) and "name" in entry and "value" in entry:
                raw_specs[entry["name"]] = entry["value"]

        cat = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(cat, raw_specs)

        rating = float(data["averageRating"]) if data.get("averageRating") else None
        rev_cnt = int(data["ratingCount"]) if data.get("ratingCount") else None

        sizes = []
        for s in data.get("variantOptions", []):
            if isinstance(s, dict) and "sizeData" in s:
                sizes.append(s["sizeData"].get("sizeDescription"))

        variants_data = {
            "sizes": [s for s in sizes if s],
            "colors": [raw_specs["Color"]] if "Color" in raw_specs else [],
            "models": [],
            "storage": [],
            "options": []
        }

        return ProductInfo(
            product_name=title,
            brand=brand or "AJIO Fashion",
            product_images=images[:6],
            current_price=price,
            original_price=orig_price,
            discount=disc,
            currency="INR",
            description=data.get("description", "AJIO Fashion Product"),
            category=cat,
            specifications=specs,
            rating=rating,
            total_reviews_count=rev_cnt,
            product_url=product_url,
            platform="ajio",
            description_data={"description": data.get("description", "Not available"), "features": [], "highlights": [], "manufacturer": "AJIO"},
            variants_data=variants_data
        )

    @classmethod
    def _parse_product_soup(cls, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        title_el = soup.select_one("h1.prod-name, h1.name")
        brand_el = soup.select_one("h2.brand-name, a.brand-name")
        title = title_el.get_text().strip() if title_el else None
        brand = brand_el.get_text().strip() if brand_el else "AJIO Fashion"

        if not title:
            meta_t = soup.select_one("meta[property='og:title']")
            title = meta_t["content"].strip() if meta_t and meta_t.get("content") else None

        if not title:
            return None

        price_el = soup.select_one("div.prod-sp, span.prod-sp")
        price = DataNormalizer.parse_price(price_el.get_text()) if price_el else None

        orig_el = soup.select_one("span.prod-cp")
        orig_price = DataNormalizer.parse_price(orig_el.get_text()) if orig_el else None

        disc_el = soup.select_one("span.prod-discnt")
        disc = disc_el.get_text().strip() if disc_el else None

        images = []
        for img in soup.select("img.prod-img, img[src*='ajio']"):
            src = img.get("src")
            if src and src.startswith("http") and src not in images and "banner" not in src:
                images.append(src)

        raw_specs = {}
        for row in soup.select("ul.prod-list li"):
            text = row.get_text().strip()
            if ":" in text:
                k, v = text.split(":", 1)
                raw_specs[k.strip()] = v.strip()

        cat = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(cat, raw_specs)

        return ProductInfo(
            product_name=title,
            brand=brand,
            product_images=images[:6],
            current_price=price,
            original_price=orig_price,
            discount=disc,
            currency="INR",
            description="AJIO Fashion Catalog Item",
            category=cat,
            specifications=specs,
            product_url=product_url,
            platform="ajio"
        )

    @classmethod
    async def extract_product_details(
        cls, url: str, html_content: Optional[str] = None
    ) -> Tuple[Optional[ProductInfo], Optional[str]]:
        valid, resolved_url, err = cls.resolve_product_url(url)
        if not valid:
            return None, err

        code = cls.extract_product_code(resolved_url)
        product = None

        if code:
            api_url = f"https://www.ajio.com/api/p/{code}"
            try:
                async with httpx.AsyncClient(timeout=15.0, headers=cls.HEADERS) as client:
                    resp = await client.get(api_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        product = cls._parse_product_api(data, resolved_url)
            except Exception as ex:
                log_ecom("AJIO API check notice", level="DEBUG", details=str(ex))

        html_text = html_content or ""
        if not product and not html_text:
            async with httpx.AsyncClient(timeout=20.0, headers=cls.HEADERS, follow_redirects=True) as client:
                try:
                    resp = await client.get(resolved_url)
                    if resp.status_code == 200:
                        html_text = resp.text
                except Exception as ex:
                    log_ecom("HTTP GET failed on AJIO product page", level="WARN", details=str(ex))

            if not html_text or len(html_text) < 1000:
                log_ecom("Launching Playwright browser session for AJIO...")
                try:
                    b_mgr = await BrowserManager.get_instance()
                    async with b_mgr.get_page() as page:
                        await page.goto(resolved_url, wait_until="domcontentloaded", timeout=25000)
                        await page.wait_for_timeout(1000)
                        html_text = await page.content()
                except Exception as b_ex:
                    log_ecom("Playwright navigation error on AJIO PDP", level="ERROR", details=str(b_ex), exc=b_ex)

        if not product and html_text:
            soup = BeautifulSoup(html_text, "lxml")
            product = cls._parse_product_soup(soup, resolved_url)

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
        reviews, collection_stats = await collect_public_reviews(
            product_url, "ajio", max_reviews=max_reviews, progress_callback=progress_callback
        )
        unique_reviews, dup_count = DataValidator.deduplicate_reviews(reviews)
        collection_stats["unique_reviews"] = len(unique_reviews)
        collection_stats["duplicates_found"] = dup_count
        return unique_reviews, collection_stats

    @classmethod
    async def extract_product_and_reviews(
        cls,
        url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[Optional[ProductInfo], List[CustomerReview], str]:
        log_ecom("E-commerce extraction started", details=f"URL: {url}")
        log_ecom("Platform detected: AJIO")

        valid, resolved_url, err_msg = cls.resolve_product_url(url)
        if not valid:
            log_ecom(f"AJIO URL rejected: {err_msg}", level="ERROR")
            return None, [], f"Security filter rejected URL: {err_msg}"

        code = cls.extract_product_code(resolved_url)
        if progress_callback:
            await progress_callback(15, f"Connecting to AJIO catalog ({code or 'direct URL'})...")

        product, html_text = await cls.extract_product_details(resolved_url)
        if not product:
            log_zero_reviews_reason("Could not extract product metadata from AJIO", "ajio", resolved_url)
            return None, [], "Could not extract valid product details from AJIO page."

        log_ecom("Product page loaded")
        log_ecom(f"Product details extracted: {product.product_name[:50]} (Price: ₹{product.current_price or 'N/A'})")

        if progress_callback:
            await progress_callback(40, f"Extracted product: {product.product_name[:40]}... (Price: ₹{product.current_price or 'N/A'})")

        log_ecom("Review section detected")
        unique_reviews, collection_stats = await cls.extract_reviews(
            resolved_url, max_reviews=max_reviews, progress_callback=progress_callback
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
            msg = f"Extracted product details and {len(unique_reviews)} customer reviews from AJIO."
        elif reported_count == 0:
            msg = "Product details extracted successfully. No customer reviews have been published for this item on AJIO."
            log_zero_reviews_reason("No public reviews published on AJIO", "ajio", resolved_url)
        else:
            msg = collection_stats.get("failure_reason") or "Extracted product details from AJIO, but customer reviews could not be retrieved from public session."
            log_zero_reviews_reason(msg, "ajio", resolved_url)

        return product, unique_reviews, msg

