import os
import json
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import settings
from backend.connectors.file_parser import parse_comments_file
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api/upload", tags=["Upload"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".txt"}


@router.post("")
async def upload_and_analyze_file(
    file: UploadFile = File(...),
    platform: str = Form(default="upload"),
    custom_mapping: Optional[str] = Form(default=None),
    auto_analyze: bool = Form(default=True),
    db: Session = Depends(get_db)
):
    """
    Accepts CSV, XLSX, XLS, JSON, or TXT file, parses comments, and sends to unified analysis engine.
    """
    filename = file.filename or "uploaded_comments.csv"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: CSV, XLSX, XLS, JSON, TXT."
        )

    # Read file content safely
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    temp_id = f"{uuid.uuid4().hex}_{filename}"
    temp_path = os.path.join(settings.UPLOADS_DIR, temp_id)

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        mapping_dict = None
        if custom_mapping:
            try:
                mapping_dict = json.loads(custom_mapping)
            except Exception:
                pass

        comments, metadata = parse_comments_file(
            file_path=temp_path,
            original_filename=filename,
            platform=platform,
            custom_mapping=mapping_dict
        )

        if not comments:
            return {
                "success": False,
                "message": "No valid comments found in uploaded file. Check column mappings or file content.",
                "metadata": metadata
            }

        if auto_analyze:
            analysis = pipeline.process_comments(
                comments=comments,
                title=f"File Upload: {filename}",
                platform=platform,
                source_mode="upload",
                target_identifier=filename,
                source_metadata=metadata
            )
            HistoryService.save_analysis(db, analysis)
            return {
                "success": True,
                "message": f"Successfully parsed and analyzed {len(comments)} comments from '{filename}'.",
                "metadata": metadata,
                "analysis": analysis
            }
        else:
            return {
                "success": True,
                "message": f"Successfully parsed {len(comments)} comments.",
                "comment_count": len(comments),
                "metadata": metadata,
                "preview": [c.model_dump() for c in comments[:5]]
            }

    finally:
        # Clean up temporary uploaded file if desired
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

