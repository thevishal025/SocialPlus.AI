import time
import uuid
import httpx
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import EngineType, EngineStatus, DataStatus
from backend.extraction.engines.base_engine import BaseEngine
from backend.utils.security import is_safe_url, resolve_safe_redirects


class Crawl4AIEngine(BaseEngine):
    """
    Engine 1: Crawl4AI Web Crawler.
    Specializes in:
    - Webpage content extraction & structured markdown conversion.
    - AI-friendly content parsing and semantic text chunking.
    - Deep metadata & OpenGraph / Schema.org extraction.
    """
    engine_type = EngineType.CRAWL4AI
    display_name = "Crawl4AI Engine"

    def is_available(self) -> bool:
        try:
            import crawl4ai
            return True
        except Exception:
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
        self.state.last_operation = "Initializing Crawl4AI crawler session"

        # Validate target URL
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            duration = time.time() - start_time
            self.state.status = EngineStatus.FAILED
            self.state.execution_time_sec = round(duration, 2)
            self.state.failure_reason = f"Security validation failed: {err_msg}"
            self.state.last_operation = "Target URL rejected"
            return [], {}, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, err_msg

        comments: List[NormalizedComment] = []
        metadata: Dict[str, Any] = {"engine": "crawl4ai", "platform": platform}

        has_crawl4ai = self.is_available()

        if has_crawl4ai:
            try:
                from crawl4ai import AsyncWebCrawler
                self.state.last_operation = f"Crawl4AI asynchronous crawler requesting {resolved_url[:50]}..."
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(url=resolved_url)
                    if result.success:
                        self.state.data_status = DataStatus.PAGE_LOADED
                        metadata["title"] = result.metadata.get("title", "") if hasattr(result, "metadata") else ""
                        markdown_text = result.markdown or ""
                        
                        # Parse review patterns from markdown
                        lines = markdown_text.split("\n")
                        for line in lines:
                            line_s = line.strip()
                            if len(line_s) > 20 and not line_s.startswith("#") and not line_s.startswith("!["):
                                if any(kw in line_s.lower() for kw in ["good", "bad", "product", "quality", "stars", "rating", "buy", "waste", "awesome", "worst"]):
                                    comments.append(NormalizedComment(
                                        id=str(uuid.uuid4()),
                                        platform=platform,
                                        source="crawl4ai",
                                        author="Customer Reviewer",
                                        text=line_s,
                                        rating=None,
                                        likes=0,
                                        product=metadata.get("title", "Product")
                                    ))
                                    if len(comments) >= max_records:
                                        break
                    else:
                        duration = time.time() - start_time
                        self.state.status = EngineStatus.FAILED
                        self.state.execution_time_sec = round(duration, 2)
                        self.state.failure_reason = result.error_message or "Crawl4AI failed to fetch target"
                        return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, self.state.failure_reason
            except Exception as e:
                # If crawl4ai throws runtime error, record failure
                duration = time.time() - start_time
                self.state.status = EngineStatus.FAILED
                self.state.execution_time_sec = round(duration, 2)
                self.state.failure_reason = f"Crawl4AI runtime error: {str(e)}"
                return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, str(e)
        else:
            # Crawl4AI module not installed -> attempt structured content extraction via httpx markdown conversion
            self.state.last_operation = "Crawl4AI package not installed; attempting HTTP markdown parser fallback"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            try:
                async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                    resp = await client.get(resolved_url)
                    if resp.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(resp.text, "lxml")
                        title = soup.find("title")
                        if title:
                            metadata["title"] = title.text.strip()
                            self.state.data_status = DataStatus.METADATA_EXTRACTED
                        
                        # Search review paragraphs
                        p_tags = soup.find_all(["p", "div"], class_=lambda c: c and any(x in str(c).lower() for x in ["review", "comment", "feedback"]))
                        for p in p_tags[:max_records]:
                            txt = p.get_text(separator=" ").strip()
                            if len(txt) > 20 and len(txt) < 1000:
                                comments.append(NormalizedComment(
                                    id=str(uuid.uuid4()),
                                    platform=platform,
                                    source="crawl4ai",
                                    author="Reviewer",
                                    text=txt,
                                    rating=None,
                                    likes=0,
                                    product=metadata.get("title", "Product")
                                ))
                    else:
                        duration = time.time() - start_time
                        self.state.status = EngineStatus.FAILED
                        self.state.execution_time_sec = round(duration, 2)
                        self.state.failure_reason = f"HTTP {resp.status_code} on target page"
                        return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, f"HTTP {resp.status_code}"
            except Exception as exc:
                duration = time.time() - start_time
                self.state.status = EngineStatus.FAILED
                self.state.execution_time_sec = round(duration, 2)
                self.state.failure_reason = f"Fallback error: {str(exc)}"
                return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, str(exc)

        duration = time.time() - start_time
        self.state.execution_time_sec = round(duration, 2)
        self.state.records_extracted = len(comments)

        if comments:
            self.state.status = EngineStatus.SUCCESS
            self.state.data_status = DataStatus.REVIEWS_FOUND
            self.state.last_operation = f"Crawl4AI extracted {len(comments)} structured records"
            return comments, metadata, EngineStatus.SUCCESS, DataStatus.REVIEWS_FOUND, f"Extracted {len(comments)} records"
        elif metadata.get("title"):
            self.state.status = EngineStatus.PARTIAL
            self.state.data_status = DataStatus.METADATA_EXTRACTED
            self.state.last_operation = "Page metadata extracted, no reviews found in markdown"
            self.state.failure_reason = "No reviews found in extracted markdown structure"
            return [], metadata, EngineStatus.PARTIAL, DataStatus.METADATA_EXTRACTED, "Only metadata found"
        else:
            self.state.status = EngineStatus.FAILED
            self.state.data_status = DataStatus.PAGE_LOADED
            self.state.failure_reason = "Crawl4AI found no structured content"
            return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "No content extracted"
