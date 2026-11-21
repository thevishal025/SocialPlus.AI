"""SocialPlus.ai — Meesho Platform Extraction Adapter.

Extracts complete product metadata, technical specifications, variants, and customer reviews
for meesho.com using structured Next.js state data and dynamic UI hydration.
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


class MeeshoAdapter(BaseEcommerceAdapter):
    """Deep extraction adapter for Meesho."""

    platform_key = "meesho"
    display_name = "Meesho"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    }

    @classmethod
    def extract_product_id(cls, url: str) -> Optional[str]:
        m = re.search(r"/p/([a-zA-Z0-9]+)", url)
        if m:
            return m.group(1)
        return None

    extract_product_code = extract_product_id

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
            "div[class*='ReviewCard'], div[class*='Card__CardWrapper'], div[class*='ReviewStyled'], "
            "div[class*='CommentCard'], div[class*='Card-sc-'], div[data-testid*='review'], div[class*='review-card']"
        )

    @classmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        body = raw_item.get("review") or raw_item.get("comment") or raw_item.get("text") or ""
        if not body:
            return None
        clean_body = re.sub(r"\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$", "", str(body), flags=re.IGNORECASE).strip()
        r_raw_id = str(raw_item.get("id") or raw_item.get("review_id") or "")
        rid = f"meesho_{r_raw_id}" if r_raw_id else f"meesho_{hashlib.sha256(clean_body.encode('utf-8')).hexdigest()[:24]}"
        rating = float(raw_item["rating"]) if raw_item.get("rating") is not None else None

        return CustomerReview(
            review_id=rid,
            reviewer_name=raw_item.get("user_name") or raw_item.get("author") or "Meesho Customer",
            review_title=raw_item.get("title") or raw_item.get("headline") or None,
            review_text=clean_body,
            rating=rating,
            review_date=raw_item.get("created_at") or raw_item.get("date"),
            verified_purchase=bool(raw_item.get("verified_purchase", False)),
            platform="meesho",
            source="embedded_public_page"
        )

    @classmethod
    def _parse_product(cls, soup: BeautifulSoup, product_url: str, product_id: Optional[str] = None) -> Optional[ProductInfo]:
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script and next_data_script.string:
            try:
                data = json.loads(next_data_script.string)
                props = data.get("props", {}).get("pageProps", {})
                p_data = props.get("initialState", {}).get("product", {}).get("details", {}) or props.get("productDetails", {})

                if p_data:
                    title = p_data.get("name") or p_data.get("title")
                    price = float(p_data["price"]) if "price" in p_data and p_data["price"] else None
                    orig_price = float(p_data["mrp"]) if "mrp" in p_data and p_data["mrp"] else None
                    disc = f"{int(p_data['discount'])}% off" if p_data.get("discount") else None
                    desc = p_data.get("description")

                    images = p_data.get("images", [])
                    if isinstance(images, list):
                        images = [img if isinstance(img, str) else img.get("url") for img in images if img]

                    raw_specs = {}
                    for attr in p_data.get("attributes", []):
                        if isinstance(attr, dict) and "name" in attr and "value" in attr:
                            raw_specs[attr["name"]] = str(attr["value"])

                    cat = SpecificationParser.detect_category(title, raw_specs)
                    specs = SpecificationParser.structure_specifications(cat, raw_specs)

                    rating = float(p_data["rating"]) if "rating" in p_data and p_data["rating"] else None
                    rev_cnt = int(p_data["review_count"]) if "review_count" in p_data and p_data["review_count"] else None

                    sizes = [s.get("name") for s in p_data.get("sizes", []) if isinstance(s, dict) and s.get("name")]
                    variants_data = {
                        "sizes": sizes,
                        "colors": [raw_specs["Color"]] if "Color" in raw_specs else [],
                        "models": [],
                        "storage": [],
                        "options": []
                    }

                    return ProductInfo(
                        product_name=title,
                        brand=p_data.get("supplier_name") or "Meesho Supplier",
                        product_images=images[:6],
                        current_price=price,
                        original_price=orig_price,
                        discount=disc,
                        currency="INR",
                        description=desc,
                        category=cat,
                        specifications=specs,
                        rating=rating,
                        total_reviews_count=rev_cnt,
                        product_url=product_url,
                        platform="meesho",
                        description_data={"description": desc or "Not available", "features": [], "highlights": [], "manufacturer": "Meesho Supplier"},
                        variants_data=variants_data
                    )
            except Exception as e:
                log_ecom("Meesho Next.js state parsing warning", level="WARN", details=str(e))

        # Fallback to HTML DOM parsing
        title_el = soup.select_one("h1") or soup.select_one("span[class*='Text__StyledText']")
        title = title_el.get_text().strip() if title_el else None
        if not title or title.lower() in ["meesho product", "meesho", "online shopping"]:
            return None

        price_el = soup.select_one("h4") or soup.find(string=re.compile(r"₹\s*\d+"))
        price = DataNormalizer.parse_price(price_el) if price_el else None

        desc_el = soup.find(["p", "div"], string=re.compile(r"Name\s*:", re.IGNORECASE))
        desc = desc_el.get_text().strip() if desc_el else None

        raw_specs = {}
        if desc:
            for line in desc.split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    raw_specs[parts[0].strip()] = parts[1].strip()

        category = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(category, raw_specs)

        images = []
        for img in soup.select("img[src*='meesho']"):
            src = img.get("src")
            if src and "256" not in src and src not in images:
                images.append(src)

        return ProductInfo(
            product_name=title,
            brand="Meesho Supplier",
            product_images=images[:6],
            current_price=price,
            currency="INR",
            description=desc,
            category=category,
            specifications=specs,
            product_url=product_url,
            platform="meesho"
        )

    @classmethod
    async def extract_product_details(
        cls, url: str, html_content: Optional[str] = None
    ) -> Tuple[Optional[ProductInfo], Optional[str]]:
        valid, resolved_url, err = cls.resolve_product_url(url)
        if not valid:
            return None, err

        product_id = cls.extract_product_id(resolved_url)
        html_text = html_content or ""
        if not html_text:
            async with httpx.AsyncClient(timeout=20.0, headers=cls.HEADERS, follow_redirects=True) as client:
                try:
                    resp = await client.get(resolved_url)
                    if resp.status_code == 200:
                        html_text = resp.text
                except Exception as ex:
                    log_ecom("HTTP GET failed on Meesho product page", level="WARN", details=str(ex))

            if not html_text or len(html_text) < 1000:
                log_ecom("Launching Playwright browser session for Meesho hydration...")
                try:
                    b_mgr = await BrowserManager.get_instance()
                    async with b_mgr.get_page() as page:
                        await page.goto(resolved_url, wait_until="domcontentloaded", timeout=25000)
                        await page.wait_for_timeout(1000)
                        html_text = await page.content()
                except Exception as b_ex:
                    log_ecom("Playwright navigation error on Meesho PDP", level="ERROR", details=str(b_ex), exc=b_ex)

        if not html_text:
            return None, "Failed to retrieve Meesho product page."

        soup = BeautifulSoup(html_text, "lxml")
        product = cls._parse_product(soup, resolved_url, product_id)
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
            next_data_script = initial_soup.find("script", id="__NEXT_DATA__")
            if next_data_script and next_data_script.string:
                try:
                    data = json.loads(next_data_script.string)
                    page_props = data.get("props", {}).get("pageProps", {})
                    raw_revs = page_props.get("reviews", {}).get("data", []) or page_props.get("productReviews", [])
                    for item in raw_revs:
                        norm = cls.normalize_review(item)
                        if norm:
                            reviews.append(norm)
                except Exception:
                    pass

        browser_reviews, browser_stats = await collect_public_reviews(
            product_url, "meesho", initial_reviews=reviews, max_reviews=max_reviews,
            progress_callback=progress_callback
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
        log_ecom("Platform detected: Meesho")

        valid, resolved_url, err_msg = cls.resolve_product_url(url)
        if not valid:
            log_ecom(f"Meesho URL rejected: {err_msg}", level="ERROR")
            return None, [], f"Security filter rejected URL: {err_msg}"

        product_id = cls.extract_product_id(resolved_url)
        if progress_callback:
            await progress_callback(15, f"Fetching Meesho product listing ({product_id or 'direct'})...")

        product, html_text = await cls.extract_product_details(resolved_url)
        if not product:
            log_zero_reviews_reason("Could not extract product metadata from Meesho", "meesho", resolved_url)
            return None, [], "Could not extract valid product details from Meesho page."

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
            msg = f"Extracted product details and {len(unique_reviews)} customer reviews from Meesho."
        elif reported_count == 0:
            msg = "Product details extracted successfully. No customer reviews have been published for this item on Meesho."
            log_zero_reviews_reason("No public reviews published on Meesho", "meesho", resolved_url)
        else:
            msg = collection_stats.get("failure_reason") or "Extracted product details from Meesho, but customer reviews could not be retrieved from public session."
            log_zero_reviews_reason(msg, "meesho", resolved_url)

        return product, unique_reviews, msg

