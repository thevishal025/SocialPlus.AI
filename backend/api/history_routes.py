from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def list_analysis_history(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List historical analysis runs."""
    items = HistoryService.list_history(db=db, search=search, limit=limit, offset=offset)
    return {
        "total": len(items),
        "items": items
    }


@router.delete("/{analysis_id}")
def delete_analysis_record(analysis_id: str, db: Session = Depends(get_db)):
    """Delete an analysis run and its stored comment records."""
    deleted = HistoryService.delete_analysis(db, analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return {
        "success": True,
        "message": f"Analysis '{analysis_id}' deleted successfully."
    }

