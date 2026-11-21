import os
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import settings
from backend.services.history_service import HistoryService
from backend.services.report_generator import ReportGenerator

router = APIRouter(prefix="/api/report", tags=["Reports"])


@router.get("/{analysis_id}/pdf")
def download_pdf_report(analysis_id: str, db: Session = Depends(get_db)):
    data = HistoryService.get_analysis(db, analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    pdf_path = os.path.join(settings.REPORTS_DIR, f"report_{analysis_id}.pdf")
    ReportGenerator.generate_pdf(data, pdf_path)

    return FileResponse(
        path=pdf_path,
        filename=f"SocialPlus_Report_{analysis_id[:8]}.pdf",
        media_type="application/pdf"
    )


@router.get("/{analysis_id}/html")
def download_html_report(analysis_id: str, db: Session = Depends(get_db)):
    data = HistoryService.get_analysis(db, analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    html_content = ReportGenerator.generate_html(data)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=SocialPlus_Report_{analysis_id[:8]}.html"}
    )


@router.get("/{analysis_id}/csv")
def download_csv_report(analysis_id: str, db: Session = Depends(get_db)):
    data = HistoryService.get_analysis(db, analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    csv_content = ReportGenerator.generate_csv(data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=SocialPlus_Data_{analysis_id[:8]}.csv"}
    )


@router.get("/{analysis_id}/excel")
def download_excel_report(analysis_id: str, db: Session = Depends(get_db)):
    data = HistoryService.get_analysis(db, analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    excel_path = os.path.join(settings.REPORTS_DIR, f"report_{analysis_id}.xlsx")
    ReportGenerator.generate_excel(data, excel_path)

    return FileResponse(
        path=excel_path,
        filename=f"SocialPlus_Report_{analysis_id[:8]}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/{analysis_id}/json")
def download_json_report(analysis_id: str, db: Session = Depends(get_db)):
    data = HistoryService.get_analysis(db, analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    return data

