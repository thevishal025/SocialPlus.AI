"""SocialPlus.ai — Amazon Platform Extraction Adapter.

Extracts complete product metadata, technical specifications, variants, and customer reviews
across all supported Amazon marketplaces (amazon.in, amazon.com, amazon.co.uk, amazon.ca,
amazon.de, amazon.fr, amazon.it, amazon.es, amazon.co.jp, etc.).
"""
from __future__ import annotations

import asyncio
import hashlib
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


class AmazonAdapter(BaseEcommerceAdapter):
    """Deep extraction adapter for Amazon regional marketplaces."""

    platform_key = "amazon"
    display_name = "Amazon"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    @classmethod
    def extract_asin(cls, url: str) -> Optional[str]:
        """Extracts 10-character Amazon Standard Identification Number (ASIN)."""
        patterns = [
            r"/dp/([A-Z0-9]{10})",
            r"/gp/product/([A-Z0-9]{10})",
            r"/product/([A-Z0-9]{10})",
            r"/ASIN/([A-Z0-9]{10})",
            r"[?&]asin=([A-Z0-9]{10})"
        ]
        for p in patterns:
            m = re.search(p, url, re.IGNORECASE)
            if m:
                return m.group(1).upper()
        return None

    @classmethod
    def resolve_product_url(cls, url: str) -> Tuple[bool, str, str]:
        """Resolve short-links and canonicalize marketplace host."""
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            return False, "", err_msg or "URL rejected by safety filter."

        asin = cls.extract_asin(resolved_url)
        parsed = urlparse(resolved_url)
        hostname = (parsed.hostname or "www.amazon.com").lower()
        if hostname.startswith("amzn."):
            hostname = "www.amazon.in"
        elif hostname in ("amazon.in", "amazon.com", "amazon.co.uk", "amazon.ca", "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.co.jp"):
            hostname = f"www.{hostname}"
        elif not hostname.startswith("www."):
            hostname = f"www.{hostname}"

        canonical = f"https://{hostname}/dp/{asin}" if asin else resolved_url
        return True, canonical, ""

    @classmethod
    def navigate_to_reviews(cls, product_url: str, **identifiers) -> Optional[str]:
        asin = identifiers.get("asin") or cls.extract_asin(product_url)
        if not asin:
            return None
        hostname = (urlparse(product_url).hostname or "www.amazon.in").lower()
        return f"https://{hostname}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_1?pageNumber=1&sortBy=recent"

    @classmethod
    def discover_review_container(cls, soup: BeautifulSoup) -> List[Any]:
        return soup.select("div[data-hook='review'], div[id^='customer_review-'], div[data-review-id]")

    @classmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        return CustomerReview(**raw_item)

    @classmethod
    def _parse_reviews_from_soup(cls, soup: BeautifulSoup) -> List[CustomerReview]:
        items: List[CustomerReview] = []
        cards = cls.discover_review_container(soup)
        for r_card in cards:
            r_id = r_card.get("id") or r_card.get("data-review-id") or ""

            # Reviewer Name
            author_el = r_card.select_one("[data-hook='genome-widget'] span.a-profile-name, span.a-profile-name")
            author = author_el.get_text().strip() if author_el else "Amazon Customer"

            # Title
            title_el = r_card.select_one("[data-hook='reviewTitle'] span:not([class]), [data-hook='reviewTitle'], a[data-hook='review-title'] span:not([class]), [data-hook='review-title']")
            title = title_el.get_text().strip() if title_el else ""

            # Body
            body_el = r_card.select_one(
                "[data-hook='reviewRichContentContainer'] span, "
                "[data-hook='reviewRichContentContainer'] p, "
                "[data-hook='reviewText'] p, "
                "[data-hook='reviewText'], "
                "span[data-hook='review-body'] span, "
                "span[data-hook='review-body'], "
                "div[data-hook='review-collapsed']"
            )
            body = body_el.get_text(separator=" ").strip() if body_el else ""

            # Strip Amazon expander teaser prefix
            body = re.sub(
                r"^(?:Brief content visible, double tap to read full content\.\s*|Full content visible, double tap to read brief content\.\s*)+",
                "", body, flags=re.IGNORECASE
            ).strip()

            # Clean trailing read more artifacts
            body = re.sub(r"\s*(?:read more|see more|\.\.\.more|\+ more|\bmore\b)$", "", body, flags=re.IGNORECASE).strip()

            # Rating
            rating_val = None
            rate_el = r_card.select_one("[data-hook='review-star-rating'] span, [data-hook='cmps-review-star-rating'] span, i.a-icon-star span, span.a-icon-alt")
            if rate_el:
                m = re.search(r"(\d+(\.\d+)?)", rate_el.get_text())
                if m:
                    try:
                        rating_val = float(m.group(1))
                    except Exception:
                        pass

            # Date
            date_el = r_card.select_one("span[data-hook='review-date']")
            date_str = date_el.get_text().strip() if date_el else None

            # Verified Purchase
            is_verified = bool(r_card.select_one("span[data-hook='avp-badge']"))
            if not is_verified and r_card.get_text():
                is_verified = "verified purchase" in r_card.get_text().lower()

            # Helpful votes
            helpful = 0
            help_el = r_card.select_one("span[data-hook='helpful-vote-statement'], span.cr-vote-text")
            if help_el:
                help_text = help_el.get_text().strip()
                if re.search(r"one person", help_text, re.IGNORECASE):
                    helpful = 1
                else:
                    m = re.search(r"(\d+)", help_text)
                    if m:
                        try:
                            helpful = int(m.group(1))
                        except Exception:
                            pass

            # Variant
            var_el = r_card.select_one("a[data-hook='format-strip']")
            variant = var_el.get_text().strip() if var_el else None

            if body and len(body) > 3:
                if not r_id:
                    r_id = f"amazon_{hashlib.sha256(f'{author}|{title}|{body}'.encode('utf-8')).hexdigest()[:24]}"
                elif not r_id.startswith("amazon_"):
                    r_id = f"amazon_{r_id}"
                items.append(CustomerReview(
                    review_id=r_id,
                    reviewer_name=author,
                    review_title=title,
                    review_text=body,
                    rating=rating_val,
                    review_date=date_str,
                    verified_purchase=is_verified,
                    helpful_votes=helpful,
                    product_variant=variant,
                    platform="amazon"
                ))
        return items

    @classmethod
    def _parse_product_page(cls, soup: BeautifulSoup, product_url: str, asin: Optional[str] = None) -> Optional[ProductInfo]:
        title_el = soup.select_one("#productTitle, #title, h1.a-size-large")
        title = title_el.get_text().strip() if title_el else None

        if not title:
            meta_t = soup.select_one("meta[name='title'], meta[property='og:title']")
            if meta_t and meta_t.get("content"):
                title = meta_t["content"].strip()

        if not title or title.lower() in ["amazon product", "amazon.in", "online shopping"]:
            return None

        brand_el = soup.select_one("#bylineInfo, .po-brand .a-span9, #brand, a#bylineInfo")
        brand = brand_el.get_text().replace("Brand:", "").replace("Visit the", "").replace("Store", "").strip() if brand_el else None

        price_val = None
        price_el = soup.select_one(".priceToPay span.a-price-whole, #corePrice_desktop .a-price-whole, #priceblock_ourprice, #priceblock_dealprice")
        if price_el:
            price_val = DataNormalizer.parse_price(price_el.get_text())
        else:
            any_price = soup.select_one("span.a-price span.a-offscreen")
            if any_price:
                price_val = DataNormalizer.parse_price(any_price.get_text())

        orig_val = None
        orig_el = soup.select_one("span.a-price.a-text-price span.a-offscreen, span.basisPrice .a-offscreen")
        if orig_el:
            orig_val = DataNormalizer.parse_price(orig_el.get_text())

        discount = None
        disc_el = soup.select_one("span.savingsPercentage, #corePrice_desktop .savingsPercentage")
        if disc_el:
            discount = disc_el.get_text().strip()

        images = []
        for img in soup.select("#landingImage, #imgTagWrapperId img, img.a-dynamic-image"):
            src = img.get("src") or img.get("data-old-hires")
            if src and src.startswith("http") and src not in images and "spinner" not in src:
                images.append(src)

        if not images:
            meta_img = soup.select_one("meta[property='og:image']")
            if meta_img and meta_img.get("content"):
                images.append(meta_img["content"])

        raw_specs = {}
        for row in soup.select("#productDetails_techSpec_section_1 tr, table.a-keyvalue tr, .po-row, #detailBullets_feature_div li"):
            th = row.find(["th", "td", "span"], class_=lambda c: c and "label" in str(c).lower() or "th" in str(row).lower())
            td = row.find(["td", "span"], class_=lambda c: c and "value" in str(c).lower() or "span" in str(row).lower())
            if th and td:
                k = th.get_text().strip()
                v = td.get_text().strip()
                if k and v and k not in raw_specs:
                    raw_specs[k] = v

        category = SpecificationParser.detect_category(title, raw_specs)
        specs = SpecificationParser.structure_specifications(category, raw_specs)

        desc_bullets = [li.get_text().strip() for li in soup.select("#feature-bullets li span.a-list-item") if li.get_text().strip()]
        desc = "\n".join(desc_bullets) if desc_bullets else None
        if not desc:
            p_desc = soup.select_one("#productDescription")
            desc = p_desc.get_text().strip() if p_desc else None

        manufacturer = raw_specs.get("Manufacturer") or raw_specs.get("Packer") or raw_specs.get("Importer") or "Not available"
        description_data = {
            "description": desc or "Not available",
            "features": desc_bullets,
            "highlights": desc_bullets,
            "manufacturer": manufacturer
        }

        sizes = [opt.get_text().strip() for opt in soup.select("#native_dropdown_selected_size_name option, #variation_size_name li") if opt.get_text().strip() and "Select" not in opt.get_text()]
        colors = [el.get("title") or el.get_text().strip() for el in soup.select("#variation_color_name li, .color-swatch") if el.get("title") or el.get_text().strip()]
        storage = [el.get_text().strip() for el in soup.select("#variation_size_name li") if any(k in el.get_text().lower() for k in ["gb", "tb"])]

        variants_data = {
            "sizes": sizes,
            "colors": colors,
            "models": [raw_specs["Item model number"]] if "Item model number" in raw_specs else [],
            "storage": storage,
            "options": []
        }

        rating = None
        r_el = soup.select_one("span[data-hook='rating-out-of-text'], #acrPopover, span.a-icon-alt")
        if r_el:
            m = re.search(r"(\d+(\.\d+)?)", r_el.get_text())
            if m:
                try:
                    rating = float(m.group(1))
                except Exception:
                    pass

        reviews_cnt = None
        cnt_el = soup.select_one("#acrCustomerReviewText")
        if cnt_el:
            cnt_m = re.search(r"([\d,]+)", cnt_el.get_text())
            if cnt_m:
                try:
                    reviews_cnt = int(cnt_m.group(1).replace(",", ""))
                except Exception:
                    pass

        parsed_host = urlparse(product_url).hostname or ""
        currency = (
            "USD" if ".com" in parsed_host and "amazon.in" not in parsed_host else
            "GBP" if "amazon.co.uk" in parsed_host else
            "CAD" if "amazon.ca" in parsed_host else
            "EUR" if any(x in parsed_host for x in ("amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.nl")) else
            "JPY" if "amazon.co.jp" in parsed_host else
            "INR"
        )

        return ProductInfo(
            product_name=title,
            brand=brand,
            product_images=images[:6],
            current_price=price_val,
            original_price=orig_val,
            discount=discount,
            currency=currency,
            description=desc,
            category=category,
            specifications=specs,
            rating=rating,
            total_reviews_count=reviews_cnt,
            product_url=product_url,
            platform="amazon",
            description_data=description_data,
            variants_data=variants_data
        )

    @classmethod
    async def extract_product_details(
        cls, url: str, html_content: Optional[str] = None
    ) -> Tuple[Optional[ProductInfo], Optional[str]]:
        valid, canonical_url, err = cls.resolve_product_url(url)
        if not valid:
            return None, err

        asin = cls.extract_asin(canonical_url)
        html_text = html_content or ""
        if not html_text:
            async with httpx.AsyncClient(timeout=20.0, headers=cls.HEADERS, follow_redirects=True) as client:
                try:
                    resp = await client.get(canonical_url)
                    if resp.status_code == 200:
                        html_text = resp.text
                except Exception as ex:
                    log_ecom(f"HTTP GET failed on Amazon product page", level="WARN", details=str(ex))

            # Fallback to browser if challenged by bot detection
            is_bot_challenge = (not html_text or "Robot Check" in html_text or "Enter the characters you see below" in html_text or "api-services-support@amazon.com" in html_text)
            if is_bot_challenge:
                log_ecom("Anti-bot challenge detected on HTTP client. Launching Playwright browser session...")
                try:
                    b_mgr = await BrowserManager.get_instance()
                    async with b_mgr.get_page() as page:
                        await page.goto(canonical_url, wait_until="commit", timeout=25000)
                        try:
                            await page.wait_for_selector("#productTitle, h1, div[data-hook='review']", timeout=12000)
                        except Exception:
                            pass
                        await page.wait_for_timeout(1000)
                        html_text = await page.content()
                except Exception as b_ex:
                    log_ecom("Playwright navigation error on Amazon PDP", level="ERROR", details=str(b_ex), exc=b_ex)

        if not html_text or "Robot Check" in html_text:
            return None, "Access restricted by Amazon anti-bot security protection."

        soup = BeautifulSoup(html_text, "lxml")
        product = cls._parse_product_page(soup, canonical_url, asin)
        return product, html_text

    @classmethod
    def extract_next_page(cls, current_page: int, soup: Optional[BeautifulSoup] = None, **kwargs) -> Optional[str]:
        if soup:
            next_link = soup.select_one("li.a-last:not(.a-disabled) a")
            if next_link and next_link.get("href"):
                return str(next_link["href"])
        asin = kwargs.get("asin")
        host = kwargs.get("marketplace_host", "www.amazon.in")
        if asin:
            next_p = current_page + 1
            return f"https://{host}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_{next_p}?pageNumber={next_p}&sortBy=recent"
        return None

    @classmethod
    async def extract_reviews(
        cls,
        product_url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None,
        initial_soup: Optional[BeautifulSoup] = None
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        valid, canonical_url, _ = cls.resolve_product_url(product_url)
        asin = cls.extract_asin(canonical_url)
        host = (urlparse(canonical_url).hostname or "www.amazon.in").lower()
        reviews: List[CustomerReview] = []

        # 1. First parse reviews directly present on the Product Detail Page (PDP)
        if initial_soup:
            pdp_reviews = cls._parse_reviews_from_soup(initial_soup)
            if pdp_reviews:
                reviews.extend(pdp_reviews)
                log_ecom(f"Review cards discovered on Amazon product page: {len(pdp_reviews)}")

        # 2. Next attempt to paginate through public reviews if ASIN is available
        paginator = PaginationManager(max_reviews=max_reviews, max_pages=None)
        if asin:
            async with httpx.AsyncClient(timeout=15.0, headers=cls.HEADERS, follow_redirects=True) as client:
                while paginator.should_continue():
                    page = paginator.current_page
                    rev_url = f"https://{host}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_{page}?pageNumber={page}&sortBy=recent"
                    try:
                        resp = await client.get(rev_url)
                        if resp.status_code != 200 or "Robot Check" in resp.text:
                            break
                        page_soup = BeautifulSoup(resp.text, "lxml")
                        page_reviews = cls._parse_reviews_from_soup(page_soup)
                        if not page_reviews:
                            paginator.record_page_results(0, has_more=False)
                            break
                        known = {r.review_id for r in reviews if r.review_id}
                        fresh = [r for r in page_reviews if r.review_id not in known]
                        if not fresh:
                            paginator.record_page_results(0, has_more=False)
                            break
                        remaining = (max_reviews - len(reviews)) if max_reviews is not None else len(fresh)
                        selected = fresh[:remaining]
                        reviews.extend(selected)
                        has_next = bool(page_soup.select("li.a-last:not(.a-disabled) a")) or len(page_reviews) >= 8
                        paginator.record_page_results(len(selected), has_more=has_next)
                        await asyncio.sleep(0.3)
                    except Exception as p_err:
                        log_ecom("Amazon paginated reviews HTTP step warning", level="WARN", details=str(p_err))
                        break

        # 3. Use managed public browser to capture dynamically rendered reviews
        review_url = f"https://{host}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_1?pageNumber=1&sortBy=recent" if asin else None
        browser_reviews, collection_stats = await collect_public_reviews(
            canonical_url, "amazon", initial_reviews=reviews, max_reviews=max_reviews,
            progress_callback=progress_callback, review_page_url=review_url
        )
        reviews = browser_reviews
        unique_reviews, dup_count = DataValidator.deduplicate_reviews(reviews)
        collection_stats["unique_reviews"] = len(unique_reviews)
        collection_stats["duplicates_found"] = collection_stats.get("duplicates_found", dup_count)

        return unique_reviews, collection_stats

    @classmethod
    async def extract_product_and_reviews(
        cls,
        url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[Optional[ProductInfo], List[CustomerReview], str]:
        log_ecom("E-commerce extraction started", details=f"URL: {url}")
        log_ecom("Platform detected: Amazon")

        valid, canonical_url, err_msg = cls.resolve_product_url(url)
        if not valid:
            log_ecom(f"Amazon URL rejected: {err_msg}", level="ERROR")
            return None, [], f"Security filter rejected URL: {err_msg}"

        if progress_callback:
            await progress_callback(15, "Connecting to Amazon product listing...")

        product, html_text = await cls.extract_product_details(canonical_url)
        if not product:
            log_zero_reviews_reason("Product page inaccessible or anti-bot challenge active", "amazon", canonical_url)
            return None, [], "Could not extract valid product details from Amazon page."

        log_ecom("Product page loaded")
        log_ecom(f"Product details extracted: {product.product_name[:50]} (Price: {product.currency} {product.current_price or 'N/A'})")

        if progress_callback:
            await progress_callback(40, f"Extracted product: {product.product_name[:40]}... (Price: {product.currency} {product.current_price or 'N/A'})")

        soup = BeautifulSoup(html_text or "", "lxml")
        log_ecom("Review section detected")

        unique_reviews, collection_stats = await cls.extract_reviews(
            canonical_url, max_reviews=max_reviews, progress_callback=progress_callback, initial_soup=soup
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
            msg = f"Extracted product details and {len(unique_reviews)} customer reviews from Amazon."
        elif collection_stats.get("stop_reason") == "anti_bot_challenge_detected":
            msg = "Product details extracted, but review extraction was halted by Amazon anti-bot security challenge ('Robot Check'). Authenticated login or manual file upload required."
            log_zero_reviews_reason("Amazon anti-bot Robot Check", "amazon", canonical_url)
        elif reported_count == 0:
            msg = "Product details extracted successfully. No customer reviews have been published for this item on Amazon."
            log_zero_reviews_reason("No public reviews published on Amazon", "amazon", canonical_url)
        else:
            msg = collection_stats.get("failure_reason") or "Extracted product details from Amazon, but customer reviews could not be retrieved from public session."
            log_zero_reviews_reason(msg, "amazon", canonical_url)

        return product, unique_reviews, msg

