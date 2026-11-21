"""SocialPlus.ai — AJIO Scraper Module.

Drop-in compatibility layer delegating to the unified AjioAdapter while preserving
all legacy class methods, signatures, and interfaces.
"""
from __future__ import annotations

from backend.ecommerce.ajio_adapter import AjioAdapter


class AjioScraper(AjioAdapter):
    """AJIO Scraper conforming to both legacy AjioScraper and unified BaseEcommerceAdapter."""
    pass
