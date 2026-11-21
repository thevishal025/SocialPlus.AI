from backend.api.youtube_routes import router as youtube_router
from backend.api.instagram_routes import router as instagram_router
from backend.api.facebook_routes import router as facebook_router
from backend.ecommerce.ecommerce_router import router as ecommerce_router
from backend.api.upload_routes import router as upload_router
from backend.api.analysis_routes import router as analysis_router
from backend.api.history_routes import router as history_router
from backend.api.report_routes import router as report_router
from backend.api.extraction_routes import router as extraction_router

__all__ = [
    "youtube_router",
    "instagram_router",
    "facebook_router",
    "ecommerce_router",
    "upload_router",
    "analysis_router",
    "history_router",
    "report_router",
    "extraction_router",
]
