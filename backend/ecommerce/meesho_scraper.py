"""SocialPlus.ai — Meesho Scraper Module.

Drop-in compatibility layer delegating to the unified MeeshoAdapter while preserving
all legacy class methods, signatures, and interfaces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from backend.ecommerce.meesho_adapter import MeeshoAdapter
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.review_collection import collect_public_reviews


class MeeshoScraper(MeeshoAdapter):
    """Meesho Scraper conforming to both legacy MeeshoScraper and unified BaseEcommerceAdapter."""

    @classmethod
    async def _extract_meesho_reviews(
        cls,
        soup: BeautifulSoup,
        product_id: Optional[str],
        max_reviews: Optional[int] = None,
        progress_callback=None,
        product_url: Optional[str] = None
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        reviews, stats = await cls.extract_reviews(
            product_url=product_url or "",
            max_reviews=max_reviews,
            progress_callback=progress_callback,
            initial_soup=soup
        )
        return reviews, stats
