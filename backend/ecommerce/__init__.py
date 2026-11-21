from backend.ecommerce.platform_detector import PlatformDetector, PLATFORM_METADATA
from backend.ecommerce.browser_manager import BrowserManager
from backend.ecommerce.product_extractor import ProductInfo, SpecificationParser
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.pagination_manager import PaginationManager
from backend.ecommerce.data_normalizer import DataNormalizer
from backend.ecommerce.data_validator import DataValidator
from backend.ecommerce.base_adapter import BaseEcommerceAdapter
from backend.ecommerce.amazon_adapter import AmazonAdapter
from backend.ecommerce.flipkart_adapter import FlipkartAdapter
from backend.ecommerce.meesho_adapter import MeeshoAdapter
from backend.ecommerce.ajio_adapter import AjioAdapter
from backend.ecommerce.myntra_adapter import MyntraAdapter
from backend.ecommerce.amazon_scraper import AmazonScraper
from backend.ecommerce.flipkart_scraper import FlipkartScraper
from backend.ecommerce.meesho_scraper import MeeshoScraper
from backend.ecommerce.ajio_scraper import AjioScraper
from backend.ecommerce.myntra_scraper import MyntraScraper
from backend.ecommerce.ecommerce_router import router as ecommerce_router

__all__ = [
    "PlatformDetector",
    "PLATFORM_METADATA",
    "BrowserManager",
    "ProductInfo",
    "SpecificationParser",
    "CustomerReview",
    "PaginationManager",
    "DataNormalizer",
    "DataValidator",
    "BaseEcommerceAdapter",
    "AmazonAdapter",
    "FlipkartAdapter",
    "MeeshoAdapter",
    "AjioAdapter",
    "MyntraAdapter",
    "AmazonScraper",
    "FlipkartScraper",
    "MeeshoScraper",
    "AjioScraper",
    "MyntraScraper",
    "ecommerce_router"
]
