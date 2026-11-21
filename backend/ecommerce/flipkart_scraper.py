"""SocialPlus.ai — Flipkart Scraper Module.

Drop-in compatibility layer delegating to the unified FlipkartAdapter while preserving
all legacy class methods, signatures, and interfaces.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from backend.ecommerce.flipkart_adapter import FlipkartAdapter
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview


class FlipkartScraper(FlipkartAdapter):
    """Flipkart Scraper conforming to both legacy FlipkartScraper and unified BaseEcommerceAdapter."""

    @classmethod
    async def _extract_paginated_reviews(
        cls,
        slug: Optional[str],
        item_id: Optional[str],
        pid: Optional[str],
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> List[CustomerReview]:
        base_slug = slug or "product"
        product_url = f"https://www.flipkart.com/{base_slug}/p/{item_id or ''}?pid={pid or ''}"
        reviews, _ = await cls.extract_reviews(product_url, max_reviews=max_reviews, progress_callback=progress_callback)
        return reviews
