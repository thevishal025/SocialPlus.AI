import time
import uuid
import httpx
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import EngineType, EngineStatus, DataStatus
from backend.extraction.engines.base_engine import BaseEngine
from backend.utils.security import is_safe_url, resolve_safe_redirects


class ScrapyEngine(BaseEngine):
    """
    Engine 3: Scrapy Crawling & Pagination Engine.
    Specializes in:
    - Structured crawling of multi-page review listings.
    - Handling permitted pagination links (e.g. page=1, page=2, /reviews?page=...).
    - High-throughput item pipeline and extraction.
    """
    engine_type = EngineType.SCRAPY
    display_name = "Scrapy Spider"

    def is_available(self) -> bool:
        try:
            import scrapy
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
        self.state.last_operation = "Initializing Scrapy spider extraction context"

        # Validate target URL
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            duration = time.time() - start_time
            self.state.status = EngineStatus.FAILED
            self.state.execution_time_sec = round(duration, 2)
            self.state.failure_reason = f"Security filter error: {err_msg}"
            self.state.last_operation = "URL validation failed"
            return [], {}, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, err_msg

        comments: List[NormalizedComment] = []
        metadata: Dict[str, Any] = {"engine": "scrapy", "platform": platform}
        pages_visited = 0

        # Try to use Scrapy's Selector if scrapy is available, else fallback to parsel/lxml
        has_scrapy = self.is_available()
        self.state.last_operation = "Starting structured crawler request loop..."

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        current_url = resolved_url
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            # Crawl up to 3 pages if pagination is accessible
            while len(comments) < max_records and pages_visited < 3 and current_url:
                pages_visited += 1
                self.state.last_operation = f"Crawling page {pages_visited}: {current_url[:50]}..."

                try:
                    resp = await client.get(current_url)
                except Exception as req_err:
                    break

                if resp.status_code != 200:
                    break

                html_body = resp.text
                self.state.data_status = DataStatus.PAGE_LOADED

                # Parse using Scrapy Selector if available, or BeautifulSoup/lxml
                if has_scrapy:
                    from scrapy.selector import Selector
                    sel = Selector(text=html_body)
                    
                    # Extract title
                    title = sel.xpath("//title/text()").get()
                    if title and not metadata.get("title"):
                        metadata["title"] = title.strip()
                        self.state.data_status = DataStatus.METADATA_EXTRACTED

                    # Extract review nodes
                    review_nodes = sel.xpath(
                        "//div[contains(@class, '_16PBlm') or contains(@class, '_27M-vq') or contains(@class, 'review') or contains(@class, 'user-review')]"
                    )
                    
                    for r_node in review_nodes:
                        if len(comments) >= max_records:
                            break
                        
                        text = r_node.xpath(".//div[contains(@class, 't-ZTKy')]//text() | .//span[@data-hook='review-body']//text() | .//p[contains(@class, 'review-text')]//text()").getall()
                        full_text = " ".join([t.strip() for t in text if t.strip()])
                        author = r_node.xpath(".//p[contains(@class, '_2sc7ZR')]//text() | .//span[contains(@class, 'a-profile-name')]//text()").get()
                        rating_str = r_node.xpath(".//div[contains(@class, '_3LWZlK')]//text() | .//i[contains(@data-hook, 'review-star-rating')]//text()").get()

                        if full_text and len(full_text) > 5:
                            rating_val = None
                            if rating_str:
                                import re
                                m = re.search(r"(\d+(\.\d+)?)", rating_str)
                                if m:
                                    try:
                                        rating_val = float(m.group(1))
                                    except Exception:
                                        pass

                            comments.append(NormalizedComment(
                                id=str(uuid.uuid4()),
                                platform=platform,
                                source="scrapy",
                                author=author.strip() if author else "Customer Reviewer",
                                text=full_text,
                                rating=rating_val,
                                likes=0,
                                product=metadata.get("title", "Product")
                            ))

                    # Look for next pagination link
                    next_href = sel.xpath("//a[contains(@class, '_1LKTO3') or contains(text(), 'Next') or @rel='next']/@href").get()
                    if next_href and next_href.startswith("/"):
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, next_href)
                    else:
                        current_url = None
                else:
                    # Fallback to BeautifulSoup if scrapy is not yet loaded
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_body, "lxml")
                    cards = soup.select("div._16PBlm, div._27M-vq, div[data-hook='review'], div.review-card")
                    for card in cards:
                        if len(comments) >= max_records:
                            break
                        text_el = card.select_one("div.t-ZTKy, div._6K-7Co, span[data-hook='review-body'], p.review-text")
                        body = text_el.get_text(separator=" ").strip() if text_el else ""
                        if body and len(body) > 5:
                            comments.append(NormalizedComment(
                                id=str(uuid.uuid4()),
                                platform=platform,
                                source="scrapy",
                                author="Customer Reviewer",
                                text=body,
                                rating=None,
                                likes=0,
                                product=metadata.get("title", "Product")
                            ))
                    current_url = None

        duration = time.time() - start_time
        self.state.execution_time_sec = round(duration, 2)
        self.state.records_extracted = len(comments)

        if comments:
            self.state.status = EngineStatus.SUCCESS
            self.state.data_status = DataStatus.REVIEWS_FOUND
            self.state.last_operation = f"Scrapy spider crawled {pages_visited} pages and retrieved {len(comments)} reviews"
            return comments, metadata, EngineStatus.SUCCESS, DataStatus.REVIEWS_FOUND, f"Scrapy retrieved {len(comments)} reviews across {pages_visited} pages"
        elif metadata.get("title"):
            self.state.status = EngineStatus.PARTIAL
            self.state.data_status = DataStatus.METADATA_EXTRACTED
            self.state.last_operation = f"Crawled {pages_visited} pages — metadata parsed, no review nodes discovered"
            self.state.failure_reason = "No reviews found across crawled pages"
            return [], metadata, EngineStatus.PARTIAL, DataStatus.METADATA_EXTRACTED, "Only metadata found"
        else:
            self.state.status = EngineStatus.FAILED
            self.state.data_status = DataStatus.PAGE_LOADED
            self.state.last_operation = "Scrapy spider found no indexable content"
            self.state.failure_reason = "Page inaccessible or anti-bot challenge encountered"
            return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "No content extracted"

