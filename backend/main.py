import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database import Base, engine
from backend.schemas.api_schemas import HealthResponse
from backend.ecommerce.ecommerce_router import router as ecommerce_router
from backend.api import (
    youtube_router,
    instagram_router,
    facebook_router,
    upload_router,
    analysis_router,
    history_router,
    report_router,
    extraction_router
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SocialPlus.ai API",
    description="Advanced Social Media & E-commerce Comment Intelligence Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(youtube_router)
app.include_router(instagram_router)
app.include_router(facebook_router)
app.include_router(ecommerce_router)
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(history_router)
app.include_router(report_router)
app.include_router(extraction_router)


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health status and configuration diagnostics."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        youtube_api_configured=settings.is_youtube_configured,
        meta_api_configured=settings.is_meta_configured,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z"
    )


# Serve Frontend
if os.path.exists(settings.FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=settings.FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_index():
        index_file = os.path.join(settings.FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "SocialPlus.ai backend is running. Frontend index.html not found."}

