import pytest
import asyncio
from backend.utils.security import is_safe_url, is_ip_restricted, resolve_safe_redirects
from backend.extraction.quality import DataQualityValidator
from backend.extraction.models import (
    EngineType,
    EngineStatus,
    DataStatus,
    OverallStatus
)
from backend.extraction.task_manager import ExtractionTaskManager
from backend.extraction.orchestrator import UniversalExtractionOrchestrator
from backend.extraction.engines import (
    BeautifulSoupEngine,
    ScrapyEngine,
    PlaywrightEngine,
    Crawl4AIEngine
)
from backend.schemas.api_schemas import NormalizedComment


def test_nat64_and_ssrf_security():
    """Verify SSRF blocks private IPs while allowing valid NAT64 IPv4 translations."""
    # Private IPv4 must be blocked
    safe, err = is_safe_url("http://127.0.0.1:8000")
    assert not safe
    assert "localhost or internal" in err

    safe, err = is_safe_url("http://192.168.1.1/admin")
    assert not safe

    safe, err = is_safe_url("http://169.254.169.254/latest/meta-data")
    assert not safe

    # Valid public domain
    safe, err = is_safe_url("https://www.google.com")
    assert safe


def test_flipkart_short_url_redirect():
    """Verify Flipkart short URL resolves to legitimate product page without SSRF rejection."""
    safe, err = is_safe_url("https://dl.flipkart.com/s/fTWKTPuuuN")
    assert safe, f"Flipkart URL falsely rejected: {err}"

    success, final_url, err_msg, chain = resolve_safe_redirects("https://dl.flipkart.com/s/fTWKTPuuuN")
    assert success
    assert "flipkart.com" in final_url
    assert len(chain) >= 1


def test_platform_detection():
    """Verify platform detection across major e-commerce and social platforms."""
    assert UniversalExtractionOrchestrator.detect_platform("https://www.flipkart.com/product/p/itm123") == "flipkart"
    assert UniversalExtractionOrchestrator.detect_platform("https://dl.flipkart.com/s/abc123") == "flipkart"
    assert UniversalExtractionOrchestrator.detect_platform("https://www.amazon.in/dp/B08N5WRWNW") == "amazon_in"
    assert UniversalExtractionOrchestrator.detect_platform("https://www.myntra.com/tshirt/12345") == "myntra"
    assert UniversalExtractionOrchestrator.detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert UniversalExtractionOrchestrator.detect_platform("https://www.instagram.com/p/C6xyz123/") == "instagram"
    assert UniversalExtractionOrchestrator.detect_platform("https://www.facebook.com/page/posts/123") == "facebook"


def test_quality_validation_and_deduplication():
    """Verify quality validation strips HTML, removes blanks, and deduplicates records."""
    comments = [
        NormalizedComment(id="1", platform="flipkart", source="bs4", author="Alice", text="<b>Great product!</b> Highly recommended."),
        NormalizedComment(id="2", platform="flipkart", source="bs4", author="Alice", text="Great product! Highly recommended."), # Duplicate
        NormalizedComment(id="3", platform="flipkart", source="bs4", author="Bob", text=""), # Empty
        NormalizedComment(id="4", platform="flipkart", source="bs4", author="Charlie", text="<html><body>noise</body></html>"), # Junk
        NormalizedComment(id="5", platform="flipkart", source="scrapy", author="David", text="Average battery life, decent display.")
    ]

    valid, stats, status = DataQualityValidator.validate_and_deduplicate(comments)
    assert len(valid) == 2
    assert stats["duplicates_removed"] == 1
    assert stats["invalid_records"] == 2
    assert status == DataStatus.DATA_VALIDATED
    assert valid[0].text == "Great product! Highly recommended."


def test_engine_initializations():
    """Verify that all 4 engine classes initialize properly."""
    bs4 = BeautifulSoupEngine()
    assert bs4.engine_type == EngineType.BEAUTIFUL_SOUP
    assert bs4.is_available() is True

    scrapy = ScrapyEngine()
    assert scrapy.engine_type == EngineType.SCRAPY
    assert scrapy.is_available() is True

    pw = PlaywrightEngine()
    assert pw.engine_type == EngineType.PLAYWRIGHT
    assert pw.is_available() is True

    c4a = Crawl4AIEngine()
    assert c4a.engine_type == EngineType.CRAWL4AI


def test_task_manager_lifecycle():
    """Verify task creation, state updates, event queuing, and cancellation."""
    task = ExtractionTaskManager.create_task(
        task_id="test-task-1",
        url="https://www.flipkart.com/test-product",
        platform="flipkart",
        max_records=50
    )
    assert task.status == OverallStatus.RUNNING
    assert task.engines[EngineType.CRAWL4AI.value].status == EngineStatus.WAITING

    task.update_engine(EngineType.BEAUTIFUL_SOUP.value, EngineStatus.RUNNING, "Extracting DOM")
    assert task.engines[EngineType.BEAUTIFUL_SOUP.value].status == EngineStatus.RUNNING

    task.update_progress(45.0, "Parsing reviews")
    assert task.progress == 45.0

    cancelled = ExtractionTaskManager.cancel_task("test-task-1")
    assert cancelled is True
    assert task.status == OverallStatus.CANCELLED

