"""Base E-Commerce Review Extraction Adapter Interface.

Defines the contract for platform-specific adapters (Amazon, Flipkart, Meesho, AJIO, Myntra)
providing deep metadata extraction, paginated customer review collection, deduplication,
and structured diagnostics.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Sequence, Tuple
from bs4 import BeautifulSoup

from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview


class BaseEcommerceAdapter(abc.ABC):
    """Abstract Base Class for all SocialPlus.ai e-commerce platform adapters."""

    platform_key: str = "generic"
    display_name: str = "Generic Platform"

    @classmethod
    @abc.abstractmethod
    def resolve_product_url(cls, url: str) -> Tuple[bool, str, str]:
        """Validate, resolve short-links/redirects, and canonicalize product URL.

        Returns (is_valid, resolved_url, error_message).
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def extract_product_details(
        cls, url: str, html_content: Optional[str] = None
    ) -> Tuple[Optional[ProductInfo], Optional[str]]:
        """Extract full product metadata, pricing, images, and specifications."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def navigate_to_reviews(cls, product_url: str, **identifiers) -> Optional[str]:
        """Construct the dedicated reviews URL or review section target."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def discover_review_container(cls, soup: BeautifulSoup) -> List[Any]:
        """Find review card elements within parsed page HTML."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def extract_reviews(
        cls,
        product_url: str,
        max_reviews: Optional[int] = None,
        progress_callback=None,
        initial_soup: Optional[BeautifulSoup] = None
    ) -> Tuple[List[CustomerReview], Dict[str, Any]]:
        """Extract customer reviews across all accessible pages."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def extract_next_page(cls, current_page: int, soup: Optional[BeautifulSoup] = None, **kwargs) -> Optional[str]:
        """Find or construct next page pagination link."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def normalize_review(cls, raw_item: Dict[str, Any]) -> Optional[CustomerReview]:
        """Normalize a platform-specific review dictionary or node into CustomerReview."""
        raise NotImplementedError

    @classmethod
    def get_reported_review_count(cls, product: Optional[ProductInfo], soup: Optional[BeautifulSoup] = None) -> Optional[int]:
        """Return the total reviews count reported on the product page."""
        if product:
            if product.total_reviews_count is not None:
                return product.total_reviews_count
            if product.review_count is not None:
                return product.review_count
        return None

    @classmethod
    def get_extraction_status(
        cls,
        product: Optional[ProductInfo],
        reviews: Sequence[CustomerReview],
        diagnostics: Dict[str, Any]
    ) -> str:
        """Evaluate overall extraction status: 'success', 'partial', or 'failure'."""
        if not product:
            return "failure"
        if reviews:
            return "success"
        reported = cls.get_reported_review_count(product)
        if reported == 0:
            return "success"
        return "partial"

