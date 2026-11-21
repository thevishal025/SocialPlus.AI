"""SocialPlus.ai — Myntra Scraper Module.

Drop-in compatibility layer delegating to the unified MyntraAdapter while preserving
all legacy class methods, signatures, and interfaces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from backend.ecommerce.myntra_adapter import MyntraAdapter
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.review_collection import collect_public_reviews


class MyntraScraper(MyntraAdapter):
    """Myntra Scraper conforming to both legacy MyntraScraper and unified BaseEcommerceAdapter."""

    @classmethod
    async def _extract_myntra_reviews(
        cls,
        soup: BeautifulSoup,
        product_url: str,
        style_id: Optional[str] = None,
        max_reviews: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        reviews, stats = await cls.extract_reviews(
            product_url=product_url,
            max_reviews=max_reviews,
            progress_callback=progress_callback,
            initial_soup=soup
        )
        return reviews, stats
