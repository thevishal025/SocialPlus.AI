import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from backend.database import get_db
from backend.ecommerce.platform_detector import PlatformDetector, PLATFORM_METADATA
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.data_normalizer import DataNormalizer
from backend.ecommerce.amazon_scraper import AmazonScraper
from backend.ecommerce.flipkart_scraper import FlipkartScraper
from backend.ecommerce.meesho_scraper import MeeshoScraper
from backend.ecommerce.ajio_scraper import AjioScraper
from backend.ecommerce.myntra_scraper import MyntraScraper
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService
from backend.models.db_models import EcommerceReviewItem
import hashlib
from backend.ecommerce.logging_helper import log_ecom, log_zero_reviews_reason
from backend.universal_scraper import UniversalEcommerceEngine

router = APIRouter(prefix="/api/ecommerce", tags=["E-commerce Deep Intelligence"])


class EcomUrlRequest(BaseModel):
    url: str
    max_reviews: Optional[int] = Field(default=None, ge=1)


class DetectRequest(BaseModel):
    url: str


@router.get("/platforms")
def get_supported_platforms():
    """Lists the five supported platforms with their capabilities."""
    return {
        "platforms": list(PLATFORM_METADATA.values())
    }


@router.post("/detect")
def detect_platform_only(req: DetectRequest):
    """Fast endpoint for frontend live URL input to detect platform."""
    platform_key, resolved_url, meta, err = PlatformDetector.detect_from_url(req.url)
    if not platform_key:
        return {"detected": False, "message": err}
    return {
        "detected": True,
        "platform_key": platform_key,
        "resolved_url": resolved_url,
        "metadata": meta
    }


@router.get("/stored-reviews")
def get_stored_product_reviews(
    product_url: str, page: int = 1, page_size: int = 100, db: Session = Depends(get_db)
):
    """Return previously collected unique reviews for a product, newest first."""
    page = max(1, page)
    page_size = min(500, max(1, page_size))
    query = db.query(EcommerceReviewItem).filter(EcommerceReviewItem.product_url == product_url)
    total = query.count()
    rows = query.order_by(EcommerceReviewItem.extracted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "success": True, "total": total, "page": page, "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "reviews": [{
            "review_id": r.review_id, "reviewer_name": r.reviewer_name, "review_title": r.review_title,
            "review_text": r.review_text, "rating": r.rating, "review_date": r.review_date,
            "verified_purchase": bool(r.verified_purchase), "helpful_votes": r.helpful_votes,
            "product_variant": r.product_variant, "review_images": r.review_images or []
        } for r in rows]
    }


@router.post("/fetch-from-url")
async def extract_and_analyze_ecommerce(req: EcomUrlRequest, db: Session = Depends(get_db)):
    """
    Main E-commerce Intelligence Pipeline:
    Paste Product URL -> Detect Platform -> Deep Product Extraction -> Deep Review Extraction
    -> Validate Data -> Send to SocialPlus.ai AI/ML Pipeline -> Persist History.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Product URL cannot be empty.")

    # Step 1: Detect Platform
    platform_key, resolved_url, meta, err = PlatformDetector.detect_from_url(url)
    if not platform_key:
        return {
            "success": False,
            "status_code": "unsupported_platform",
            "message": err or "Unsupported platform. Please provide an Amazon, Flipkart, Meesho, AJIO, or Myntra URL."
        }

    # Step 2: Route to Universal Scraper Engine for E-commerce
    extract_result = await UniversalEcommerceEngine.extract_product_and_reviews(
        url=resolved_url,
        max_reviews=req.max_reviews
    )

    if not extract_result.get("success"):
        return {
            "success": False,
            "status": extract_result.get("status", "extraction_error"),
            "status_code": extract_result.get("status", "extraction_error"),
            "message": extract_result.get("message", f"Could not extract product details from {platform_key.upper()}."),
            "platform": platform_key
        }

    product = extract_result["product"]
    fresh_reviews = extract_result["reviews"]
    status_msg = extract_result.get("message", "")

    # Merge previously archived reviews for this exact product URL with newly collected
    # records. This lets repeated runs grow the local archive instead of losing earlier pages.
    archived_rows = db.query(EcommerceReviewItem).filter(EcommerceReviewItem.product_url == resolved_url).all()
    merged_by_id = {}
    for row in archived_rows:
        merged_by_id[row.review_id] = CustomerReview(
            review_id=row.review_id, reviewer_name=row.reviewer_name or "Customer",
            review_title=row.review_title, review_text=row.review_text, rating=row.rating,
            review_date=row.review_date, verified_purchase=bool(row.verified_purchase),
            helpful_votes=row.helpful_votes or 0, product_variant=row.product_variant,
            review_images=row.review_images or [], platform=platform_key, source=row.source or "local_archive"
        )
    for review in fresh_reviews:
        review_key = str(review.review_id or hashlib.sha256(
            f"{review.reviewer_name}|{review.review_title}|{review.review_text}".encode("utf-8")
        ).hexdigest())
        if review_key not in merged_by_id:
            review.review_id = review_key
            merged_by_id[review_key] = review
    reviews = list(merged_by_id.values())

    # Persist raw reviews independently from the analysis result so the collected archive
    # remains available even if an analysis model fails or the UI is refreshed.
    archive_rows = []
    for review in reviews:
        review_key = str(review.review_id or hashlib.sha256(
            f"{review.reviewer_name}|{review.review_title}|{review.review_text}".encode("utf-8")
        ).hexdigest())
        archive_id = hashlib.sha256(f"{platform_key}|{resolved_url}|{review_key}".encode("utf-8")).hexdigest()
        archive_rows.append((archive_id, review_key, review))
    existing_ids = set()
    if archive_rows:
        ids = [row[0] for row in archive_rows]
        existing_ids = {row[0] for row in db.query(EcommerceReviewItem.id).filter(EcommerceReviewItem.id.in_(ids)).all()}
    for archive_id, review_key, review in archive_rows:
        if archive_id in existing_ids:
            continue
        db.add(EcommerceReviewItem(
            id=archive_id, platform=platform_key, product_url=resolved_url,
            product_name=product.product_name, review_id=review_key,
            reviewer_name=review.reviewer_name, review_title=review.review_title,
            review_text=review.review_text, rating=review.rating, review_date=review.review_date,
            verified_purchase=1 if review.verified_purchase else 0,
            helpful_votes=review.helpful_votes or 0, product_variant=review.product_variant,
            review_images=review.review_images or [], source=review.source
        ))
    if reviews:
        db.commit()
        log_ecom(f"Reviews saved to database: {len(reviews)} unique records cached in SQLite")

    # Step 3: Normalize reviews to SocialPlus.ai NormalizedComment schema
    normalized_comments = DataNormalizer.to_normalized_comments(reviews, product.product_name)

    status = "success" if normalized_comments else "partial"
    final_message = status_msg
    if not final_message:
        if normalized_comments:
            final_message = f"Successfully extracted product details and {len(normalized_comments)} reviews."
        else:
            final_message = "Product details extracted successfully, but reviews are currently unavailable or protected by platform."

    prior_extraction_info = dict(product.extraction_info or {})
    product.extraction_info = {
        **prior_extraction_info,
        "platform": platform_key,
        "platform_display": meta["display_name"] if meta else platform_key.upper(),
        "source_url": resolved_url,
        "extraction_timestamp": product.extraction_timestamp,
        "reported_reviews": product.total_reviews_count if product.total_reviews_count is not None else product.review_count,
        "extracted_reviews": len(reviews),
        "unique_reviews": len(normalized_comments),
        "status": status
    }

    # Step 4: Run SocialPlus.ai Unified AI/ML Analysis Pipeline if reviews were retrieved
    analysis = None
    if normalized_comments:
        log_ecom(f"Sending {len(normalized_comments)} reviews to AI/ML analysis pipeline...")
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(
            None,
            lambda: pipeline.process_comments(
                comments=normalized_comments,
                title=f"{product.brand + ' - ' if product.brand else ''}{product.product_name}",
                platform="ecommerce",
                source_mode=platform_key,
                target_identifier=resolved_url,
                source_metadata={
                    "platform": platform_key,
                    "product": product.model_dump(),
                    "price": product.current_price,
                    "rating": product.rating,
                    "completeness": product.completeness
                }
            )
        )
        HistoryService.save_analysis(db, analysis)
        log_ecom("AI/ML analysis successfully computed and persisted")

    diagnostics = product.extraction_info.get("diagnostics") or product.extraction_info.get("review_collection") or {}
    reported_count = product.total_reviews_count if product.total_reviews_count is not None else product.review_count
    retrieved_count = diagnostics.get("retrieved_reviews", len(reviews))
    pages_processed = diagnostics.get("pages_scanned", 1 if reviews else 0)

    log_ecom("API response successfully returned")

    return {
        "success": True,
        "status": status,
        "status_code": status,
        "platform": platform_key,
        "platform_display": meta["display_name"] if meta else platform_key.upper(),
        "product": product.model_dump(),
        "reviews": [r.model_dump() for r in reviews],
        "reviews_count": len(reviews),
        "unique_reviews_count": len(normalized_comments),
        "retrieved_reviews_count": retrieved_count,
        "reported_review_count": reported_count,
        "pages_processed": pages_processed,
        "collection_mode": "all_accessible",
        "collection_limit": req.max_reviews,
        "review_collection": diagnostics,
        "diagnostics": diagnostics,
        "stop_reason": diagnostics.get("stop_reason"),
        "failure_reason": diagnostics.get("failure_reason"),
        "platform_limitations": diagnostics.get("platform_limitations"),
        "message": final_message,
        "analysis": analysis
    }
