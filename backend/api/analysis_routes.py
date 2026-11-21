import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.api_schemas import ManualAnalysisRequest, NormalizedComment
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/manual")
def analyze_manual_comments(req: ManualAnalysisRequest, db: Session = Depends(get_db)):
    """
    Direct Manual Comment Analysis.
    Accepts one comment per line or a list of comment strings.
    Processes comments through the exact same unified pipeline.
    """
    comment_texts = []
    if req.comments:
        comment_texts = [c.strip() for c in req.comments if c and c.strip()]
    elif req.raw_text:
        lines = req.raw_text.splitlines()
        comment_texts = [line.strip() for line in lines if line.strip()]

    if not comment_texts:
        raise HTTPException(
            status_code=400,
            detail="No comments provided. Please enter at least one comment."
        )

    normalized = [
        NormalizedComment(
            id=f"manual-{idx+1}-{uuid.uuid4().hex[:6]}",
            platform=req.platform or "manual",
            source="manual",
            author=f"User {idx+1}",
            text=text,
            likes=0
        )
        for idx, text in enumerate(comment_texts)
    ]

    analysis = pipeline.process_comments(
        comments=normalized,
        title=req.title or "Manual Comment Intelligence Analysis",
        platform=req.platform or "manual",
        source_mode="manual",
        target_identifier="Manual Input"
    )

    HistoryService.save_analysis(db, analysis)
    return {
        "success": True,
        "message": f"Successfully analyzed {len(normalized)} comments.",
        "analysis": analysis
    }


@router.get("/{analysis_id}")
def get_analysis_details(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve complete analysis details by ID."""
    result = HistoryService.get_analysis(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return result


@router.get("/{analysis_id}/comments")
def get_analysis_comments_paginated(
    analysis_id: str,
    search: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    emotion: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    moderation_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("date"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Filter, search, sort, and paginate individual comments belonging to an analysis."""
    return HistoryService.filter_comments(
        db=db,
        analysis_id=analysis_id,
        search=search,
        sentiment=sentiment,
        emotion=emotion,
        intent=intent,
        moderation_status=moderation_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc
    )

