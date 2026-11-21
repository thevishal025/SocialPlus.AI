from backend.universal_scraper.engine import UniversalScraperEngine
from backend.universal_scraper.structured_data import StructuredDataExtractor
from backend.universal_scraper.social_scraper import UniversalInstagramScraper, UniversalFacebookScraper
from backend.universal_scraper.ecommerce_adapters import UniversalEcommerceEngine

__all__ = [
    "UniversalScraperEngine",
    "StructuredDataExtractor",
    "UniversalInstagramScraper",
    "UniversalFacebookScraper",
    "UniversalEcommerceEngine",
]
