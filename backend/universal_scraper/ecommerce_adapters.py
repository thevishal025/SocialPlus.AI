import asyncio
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.amazon_scraper import AmazonScraper
from backend.ecommerce.flipkart_scraper import FlipkartScraper
from backend.ecommerce.meesho_scraper import MeeshoScraper
from backend.ecommerce.ajio_scraper import AjioScraper
from backend.ecommerce.myntra_scraper import MyntraScraper
from backend.universal_scraper.engine import UniversalScraperEngine


class UniversalEcommerceEngine:
    """
    Universal Scraper Engine Adapter for E-Commerce Platforms.
    Unified interface for Amazon India, Flipkart, Meesho, AJIO, and Myntra.
    Supports complete Product Intelligence extraction conforming to the master specification:
    - Product Overview
    - Product Description
    - Technical Specifications
    - Product Variants
    - Customer Reviews
    - Extraction Information
    """

    SUPPORTED_PLATFORMS = {
        "amazon": AmazonScraper,
        "flipkart": FlipkartScraper,
        "meesho": MeeshoScraper,
        "ajio": AjioScraper,
        "myntra": MyntraScraper
    }

    @classmethod
    async def extract_product_and_reviews(
        cls,
        url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes unified deep extraction for any supported e-commerce product URL.
        """
        p_key, display_name = UniversalScraperEngine.detect_platform(url)

        if p_key not in cls.SUPPORTED_PLATFORMS:
            return {
                "success": False,
                "status": "unsupported_platform",
                "platform": p_key,
                "platform_display": display_name,
                "product": None,
                "reviews": [],
                "message": f"Platform '{display_name}' is not currently supported for deep e-commerce intelligence."
            }

        scraper_cls = cls.SUPPORTED_PLATFORMS[p_key]
        product: Optional[ProductInfo] = None
        reviews: List[CustomerReview] = []
        msg: str = ""

        try:
            product, reviews, msg = await scraper_cls.extract_product_and_reviews(
                url,
                max_reviews=max_reviews,
                progress_callback=progress_callback
            )
        except Exception as exc:
            return {
                "success": False,
                "status": "extraction_error",
                "platform": p_key,
                "platform_display": display_name,
                "product": None,
                "reviews": [],
                "message": f"Universal Scraper error on {display_name}: {str(exc)}"
            }

        if not product:
            fail_status = "access_restricted" if ("restricted" in msg.lower() or "anti-bot" in msg.lower()) else "product_not_found"
            return {
                "success": False,
                "status": fail_status,
                "platform": p_key,
                "platform_display": display_name,
                "product": None,
                "reviews": [],
                "message": msg or f"Could not extract product details from {display_name}."
            }

        # Build clean extraction info
        status = "success" if reviews else "partial"
        prior_extraction_info = dict(product.extraction_info or {})
        diagnostics = prior_extraction_info.get("diagnostics") or prior_extraction_info.get("review_collection") or {}
        reported = product.total_reviews_count if product.total_reviews_count is not None else product.review_count
        retrieved = diagnostics.get("retrieved_reviews", len(reviews))

        product.extraction_info = {
            **prior_extraction_info,
            "platform": p_key,
            "platform_display": display_name,
            "source_url": url,
            "extraction_timestamp": product.extraction_timestamp,
            "reported_reviews": reported,
            "retrieved_reviews": retrieved,
            "extracted_reviews": len(reviews),
            "unique_reviews": len(reviews),
            "duplicates_found": diagnostics.get("duplicates_found", 0),
            "diagnostics": diagnostics,
            "stop_reason": diagnostics.get("stop_reason"),
            "failure_reason": diagnostics.get("failure_reason"),
            "platform_limitations": diagnostics.get("platform_limitations"),
            "collection_mode": "all_accessible" if max_reviews is None else "limited",
            "requested_limit": max_reviews,
            "status": status
        }

        return {
            "success": True,
            "status": status,
            "platform": p_key,
            "platform_display": display_name,
            "product": product,
            "reviews": reviews,
            "reported_reviews": reported,
            "retrieved_reviews": retrieved,
            "unique_reviews": len(reviews),
            "diagnostics": diagnostics,
            "message": msg
        }

