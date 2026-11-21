import re
import uuid
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from backend.connectors.base_connector import BaseConnector, ConnectorResult
from backend.schemas.api_schemas import NormalizedComment
from backend.utils.security import is_safe_url


class BaseEcommerceAdapter:
    """Base class for platform-specific e-commerce adapters."""
    platform_key: str
    display_name: str
    status: str  # Supported, Limited Support, Upload Required, Temporarily Unavailable
    base_url: str

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })

    def validate_url(self, url: str) -> bool:
        try:
            hostname = (urlparse(url).hostname or "").lower().rstrip(".")
        except ValueError:
            return False
        return hostname == self.base_url or hostname.endswith("." + self.base_url)

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search products on platform (where permitted)."""
        return []

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        """Fetch reviews for a product."""
        raise NotImplementedError


class AmazonIndiaAdapter(BaseEcommerceAdapter):
    platform_key = "amazon_in"
    display_name = "Amazon India"
    status = "Limited Support"
    base_url = "amazon.in"

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        # Return structured search target
        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        return [{
            "id": "amz-search-1",
            "title": f"Amazon India: '{clean_q}'",
            "platform": "Amazon India",
            "platform_key": "amazon_in",
            "url": f"https://www.amazon.in/s?k={requests.utils.quote(clean_q)}",
            "status": "Limited Support",
            "note": "Amazon blocks automated review harvesting via bot-detection. Use 'Upload File' mode for complete CSV/Excel review datasets."
        }]

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        is_url = identifier.startswith("http://") or identifier.startswith("https://")
        if is_url:
            safe, err = is_safe_url(identifier)
            if not safe:
                return ConnectorResult(
                    success=False, platform="amazon_in", retrieval_method="online",
                    status_code="security_blocked", message=f"URL rejected by security filter: {err}"
                )

        # Amazon enforces strict CAPTCHA gates on automated HTTP requests
        return ConnectorResult(
            success=False,
            platform="amazon_in",
            retrieval_method="online",
            status_code="unsupported",
            message=(
                "Amazon India utilizes strict anti-bot and CAPTCHA gates preventing direct automated review extraction. "
                "Per system guidelines, automated CAPTCHA bypass is disabled. "
                "Please use 'Upload File' mode to upload your exported Amazon reviews dataset (CSV or Excel)."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            limitations="Amazon blocks unauthenticated third-party scrapers via CAPTCHA challenges."
        )


class FlipkartAdapter(BaseEcommerceAdapter):
    platform_key = "flipkart"
    display_name = "Flipkart"
    status = "Limited Support"
    base_url = "flipkart.com"

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        return [{
            "id": "fk-search-1",
            "title": f"Flipkart: '{clean_q}'",
            "platform": "Flipkart",
            "platform_key": "flipkart",
            "url": f"https://www.flipkart.com/search?q={requests.utils.quote(clean_q)}",
            "status": "Limited Support",
            "note": "Public review extraction is rate-limited. Switch to 'Upload File' mode for large datasets."
        }]

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        is_url = identifier.startswith("http://") or identifier.startswith("https://")
        if is_url:
            safe, err = is_safe_url(identifier)
            if not safe:
                return ConnectorResult(
                    success=False, platform="flipkart", retrieval_method="online",
                    status_code="security_blocked", message=f"URL rejected by security filter: {err}"
                )

        comments: List[NormalizedComment] = []
        # Attempt public review page extraction if URL provided
        if is_url and "flipkart.com" in identifier:
            try:
                res = self.session.get(identifier, timeout=10)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    # Locate review blocks
                    review_cards = soup.select("div._16PBlm, div._27M-vq, div.col._2wzgFH")
                    for card in review_cards[:max_reviews]:
                        text_elem = card.select_one("div.t-ZTKy, div._6K-7Co")
                        title_elem = card.select_one("p._2-N8zT")
                        author_elem = card.select_one("p._2sc7ZR")
                        rating_elem = card.select_one("div._3LWZlK")
                        
                        review_text = text_elem.get_text(separator=" ").strip() if text_elem else ""
                        if review_text:
                            rating_val = None
                            if rating_elem:
                                try:
                                    rating_val = float(rating_elem.get_text().strip())
                                except Exception:
                                    pass
                            
                            comments.append(NormalizedComment(
                                id=str(uuid.uuid4()),
                                platform="flipkart",
                                source="online",
                                author=author_elem.get_text().strip() if author_elem else "Flipkart Customer",
                                text=f"{title_elem.get_text().strip() + ': ' if title_elem else ''}{review_text}",
                                rating=rating_val,
                                likes=0,
                                product="Flipkart Product"
                            ))

                    if comments:
                        return ConnectorResult(
                            success=True,
                            platform="flipkart",
                            retrieval_method="online",
                            status_code="success",
                            message=f"Successfully extracted {len(comments)} public reviews from Flipkart product page.",
                            comments=comments,
                            total_found=len(comments),
                            retrieved_count=len(comments)
                        )
            except Exception as e:
                pass

        return ConnectorResult(
            success=False,
            platform="flipkart",
            retrieval_method="online",
            status_code="unsupported",
            message=(
                "Could not extract public Flipkart reviews directly due to dynamic client-side rendering or access limits. "
                "Please use 'Upload File' mode to upload your Flipkart reviews file (CSV, Excel, or JSON)."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            limitations="Flipkart pages render review blocks dynamically via React hydration."
        )


class MyntraAdapter(BaseEcommerceAdapter):
    platform_key = "myntra"
    display_name = "Myntra"
    status = "Upload Required"
    base_url = "myntra.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="myntra",
            retrieval_method="online",
            status_code="unsupported",
            message=(
                "Myntra's Terms of Use prohibit automated page scraping and reviews are served exclusively through mobile-app APIs. "
                "Please use 'Upload File' mode to analyze Myntra reviews (CSV or Excel)."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            limitations="Scraping prohibited by Myntra terms of service."
        )


class MeeshoAdapter(BaseEcommerceAdapter):
    platform_key = "meesho"
    display_name = "Meesho"
    status = "Upload Required"
    base_url = "meesho.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="meesho",
            retrieval_method="online",
            status_code="unsupported",
            message=(
                "Meesho reviews are fetched via internal GraphQL app endpoints requiring encrypted mobile session tokens. "
                "Please use 'Upload File' mode to analyze Meesho customer feedback datasets."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            limitations="Meesho requires mobile token authentication."
        )


class AjioAdapter(BaseEcommerceAdapter):
    platform_key = "ajio"
    display_name = "Ajio"
    status = "Upload Required"
    base_url = "ajio.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="ajio",
            retrieval_method="online",
            status_code="unsupported",
            message=(
                "Ajio review streams are protected by Akamai bot-manager. "
                "Please use 'Upload File' mode to upload your Ajio review export."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            limitations="Akamai bot challenge protects Ajio catalog endpoints."
        )


class SnapdealAdapter(BaseEcommerceAdapter):
    platform_key = "snapdeal"
    display_name = "Snapdeal"
    status = "Limited Support"
    base_url = "snapdeal.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        is_url = identifier.startswith("http://") or identifier.startswith("https://")
        if is_url:
            safe, err = is_safe_url(identifier)
            if not safe:
                return ConnectorResult(
                    success=False, platform="snapdeal", retrieval_method="online",
                    status_code="security_blocked", message=f"URL rejected by security filter: {err}"
                )
            try:
                res = self.session.get(identifier, timeout=10)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    comment_wrappers = soup.select(".user-review, .feedback-item")
                    comments = []
                    for cw in comment_wrappers[:max_reviews]:
                        text_elem = cw.select_one(".user-review-text, p")
                        if text_elem:
                            text = text_elem.get_text().strip()
                            if text:
                                comments.append(NormalizedComment(
                                    id=str(uuid.uuid4()),
                                    platform="snapdeal",
                                    source="online",
                                    author="Snapdeal Customer",
                                    text=text,
                                    rating=None,
                                    product="Snapdeal Product"
                                ))
                    if comments:
                        return ConnectorResult(
                            success=True,
                            platform="snapdeal",
                            retrieval_method="online",
                            status_code="success",
                            message=f"Extracted {len(comments)} reviews from Snapdeal product page.",
                            comments=comments,
                            total_found=len(comments),
                            retrieved_count=len(comments)
                        )
            except Exception:
                pass

        return ConnectorResult(
            success=False,
            platform="snapdeal",
            retrieval_method="online",
            status_code="unsupported",
            message="No public reviews could be extracted from this Snapdeal URL. Use 'Upload File' mode for guaranteed analysis.",
            comments=[],
            total_found=0,
            retrieved_count=0
        )


class TataCliqAdapter(BaseEcommerceAdapter):
    platform_key = "tatacliq"
    display_name = "Tata CLiQ"
    status = "Upload Required"
    base_url = "tatacliq.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="tatacliq",
            retrieval_method="online",
            status_code="unsupported",
            message="Tata CLiQ does not provide an open public review API. Use 'Upload File' mode to analyze reviews.",
            comments=[],
            total_found=0,
            retrieved_count=0
        )


class NykaaAdapter(BaseEcommerceAdapter):
    platform_key = "nykaa"
    display_name = "Nykaa"
    status = "Upload Required"
    base_url = "nykaa.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="nykaa",
            retrieval_method="online",
            status_code="unsupported",
            message="Nykaa customer reviews require app-signed token access. Use 'Upload File' mode to analyze Nykaa review exports.",
            comments=[],
            total_found=0,
            retrieved_count=0
        )


class JioMartAdapter(BaseEcommerceAdapter):
    platform_key = "jiomart"
    display_name = "JioMart"
    status = "Upload Required"
    base_url = "jiomart.com"

    def fetch_reviews(self, identifier: str, max_reviews: int = 100) -> ConnectorResult:
        return ConnectorResult(
            success=False,
            platform="jiomart",
            retrieval_method="online",
            status_code="unsupported",
            message="JioMart does not permit automated web review scraping. Use 'Upload File' mode to analyze your customer feedback datasets.",
            comments=[],
            total_found=0,
            retrieved_count=0
        )


class EcommerceConnector(BaseConnector):
    """Unified E-commerce Connector Registry managing all 9 platforms."""

    ADAPTERS = {
        "amazon_in": AmazonIndiaAdapter,
        "flipkart": FlipkartAdapter,
        "myntra": MyntraAdapter,
        "meesho": MeeshoAdapter,
        "ajio": AjioAdapter,
        "snapdeal": SnapdealAdapter,
        "tatacliq": TataCliqAdapter,
        "nykaa": NykaaAdapter,
        "jiomart": JioMartAdapter,
    }

    def __init__(self):
        super().__init__(platform="ecommerce", retrieval_method="online")
        self._instances: Dict[str, BaseEcommerceAdapter] = {
            k: cls() for k, cls in self.ADAPTERS.items()
        }

    def get_supported_platforms(self) -> List[Dict[str, str]]:
        return [
            {
                "key": k,
                "name": adapter.display_name,
                "status": adapter.status
            }
            for k, adapter in self._instances.items()
        ]

    def validate_identifier(self, identifier: str) -> bool:
        return bool(identifier and len(identifier.strip()) > 1)

    def search_products(self, platform_key: str, query: str) -> List[Dict[str, Any]]:
        adapter = self._instances.get(platform_key)
        if not adapter:
            return []
        return adapter.search_products(query)

    def detect_platform_from_url(self, url: str) -> Optional[str]:
        """Auto-detect e-commerce platform from a URL string."""
        try:
            hostname = (urlparse(url).hostname or "").lower().rstrip(".")
        except ValueError:
            return None
        domain_map = {
            "amazon.in": "amazon_in",
            "flipkart.com": "flipkart",
            "myntra.com": "myntra",
            "meesho.com": "meesho",
            "ajio.com": "ajio",
            "snapdeal.com": "snapdeal",
            "tatacliq.com": "tatacliq",
            "nykaa.com": "nykaa",
            "jiomart.com": "jiomart",
        }
        for domain, key in domain_map.items():
            if hostname == domain or hostname.endswith("." + domain):
                return key
        return None

    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 100,
        platform_key: Optional[str] = None,
        **kwargs
    ) -> ConnectorResult:
        # Detect platform from URL if not explicitly provided
        if not platform_key:
            for k, adapter in self._instances.items():
                if adapter.validate_url(identifier):
                    platform_key = k
                    break
        
        platform_key = platform_key or "amazon_in"
        adapter = self._instances.get(platform_key)
        if not adapter:
            return ConnectorResult(
                success=False,
                platform=platform_key,
                retrieval_method="online",
                status_code="unsupported_platform",
                message=f"Unsupported e-commerce platform: '{platform_key}'."
            )

        return adapter.fetch_reviews(identifier, max_reviews=max_comments)
