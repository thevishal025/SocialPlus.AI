import time
import uuid
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import EngineType, EngineStatus, DataStatus
from backend.extraction.engines.base_engine import BaseEngine
from backend.utils.security import is_safe_url, resolve_safe_redirects


class BeautifulSoupEngine(BaseEngine):
    """
    Engine 4: BeautifulSoup + lxml parser.
    Specializes in:
    - HTML parsing of retrieved markup.
    - Extracting review containers, titles, authors, ratings, and body text.
    - Cleaning HTML and extracting structured product metadata.
    """
    engine_type = EngineType.BEAUTIFUL_SOUP
    display_name = "BeautifulSoup 4"

    def is_available(self) -> bool:
        try:
            import bs4
            return True
        except ImportError:
            return False

    async def extract(
        self,
        url: str,
        platform: str,
        max_records: int = 100,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[NormalizedComment], Dict[str, Any], EngineStatus, DataStatus, str]:
        start_time = time.time()
        self.state.status = EngineStatus.RUNNING
        self.state.last_operation = "Validating target URL and resolving redirects"

        # Check if pre-fetched HTML was provided in context
        html_content = context.get("html") if context else None
        final_url = url
        metadata: Dict[str, Any] = {"engine": "beautifulsoup", "platform": platform}
        comments: List[NormalizedComment] = []

        if not html_content:
            # Safely resolve redirects first
            safe, resolved_url, err_msg, chain = resolve_safe_redirects(url)
            if not safe:
                duration = time.time() - start_time
                self.state.status = EngineStatus.FAILED
                self.state.execution_time_sec = round(duration, 2)
                self.state.failure_reason = f"Security block / redirect error: {err_msg}"
                self.state.last_operation = "URL validation failed"
                return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, err_msg

            final_url = resolved_url
            self.state.last_operation = f"Fetching page HTML from {final_url[:60]}..."

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                    resp = await client.get(final_url)
                    if resp.status_code == 200:
                        html_content = resp.text
                        self.state.data_status = DataStatus.PAGE_LOADED
                    elif resp.status_code == 403:
                        duration = time.time() - start_time
                        self.state.status = EngineStatus.FAILED
                        self.state.execution_time_sec = round(duration, 2)
                        self.state.failure_reason = "HTTP 403 Forbidden (Anti-bot / login wall active)"
                        self.state.last_operation = "Access denied by server"
                        return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "403 Forbidden"
                    else:
                        duration = time.time() - start_time
                        self.state.status = EngineStatus.FAILED
                        self.state.execution_time_sec = round(duration, 2)
                        self.state.failure_reason = f"HTTP status {resp.status_code}"
                        self.state.last_operation = f"Received status {resp.status_code}"
                        return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, f"HTTP {resp.status_code}"
            except Exception as exc:
                duration = time.time() - start_time
                self.state.status = EngineStatus.FAILED
                self.state.execution_time_sec = round(duration, 2)
                self.state.failure_reason = f"Network request error: {str(exc)}"
                self.state.last_operation = "Failed to connect to host"
                return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, str(exc)

        # Parse HTML with BeautifulSoup + lxml
        self.state.last_operation = "Parsing HTML DOM structure with lxml..."
        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception:
            soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract Product Metadata
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            metadata["title"] = title_tag.text.strip()

        # Flipkart / Amazon specific title / rating selectors
        h1_tag = soup.find("h1") or soup.select_one("span.B_NuCI, span#productTitle, span.VU-ZEz")
        if h1_tag:
            metadata["product_name"] = h1_tag.text.strip()
            self.state.data_status = DataStatus.METADATA_EXTRACTED

        # 2. Extract Reviews based on common review selectors
        self.state.last_operation = "Searching review containers in DOM..."
        
        # Selectors for various platforms (Flipkart, Amazon, Generic)
        review_selectors = [
            "div._16PBlm", "div._27M-vq", "div.col._2wzgFH", "div.cPHDOP", # Flipkart
            "div[data-hook='review']", "div.review",                         # Amazon
            "div.review-card", "div.feedback-item", "div.user-review",       # Generic
            "div.customer-review", "div.comment-thread"
        ]

        found_cards = []
        for sel in review_selectors:
            elements = soup.select(sel)
            if elements:
                found_cards = elements
                break

        for card in found_cards[:max_records]:
            # Extract text
            text_el = card.select_one("div.t-ZTKy, div._6K-7Co, span[data-hook='review-body'], p.review-text, div.content")
            title_el = card.select_one("p._2-N8zT, a[data-hook='review-title'], h5.review-title")
            author_el = card.select_one("p._2sc7ZR, span.a-profile-name, span.author")
            rating_el = card.select_one("div._3LWZlK, i[data-hook='review-star-rating'], span.rating")

            body_text = text_el.get_text(separator=" ").strip() if text_el else ""
            if not body_text and card.text:
                # Fallback to card text if short enough
                body_text = card.get_text(separator=" ").strip()

            if body_text and len(body_text) > 5:
                rating_val = None
                if rating_el:
                    import re
                    m = re.search(r"(\d+(\.\d+)?)", rating_el.get_text())
                    if m:
                        try:
                            rating_val = float(m.group(1))
                        except Exception:
                            pass

                full_text = f"{title_el.get_text().strip()}: {body_text}" if title_el else body_text
                comments.append(NormalizedComment(
                    id=str(uuid.uuid4()),
                    platform=platform,
                    source="beautifulsoup",
                    author=author_el.get_text().strip() if author_el else "Customer Reviewer",
                    text=full_text,
                    rating=rating_val,
                    likes=0,
                    product=metadata.get("product_name") or metadata.get("title") or "Product"
                ))

        duration = time.time() - start_time
        self.state.execution_time_sec = round(duration, 2)
        self.state.records_extracted = len(comments)

        if comments:
            self.state.status = EngineStatus.SUCCESS
            self.state.data_status = DataStatus.REVIEWS_FOUND
            self.state.last_operation = f"Successfully extracted {len(comments)} reviews via BeautifulSoup"
            return comments, metadata, EngineStatus.SUCCESS, DataStatus.REVIEWS_FOUND, f"Extracted {len(comments)} reviews"
        elif metadata.get("product_name") or metadata.get("title"):
            self.state.status = EngineStatus.PARTIAL
            self.state.data_status = DataStatus.METADATA_EXTRACTED
            self.state.last_operation = "Page metadata extracted, but comments container is empty or dynamically rendered"
            self.state.failure_reason = "No reviews found in static HTML (page may require JS execution)"
            return [], metadata, EngineStatus.PARTIAL, DataStatus.METADATA_EXTRACTED, "Only metadata found in HTML"
        else:
            self.state.status = EngineStatus.FAILED
            self.state.data_status = DataStatus.PAGE_LOADED
            self.state.last_operation = "No structured review content detected"
            self.state.failure_reason = "Static HTML lacked recognized comment/review nodes"
            return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "No reviews detected"

