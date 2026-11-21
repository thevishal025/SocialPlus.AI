import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import EngineType, EngineStatus, DataStatus
from backend.extraction.engines.base_engine import BaseEngine
from backend.utils.security import is_safe_url, resolve_safe_redirects


class PlaywrightEngine(BaseEngine):
    """
    Engine 2: Playwright Browser Automation.
    Specializes in:
    - Browser-based rendering of dynamic JavaScript pages.
    - Capturing dynamically rendered review containers.
    - Handling scrolling and permitted pagination triggers.
    - Detecting login-walls and anti-bot challenges gracefully.
    """
    engine_type = EngineType.PLAYWRIGHT
    display_name = "Playwright Headless"

    def is_available(self) -> bool:
        try:
            import playwright
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
        self.state.last_operation = "Checking Playwright environment and browser drivers"

        if not self.is_available():
            duration = time.time() - start_time
            self.state.status = EngineStatus.FAILED
            self.state.execution_time_sec = round(duration, 2)
            self.state.failure_reason = "Playwright library is not installed in Python environment"
            self.state.last_operation = "Playwright module missing"
            return [], {}, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "Playwright not installed"

        # Validate URL
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            duration = time.time() - start_time
            self.state.status = EngineStatus.FAILED
            self.state.execution_time_sec = round(duration, 2)
            self.state.failure_reason = f"Security filter error: {err_msg}"
            self.state.last_operation = "Target URL rejected"
            return [], {}, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, err_msg

        comments: List[NormalizedComment] = []
        metadata: Dict[str, Any] = {"engine": "playwright", "platform": platform}

        try:
            from backend.ecommerce.browser_manager import BrowserManager
            self.state.last_operation = "Reusing shared headless browser instance..."
            b_mgr = await BrowserManager.get_instance()

            async with b_mgr.get_page(timeout=25000) as page:
                self.state.last_operation = f"Navigating to {resolved_url[:60]}..."
                response = await page.goto(resolved_url, timeout=20000, wait_until="domcontentloaded")

                # Extract page title
                page_title = await page.title()
                metadata["title"] = page_title
                self.state.data_status = DataStatus.PAGE_LOADED

                # Scroll down slightly to trigger dynamic lazy loading
                self.state.last_operation = "Executing dynamic scroll to trigger review lazy loading..."
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(1500)

                # Search for reviews using evaluate script
                self.state.last_operation = "Evaluating DOM review structures inside browser context..."
                reviews_data = await page.evaluate("""() => {
                    const reviews = [];
                    // Common selectors across e-commerce & social sites
                    const cards = document.querySelectorAll(
                        'div._16PBlm, div._27M-vq, div[data-hook="review"], div.review-card, div.user-review'
                    );
                    cards.forEach(card => {
                        const textEl = card.querySelector('div.t-ZTKy, div._6K-7Co, span[data-hook="review-body"], p.review-text');
                        const authorEl = card.querySelector('p._2sc7ZR, span.a-profile-name, span.author');
                        const titleEl = card.querySelector('p._2-N8zT, a[data-hook="review-title"]');
                        const ratingEl = card.querySelector('div._3LWZlK, i[data-hook="review-star-rating"]');

                        if (textEl && textEl.innerText.trim().length > 5) {
                            reviews.push({
                                text: (titleEl ? titleEl.innerText.trim() + ': ' : '') + textEl.innerText.trim(),
                                author: authorEl ? authorEl.innerText.trim() : 'Customer Reviewer',
                                rating: ratingEl ? parseFloat(ratingEl.innerText) || null : null
                            });
                        }
                    });
                    return reviews;
                }""")


                for r in reviews_data[:max_records]:
                    comments.append(NormalizedComment(
                        id=str(uuid.uuid4()),
                        platform=platform,
                        source="playwright",
                        author=r.get("author", "Anonymous"),
                        text=r.get("text", ""),
                        rating=r.get("rating"),
                        likes=0,
                        product=metadata.get("title", "Product")
                    ))

                duration = time.time() - start_time
                self.state.execution_time_sec = round(duration, 2)
                self.state.records_extracted = len(comments)

                if comments:
                    self.state.status = EngineStatus.SUCCESS
                    self.state.data_status = DataStatus.REVIEWS_FOUND
                    self.state.last_operation = f"Extracted {len(comments)} dynamic reviews via Playwright"
                    return comments, metadata, EngineStatus.SUCCESS, DataStatus.REVIEWS_FOUND, f"Extracted {len(comments)} reviews"
                elif metadata.get("title"):
                    self.state.status = EngineStatus.PARTIAL
                    self.state.data_status = DataStatus.METADATA_EXTRACTED
                    self.state.last_operation = "Page loaded, but no review DOM containers matched"
                    self.state.failure_reason = "No reviews found or page required authentication"
                    return [], metadata, EngineStatus.PARTIAL, DataStatus.METADATA_EXTRACTED, "Only metadata found"
                else:
                    self.state.status = EngineStatus.FAILED
                    self.state.failure_reason = "No content extracted"
                    return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, "No content extracted"

        except Exception as e:
            duration = time.time() - start_time
            self.state.status = EngineStatus.FAILED
            self.state.execution_time_sec = round(duration, 2)
            self.state.failure_reason = f"Playwright execution error: {str(e)}"
            self.state.last_operation = "Runtime exception occurred"
            return [], metadata, EngineStatus.FAILED, DataStatus.EXTRACTION_FAILED, str(e)

