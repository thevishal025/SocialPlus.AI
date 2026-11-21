"""SocialPlus.ai — Amazon Scraper Module.

Drop-in compatibility layer delegating to the unified AmazonAdapter while preserving
all legacy class methods, signatures, and interfaces.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from backend.ecommerce.amazon_adapter import AmazonAdapter
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview


class AmazonScraper(AmazonAdapter):
    """Amazon Scraper conforming to both legacy AmazonScraper and unified BaseEcommerceAdapter."""

    @classmethod
    async def _extract_paginated_reviews(
        cls,
        asin: str,
        max_reviews: Optional[int] = None,
        progress_callback=None,
        marketplace_host: str = "www.amazon.in"
    ) -> List[CustomerReview]:
        product_url = f"https://{marketplace_host}/dp/{asin}"
        reviews, _ = await cls.extract_reviews(product_url, max_reviews=max_reviews, progress_callback=progress_callback)
        return reviews
