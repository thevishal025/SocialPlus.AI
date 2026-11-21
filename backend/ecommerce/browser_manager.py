import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("ecommerce.browser")


class BrowserManager:
    """
    Shared Playwright Browser Architecture.
    Maintains a reusable headless Chromium browser process, sharing resources across
    scrapers rather than spinning up heavy new browser instances for every request.
    """
    _instance: Optional["BrowserManager"] = None
    _playwright = None
    _browser = None
    _lock = asyncio.Lock()
    _is_available: Optional[bool] = None

    def __init__(self):
        pass

    @classmethod
    async def get_instance(cls) -> "BrowserManager":
        if cls._instance is None:
            cls._instance = BrowserManager()
        return cls._instance

    @classmethod
    async def is_browser_available(cls) -> bool:
        """Check if Playwright and Chromium executable are available."""
        if cls._is_available is not None:
            return cls._is_available

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                try:
                    b = await p.chromium.launch(headless=True)
                    await b.close()
                    cls._is_available = True
                except Exception as e:
                    logger.warning(f"Chromium executable not ready: {e}")
                    cls._is_available = False
        except Exception as exc:
            logger.warning(f"Playwright library error: {exc}")
            cls._is_available = False

        return cls._is_available

    async def _ensure_browser(self):
        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu"
                    ]
                )
                self._is_available = True

    @asynccontextmanager
    async def get_page(self, timeout: float = 30000):
        """
        Context manager that yields a newly isolated page from the shared browser instance.
        Cleans up the page context upon exit.
        """
        browser_ready = await self.is_browser_available()
        if not browser_ready:
            raise RuntimeError("Playwright Chromium browser executable is not available on this host.")

        await self._ensure_browser()

        # Create isolated browser context with anti-detection headers
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True
        )
        page = await context.new_page()
        page.set_default_timeout(timeout)

        try:
            yield page
        finally:
            try:
                await page.close()
                await context.close()
            except Exception:
                pass

    async def close(self):
        """Clean up shared browser and Playwright process."""
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
