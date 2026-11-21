import asyncio
import time
import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple, Callable, Coroutine
from urllib.parse import urlparse

from backend.ecommerce.browser_manager import BrowserManager
from backend.utils.security import resolve_safe_redirects
from backend.universal_scraper.structured_data import StructuredDataExtractor


class UniversalScraperEngine:
    """
    Universal Scraper Engine Core Integration.
    Based on open-source Universal Scraper architecture:
    - Multi-mode fetching: HTTP (Static) -> Browser (Dynamic) -> Structured Fallback
    - Four-stage anti-bot / degradation chain
    - Automatic website detection & adapter routing
    - Bounded exponential backoff retry
    - Universal structured data parser (JSON-LD, OpenGraph, Microdata)
    - Deduplication, data validation, and clean lifecycle resource cleanup
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
    ]

    PLATFORM_DOMAINS = {
        "instagram": ["instagram.com"],
        "facebook": ["facebook.com", "fb.watch", "m.facebook.com"],
        "amazon": ["amazon.in", "amazon.com", "amazon.co.uk", "amazon.ca", "amazon.de", "amazon.fr", "amazon.it", "amazon.es", "amazon.co.jp", "amazon.com.au", "amazon.com.br", "amazon.com.mx", "amazon.nl", "amazon.sg", "amazon.ae", "amazon.sa", "amazon.com.tr", "amazon.pl", "amazon.se", "amazon.com.be", "amazon.com.eg", "amazon.com.ng", "amzn.in", "amzn.to"],
        "flipkart": ["flipkart.com", "dl.flipkart.com", "fkrt.it"],
        "meesho": ["meesho.com"],
        "ajio": ["ajio.com"],
        "myntra": ["myntra.com"],
        "youtube": ["youtube.com", "youtu.be"]
    }

    @classmethod
    def detect_platform(cls, url: str) -> Tuple[str, str]:
        """
        Auto-detects target platform and returns (platform_key, display_name).
        """
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower().rstrip(".")
        except Exception:
            return "general", "General Web"

        for p_key, domains in cls.PLATFORM_DOMAINS.items():
            if any(host == d or host.endswith("." + d) for d in domains):
                display = {
                    "instagram": "Instagram",
                    "facebook": "Facebook",
                    "amazon": "Amazon",
                    "flipkart": "Flipkart",
                    "meesho": "Meesho",
                    "ajio": "AJIO",
                    "myntra": "Myntra",
                    "youtube": "YouTube"
                }.get(p_key, p_key.title())
                return p_key, display

        return "general", "General Web"

    @classmethod
    async def retry_with_backoff(
        cls,
        func: Callable[[], Coroutine[Any, Any, Any]],
        max_retries: int = 3,
        initial_delay: float = 0.5,
        backoff_factor: float = 2.0,
        max_delay: float = 4.0
    ) -> Any:
        """Executes an async operation with bounded exponential backoff."""
        delay = initial_delay
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as exc:
                last_exception = exc
                if attempt == max_retries - 1:
                    break
                await asyncio.sleep(min(delay, max_delay))
                delay *= backoff_factor
        if last_exception:
            raise last_exception
        return None

    @classmethod
    async def fetch_page(
        cls,
        url: str,
        force_browser: bool = False,
        wait_selector: Optional[str] = None,
        scroll_count: int = 1,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes Universal Four-Stage Extraction Chain:
        Stage 1: Fast HTTP GET with anti-bot header profiles
        Stage 2: Browser fallback (Playwright) if JS rendering or challenge is detected
        Stage 3: Extract structured data (JSON-LD, OpenGraph, microdata, embedded state)
        Stage 4: Return normalized extraction result payload
        """
        # Step 0: Security & Safe redirect check
        safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
        if not safe:
            return {
                "success": False,
                "resolved_url": url,
                "error": f"Security validation rejected URL: {err_msg}",
                "html": "",
                "soup": None,
                "status_code": 403,
                "structured_data": {},
                "extraction_mode": "blocked"
            }

        html_text = ""
        status_code = 0
        extraction_mode = "http"

        # Stage 1: Fast HTTP (Static) Fetch
        if not force_browser:
            if progress_callback:
                await progress_callback(10, f"Attempting fast HTTP static fetch for {resolved_url}...")

            headers = {
                "User-Agent": cls.USER_AGENTS[0],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }

            try:
                async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
                    resp = await client.get(resolved_url)
                    status_code = resp.status_code
                    if resp.status_code == 200:
                        html_text = resp.text
            except Exception:
                pass

        # Check if browser rendering is needed (Stage 2 Degradation)
        is_client_rendered = (
            force_browser or
            not html_text or
            len(html_text) < 1200 or
            "Robot Check" in html_text or
            "Enter the characters you see below" in html_text or
            "Access Denied" in html_text or
            "You need to enable JavaScript" in html_text or
            "window._sharedData" in html_text or
            status_code in [401, 403, 429]
        )

        if is_client_rendered:
            extraction_mode = "browser"
            if progress_callback:
                await progress_callback(25, "Dynamic content or protection detected. Launching managed browser session...")

            async def _browser_fetch():
                b_mgr = await BrowserManager.get_instance()
                async with b_mgr.get_page() as page:
                    await page.goto(resolved_url, wait_until="domcontentloaded", timeout=25000)
                    if wait_selector:
                        try:
                            await page.wait_for_selector(wait_selector, timeout=5000)
                        except Exception:
                            pass

                    # Scroll for dynamic hydration if needed
                    for s_idx in range(scroll_count):
                        await page.evaluate("window.scrollBy(0, 800)")
                        await page.wait_for_timeout(400)

                    content = await page.content()
                    return content

            try:
                html_text = await cls.retry_with_backoff(_browser_fetch, max_retries=2, initial_delay=1.0)
                status_code = 200 if html_text else 500
            except Exception as b_err:
                if not html_text:
                    return {
                        "success": False,
                        "resolved_url": resolved_url,
                        "error": f"Browser rendering failed: {str(b_err)}",
                        "html": "",
                        "soup": None,
                        "status_code": 500,
                        "structured_data": {},
                        "extraction_mode": "failed"
                    }

        # Stage 3: Parse DOM & Structured Semantic Metadata
        soup = BeautifulSoup(html_text, "lxml")
        json_ld = StructuredDataExtractor.extract_json_ld(soup)
        og_meta = StructuredDataExtractor.extract_opengraph_and_meta(soup)
        embedded_state = StructuredDataExtractor.extract_embedded_state(html_text)

        structured_data = {
            "json_ld": json_ld,
            "meta": og_meta,
            "embedded_state": embedded_state
        }

        return {
            "success": True,
            "resolved_url": resolved_url,
            "error": None,
            "html": html_text,
            "soup": soup,
            "status_code": status_code,
            "structured_data": structured_data,
            "extraction_mode": extraction_mode
        }

    @classmethod
    def deduplicate_items(cls, items: List[Any], key_fn: Callable[[Any], str]) -> List[Any]:
        """Removes duplicates preserving first appearance order."""
        seen = set()
        deduped = []
        for it in items:
            k = key_fn(it)
            if k and k not in seen:
                seen.add(k)
                deduped.append(it)
            elif not k:
                deduped.append(it)
        return deduped

