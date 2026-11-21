import asyncio
import time
import uuid
import re
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse

from backend.schemas.api_schemas import NormalizedComment
from backend.utils.security import is_safe_url, resolve_safe_redirects
from backend.extraction.models import (
    EngineType,
    EngineStatus,
    OverallStatus,
    DataStatus,
    ExtractionStats
)
from backend.extraction.task_manager import ExtractionTaskManager, ExtractionTaskState
from backend.extraction.quality import DataQualityValidator
from backend.extraction.performance_history import EnginePerformanceTracker
from backend.extraction.engines import (
    Crawl4AIEngine,
    PlaywrightEngine,
    ScrapyEngine,
    BeautifulSoupEngine
)
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService
from backend.database import SessionLocal


class UniversalExtractionOrchestrator:
    """
    SocialPlus Universal Multi-Engine Extraction Orchestrator.
    Implements intelligent hybrid execution:
    - Auto-detection of platforms and domains.
    - Parallel execution of independent, compatible extraction engines.
    - Dynamic sequential fallback when engines encounter anti-bot or rendering blocks.
    - Real-time event streaming via SSE.
    - Data deduplication and quality validation before AI/ML processing.
    """

    @staticmethod
    def detect_platform(url: str) -> str:
        try:
            hostname = (urlparse(url).hostname or "").lower().rstrip(".")
        except ValueError:
            return "general"

        def is_host(*domains: str) -> bool:
            return any(hostname == domain or hostname.endswith("." + domain) for domain in domains)

        if is_host("youtube.com", "youtu.be"):
            return "youtube"
        elif is_host("instagram.com"):
            return "instagram"
        elif is_host("facebook.com", "fb.watch"):
            return "facebook"
        elif is_host("flipkart.com"):
            return "flipkart"
        elif is_host("amazon.in", "amzn.to"):
            return "amazon_in"
        elif is_host("myntra.com"):
            return "myntra"
        elif is_host("meesho.com"):
            return "meesho"
        elif is_host("ajio.com"):
            return "ajio"
        elif is_host("snapdeal.com"):
            return "snapdeal"
        elif is_host("tatacliq.com"):
            return "tatacliq"
        elif is_host("nykaa.com"):
            return "nykaa"
        elif is_host("jiomart.com"):
            return "jiomart"
        return "general"

    @classmethod
    async def run_extraction(cls, task_id: str):
        """Asynchronous execution worker for an extraction task."""
        task: Optional[ExtractionTaskState] = ExtractionTaskManager.get_task(task_id)
        if not task:
            return

        try:
            if task.cancel_requested:
                task.end_time = time.time()
                task.push_event("completed", task.to_dict())
                return

            task.add_log(f"Received URL: {task.url}", level="info")
            task.update_progress(10.0, "Validating URL and inspecting redirect chain...")

            # ── STEP 1: Safe Redirect Resolution & SSRF Check ───────────────
            safe, resolved_url, err_msg, chain = resolve_safe_redirects(task.url)
            if not safe:
                task.status = OverallStatus.FAILED
                task.error_message = f"Security filter blocked URL: {err_msg}"
                task.add_log(f"Security check failed: {err_msg}", level="error")
                task.update_progress(100.0, "Security validation failed")
                task.push_event("completed", task.to_dict())
                return

            if len(chain) > 1:
                task.add_log(f"Resolved {len(chain)} redirect hop(s) to: {resolved_url[:75]}", level="info")
            else:
                task.add_log(f"Validated destination: {resolved_url[:75]}", level="info")

            # ── STEP 2: Platform Identification ─────────────────────────────
            platform = cls.detect_platform(resolved_url)
            task.platform = platform
            task.add_log(f"Target platform identified: {platform.upper()}", level="info")
            task.push_event("platform_detected", {"platform": platform, "resolved_url": resolved_url})
            task.update_progress(20.0, f"Platform confirmed: {platform.upper()}. Initializing engines...")

            # ── STEP 3: Instantiate Core Engines ────────────────────────────
            c4a_engine = Crawl4AIEngine()
            pw_engine = PlaywrightEngine()
            scrapy_engine = ScrapyEngine()
            bs4_engine = BeautifulSoupEngine()

            all_extracted_comments: List[NormalizedComment] = []
            extracted_metadata: Dict[str, Any] = {"resolved_url": resolved_url, "platform": platform}

            # ── STEP 4: Execution Strategy (Dedicated E-com or Universal Hybrid) ──
            ecom_platforms = {
                "amazon_in": "amazon",
                "amazon": "amazon",
                "flipkart": "flipkart",
                "meesho": "meesho",
                "ajio": "ajio",
                "myntra": "myntra"
            }

            if platform in ecom_platforms:
                ecom_key = ecom_platforms[platform]
                task.add_log(f"Routing to dedicated {ecom_key.upper()} intelligence engine", level="info")
                task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.RUNNING, f"Connecting to {ecom_key.upper()}...")
                task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.RUNNING, "Parsing specifications and DOM selectors...")
                task.update_engine(EngineType.CRAWL4AI.value, EngineStatus.SKIPPED, "Not required for specialized e-commerce connector")
                task.update_engine(EngineType.SCRAPY.value, EngineStatus.SKIPPED, "Not required for specialized e-commerce connector")

                async def progress_cb(pct: float, msg: str):
                    task.update_progress(min(pct, 88.0), msg)
                    task.add_log(msg, level="info")

                from backend.ecommerce.amazon_scraper import AmazonScraper
                from backend.ecommerce.flipkart_scraper import FlipkartScraper
                from backend.ecommerce.meesho_scraper import MeeshoScraper
                from backend.ecommerce.ajio_scraper import AjioScraper
                from backend.ecommerce.myntra_scraper import MyntraScraper
                from backend.ecommerce.data_normalizer import DataNormalizer

                product = None
                reviews = []
                status_msg = ""
                scraper_start = time.time()

                try:
                    if ecom_key == "amazon":
                        product, reviews, status_msg = await AmazonScraper.extract_product_and_reviews(resolved_url, task.max_records, progress_cb)
                    elif ecom_key == "flipkart":
                        product, reviews, status_msg = await FlipkartScraper.extract_product_and_reviews(resolved_url, task.max_records, progress_cb)
                    elif ecom_key == "meesho":
                        product, reviews, status_msg = await MeeshoScraper.extract_product_and_reviews(resolved_url, task.max_records, progress_cb)
                    elif ecom_key == "ajio":
                        product, reviews, status_msg = await AjioScraper.extract_product_and_reviews(resolved_url, task.max_records, progress_cb)
                    elif ecom_key == "myntra":
                        product, reviews, status_msg = await MyntraScraper.extract_product_and_reviews(resolved_url, task.max_records, progress_cb)
                except Exception as sc_err:
                    status_msg = f"Extraction error: {str(sc_err)}"
                    task.add_log(status_msg, level="error")

                elapsed = round(time.time() - scraper_start, 2)
                task.stats.engines_attempted = 2

                if product:
                    extracted_metadata["product"] = product.model_dump()
                    extracted_metadata["product_name"] = product.product_name
                    extracted_metadata["brand"] = product.brand
                    extracted_metadata["price"] = product.current_price
                    extracted_metadata["rating"] = product.rating
                    extracted_metadata["completeness"] = product.completeness
                    diag = product.extraction_info.get("diagnostics") or {}
                    extracted_metadata["diagnostics"] = diag
                    task.add_log(f"Product identified: {product.product_name[:50]} (Brand: {product.brand or 'N/A'}, Price: ₹{product.current_price or 'N/A'})", level="success")
                    task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.SUCCESS, "Extracted product specifications & pricing", 1, elapsed)
                else:
                    task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.FAILED, status_msg or "Product details not found", 0, elapsed)

                if reviews:
                    task.stats.engines_successful = 2
                    norm_reviews = DataNormalizer.to_normalized_comments(reviews, product.product_name if product else "Product")
                    all_extracted_comments.extend(norm_reviews)
                    task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.SUCCESS, f"Extracted {len(reviews)} reviews", len(reviews), elapsed)
                    task.add_log(f"Successfully extracted {len(reviews)} customer reviews with pagination", level="success", engine="playwright")
                else:
                    task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.PARTIAL if product else EngineStatus.FAILED, status_msg or "No reviews exposed", 0, elapsed)
                    task.add_log(status_msg or f"No customer reviews could be retrieved from {ecom_key.upper()}", level="warning")

            else:
                # Execute Crawl4AI and BeautifulSoup in parallel for initial extraction
                task.update_progress(35.0, "Launching parallel extraction: Crawl4AI + BeautifulSoup...")
                task.add_log("Starting parallel workers: Crawl4AI & BeautifulSoup", level="info")

                task.update_engine(EngineType.CRAWL4AI.value, EngineStatus.RUNNING, "Extracting page content & markdown structure")
                task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.RUNNING, "Parsing DOM review selectors")

                c4a_task = asyncio.create_task(c4a_engine.extract(resolved_url, platform, task.max_records))
                bs4_task = asyncio.create_task(bs4_engine.extract(resolved_url, platform, task.max_records))

                c4a_res, bs4_res = await asyncio.gather(c4a_task, bs4_task, return_exceptions=True)

                task.stats.engines_attempted += 2

                # Process Crawl4AI result
                if isinstance(c4a_res, Exception):
                    task.update_engine(EngineType.CRAWL4AI.value, EngineStatus.FAILED, "Crawl4AI exception", failure_reason=str(c4a_res))
                    task.add_log(f"Crawl4AI failed: {str(c4a_res)}", level="error", engine="crawl4ai")
                    EnginePerformanceTracker.record_execution(EngineType.CRAWL4AI, platform, 1.0, False, 0, str(c4a_res))
                else:
                    c_comments, c_meta, c_status, c_dstatus, c_msg = c4a_res
                    task.update_engine(EngineType.CRAWL4AI.value, c_status, c4a_engine.state.last_operation, len(c_comments), c4a_engine.state.execution_time_sec, c4a_engine.state.failure_reason, c_dstatus)
                    if c_comments:
                        all_extracted_comments.extend(c_comments)
                        task.stats.engines_successful += 1
                        task.add_log(f"Crawl4AI successfully retrieved {len(c_comments)} records", level="success", engine="crawl4ai")
                    else:
                        task.add_log(f"Crawl4AI: {c_msg}", level="warning", engine="crawl4ai")
                    extracted_metadata.update(c_meta)
                    EnginePerformanceTracker.record_execution(EngineType.CRAWL4AI, platform, c4a_engine.state.execution_time_sec, bool(c_comments), len(c_comments))

                # Process BeautifulSoup result
                if isinstance(bs4_res, Exception):
                    task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.FAILED, "BeautifulSoup exception", failure_reason=str(bs4_res))
                    task.add_log(f"BeautifulSoup failed: {str(bs4_res)}", level="error", engine="beautifulsoup")
                    EnginePerformanceTracker.record_execution(EngineType.BEAUTIFUL_SOUP, platform, 1.0, False, 0, str(bs4_res))
                else:
                    b_comments, b_meta, b_status, b_dstatus, b_msg = bs4_res
                    task.update_engine(EngineType.BEAUTIFUL_SOUP.value, b_status, bs4_engine.state.last_operation, len(b_comments), bs4_engine.state.execution_time_sec, bs4_engine.state.failure_reason, b_dstatus)
                    if b_comments:
                        all_extracted_comments.extend(b_comments)
                        task.stats.engines_successful += 1
                        task.add_log(f"BeautifulSoup extracted {len(b_comments)} reviews", level="success", engine="beautifulsoup")
                    else:
                        task.add_log(f"BeautifulSoup: {b_msg}", level="warning", engine="beautifulsoup")
                    extracted_metadata.update(b_meta)
                    EnginePerformanceTracker.record_execution(EngineType.BEAUTIFUL_SOUP, platform, bs4_engine.state.execution_time_sec, bool(b_comments), len(b_comments))

                task.update_progress(55.0, f"Initial parallel run complete ({len(all_extracted_comments)} records). Evaluating fallbacks...")

                # ── STEP 5: Conditional Fallback to Playwright & Scrapy ─────────
                # If review count is below target or static HTML lacked comments, execute Playwright browser
                if len(all_extracted_comments) < task.max_records and not task.cancel_requested:
                    task.add_log("Initial static extraction yielded insufficient records. Attempting Playwright headless browser fallback...", level="info")
                    task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.RUNNING, "Starting headless Chromium to render dynamic content")
                    task.update_progress(65.0, "Running Playwright headless browser fallback...")
                    task.stats.engines_attempted += 1

                    try:
                        pw_res = await pw_engine.extract(resolved_url, platform, task.max_records - len(all_extracted_comments))
                        p_comments, p_meta, p_status, p_dstatus, p_msg = pw_res
                        task.update_engine(EngineType.PLAYWRIGHT.value, p_status, pw_engine.state.last_operation, len(p_comments), pw_engine.state.execution_time_sec, pw_engine.state.failure_reason, p_dstatus)
                        if p_comments:
                            all_extracted_comments.extend(p_comments)
                            task.stats.engines_successful += 1
                            task.add_log(f"Playwright successfully extracted {len(p_comments)} dynamic reviews", level="success", engine="playwright")
                        else:
                            task.add_log(f"Playwright: {p_msg}", level="warning", engine="playwright")
                        extracted_metadata.update(p_meta)
                        EnginePerformanceTracker.record_execution(EngineType.PLAYWRIGHT, platform, pw_engine.state.execution_time_sec, bool(p_comments), len(p_comments))
                    except Exception as p_err:
                        task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.FAILED, "Playwright execution error", failure_reason=str(p_err))
                        task.add_log(f"Playwright error: {str(p_err)}", level="error", engine="playwright")
                else:
                    task.update_engine(EngineType.PLAYWRIGHT.value, EngineStatus.SKIPPED, "Target record count reached with initial engines")
                    task.add_log("Playwright skipped: Sufficient records already extracted", level="info")

                # If still incomplete, execute Scrapy for structured pagination crawling
                if len(all_extracted_comments) < task.max_records and not task.cancel_requested:
                    task.add_log("Evaluating Scrapy spider for multi-page review pagination...", level="info")
                    task.update_engine(EngineType.SCRAPY.value, EngineStatus.RUNNING, "Crawling review pagination listings")
                    task.update_progress(78.0, "Running Scrapy pagination spider...")
                    task.stats.engines_attempted += 1

                    try:
                        s_comments, s_meta, s_status, s_dstatus, s_msg = await scrapy_engine.extract(resolved_url, platform, task.max_records - len(all_extracted_comments))
                        task.update_engine(EngineType.SCRAPY.value, s_status, scrapy_engine.state.last_operation, len(s_comments), scrapy_engine.state.execution_time_sec, scrapy_engine.state.failure_reason, s_dstatus)
                        if s_comments:
                            all_extracted_comments.extend(s_comments)
                            task.stats.engines_successful += 1
                            task.add_log(f"Scrapy retrieved {len(s_comments)} paginated reviews", level="success", engine="scrapy")
                        else:
                            task.add_log(f"Scrapy: {s_msg}", level="warning", engine="scrapy")
                        extracted_metadata.update(s_meta)
                        EnginePerformanceTracker.record_execution(EngineType.SCRAPY, platform, scrapy_engine.state.execution_time_sec, bool(s_comments), len(s_comments))
                    except Exception as s_err:
                        task.update_engine(EngineType.SCRAPY.value, EngineStatus.FAILED, "Scrapy error", failure_reason=str(s_err))
                        task.add_log(f"Scrapy error: {str(s_err)}", level="error", engine="scrapy")
                else:
                    task.update_engine(EngineType.SCRAPY.value, EngineStatus.SKIPPED, "Target count reached or pagination not needed")

            if task.cancel_requested:
                task.status = OverallStatus.CANCELLED
                task.end_time = time.time()
                task.update_progress(task.progress, "Extraction cancelled")
                task.push_event("completed", task.to_dict())
                return

            # ── STEP 6: Quality Validation & Deduplication ───────────────────
            task.update_progress(88.0, "Validating data quality and removing duplicate records...")
            task.add_log("Running data quality validation & cross-engine deduplication...", level="info")

            valid_comments, val_stats, data_status = DataQualityValidator.validate_and_deduplicate(all_extracted_comments)
            task.stats.total_records = val_stats["total_records"]
            task.stats.unique_records = val_stats["unique_records"]
            task.stats.duplicates_removed = val_stats["duplicates_removed"]
            task.stats.valid_records = val_stats["valid_records"]
            task.stats.invalid_records = val_stats["invalid_records"]
            task.final_comments = valid_comments
            task.metadata = extracted_metadata

            task.add_log(
                f"Data quality summary: {len(valid_comments)} unique valid records, {val_stats['duplicates_removed']} duplicates removed",
                level="info"
            )

            # ── STEP 7: Route to AI/ML Intelligence Pipeline ────────────────
            if valid_comments:
                task.update_progress(94.0, f"Analyzing {len(valid_comments)} comments through AI/ML pipeline...")
                task.add_log("Sending validated dataset to SocialPlus.ai AI/ML engine...", level="info")

                title = extracted_metadata.get("product_name") or extracted_metadata.get("title") or f"{platform.upper()} Reviews"
                
                # Execute pipeline synchronously in thread to avoid event loop starvation
                loop = asyncio.get_event_loop()
                analysis = await loop.run_in_executor(
                    None,
                    lambda: pipeline.process_comments(
                        comments=valid_comments,
                        title=title,
                        platform=platform,
                        source_mode="universal_engine",
                        target_identifier=resolved_url,
                        source_metadata=extracted_metadata
                    )
                )

                # Persist to database
                db = SessionLocal()
                try:
                    HistoryService.save_analysis(db, analysis)
                finally:
                    db.close()

                task.analysis_result = analysis
                task.status = OverallStatus.COMPLETED
                task.end_time = time.time()
                task.update_progress(100.0, f"Complete! Analyzed {len(valid_comments)} reviews.")
                task.add_log("AI/ML analysis successfully completed and saved to history", level="success")
            else:
                # No reviews found (e.g. anti-bot block, login wall, or empty reviews)
                task.status = OverallStatus.PARTIAL if extracted_metadata.get("title") else OverallStatus.FAILED
                task.end_time = time.time()
                task.update_progress(100.0, "Extraction concluded — no valid customer reviews detected.")
                
                platform_display = platform.upper()
                task.add_log(
                    f"Direct unauthenticated review harvesting is guarded by {platform_display}'s anti-bot protections. "
                    f"Use 'Upload File' mode to analyze an exported reviews dataset.",
                    level="warning"
                )
                task.error_message = (
                    f"Direct unauthenticated review scraping is restricted by {platform_display}'s bot-detection controls. "
                    f"Page metadata was verified, but review text could not be extracted without authentication.\n\n"
                    f"Alternative: Please use 'Upload File' mode to upload a CSV, Excel, or JSON review export."
                )

            task.push_event("completed", task.to_dict())

        except Exception as e:
            task.status = OverallStatus.FAILED
            task.end_time = time.time()
            task.error_message = f"Universal orchestrator failure: {str(e)}"
            task.add_log(f"Critical error: {str(e)}", level="error")
            task.update_progress(100.0, "Extraction failed due to an unexpected error")
            task.push_event("error", {"error": str(e)})
