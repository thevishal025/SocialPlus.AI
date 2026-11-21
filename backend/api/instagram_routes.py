from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.api_schemas import FetchRequestMeta
from backend.connectors.instagram_connector import InstagramApiConnector, InstagramPublicConnector
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService
from backend.config import settings

router = APIRouter(prefix="/api/instagram", tags=["Instagram"])


@router.get("/status")
def get_instagram_status():
    return {
        "is_configured": settings.is_meta_configured,
        "app_id_present": bool(settings.META_APP_ID and not settings.META_APP_ID.startswith("YOUR_")),
        "api_version": settings.META_API_VERSION
    }


@router.post("/api/connect")
def connect_instagram():
    """Returns Instagram OAuth / Graph API setup details."""
    if not settings.is_meta_configured:
        return {
            "connected": False,
            "message": "Meta App ID & Secret are not configured in .env.",
            "instructions": "Add META_APP_ID, META_APP_SECRET, and META_REDIRECT_URI in .env to enable OAuth connect."
        }
    auth_url = (
        f"https://www.facebook.com/{settings.META_API_VERSION}/dialog/oauth?"
        f"client_id={settings.META_APP_ID}&redirect_uri={settings.META_REDIRECT_URI}&"
        f"scope=instagram_basic,instagram_manage_comments,pages_show_list,pages_read_engagement"
    )
    return {
        "connected": True,
        "auth_url": auth_url,
        "message": "OAuth URL generated. Connect with your Meta Developer App."
    }


@router.post("/api/fetch")
def fetch_instagram_api(req: FetchRequestMeta, db: Session = Depends(get_db)):
    """Fetch comments via official Meta Graph API."""
    connector = InstagramApiConnector(access_token=req.access_token)
    result = connector.fetch_comments(
        identifier=req.post_url_or_id,
        max_comments=req.max_comments,
        access_token=req.access_token
    )

    if not result.success:
        return {
            "success": False,
            "status_code": result.status_code,
            "message": result.message,
            "limitations": result.limitations
        }

    analysis = pipeline.process_comments(
        comments=result.comments,
        title=f"Instagram Post ({req.post_url_or_id})",
        platform="instagram",
        source_mode="api",
        target_identifier=req.post_url_or_id,
        source_metadata=result.metadata
    )

    HistoryService.save_analysis(db, analysis)
    return {
        "success": True,
        "status_code": "success",
        "message": result.message,
        "comments_count": len(result.comments),
        "comments": [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in result.comments],
        "metadata": result.metadata,
        "analysis": analysis
    }


from backend.universal_scraper import UniversalInstagramScraper

@router.post("/public/fetch")
async def fetch_instagram_public(req: FetchRequestMeta, db: Session = Depends(get_db)):
    """Universal Scraper Engine for Instagram public posts & comments."""
    res = await UniversalInstagramScraper.extract_post_and_comments(
        url=req.post_url_or_id,
        max_comments=req.max_comments
    )

    comments = res.get("comments", [])
    post_meta = res.get("post_metadata", {})

    analysis = None
    if comments:
        analysis = pipeline.process_comments(
            comments=comments,
            title=post_meta.get("caption", f"Instagram Post ({req.post_url_or_id})")[:60],
            platform="instagram",
            source_mode="public",
            target_identifier=req.post_url_or_id,
            source_metadata=post_meta
        )
        HistoryService.save_analysis(db, analysis)

    return {
        "success": res.get("success", False),
        "status": res.get("status", "error"),
        "status_code": res.get("status", "error"),
        "message": res.get("message", ""),
        "post_metadata": post_meta,
        "comments_count": len(comments),
        "comments": [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in comments],
        "analysis": analysis
    }

