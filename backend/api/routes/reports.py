from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from backend.database.database import get_db
from backend.services.report_service import report_service
from backend.schemas.report import ReportGenerationRequest, ReportMetadataResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_report(request: ReportGenerationRequest, db: Session = Depends(get_db)):
    """
    Generate a new report and return metadata + preview data.
    """
    try:
        return report_service.generate_report(request.model_dump(exclude_none=True), db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ReportMetadataResponse], status_code=status.HTTP_200_OK)
def get_report_history(db: Session = Depends(get_db)):
    """
    Get history of generated reports.
    """
    try:
        return report_service.get_history(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/export")
def export_report_pdf(report_id: int, db: Session = Depends(get_db)):
    """
    Download the generated PDF for a report.
    """
    try:
        pdf_path = report_service.get_report_pdf(report_id, db)
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF could not be generated or found")
        
        return FileResponse(
            path=pdf_path,
            filename=os.path.basename(pdf_path),
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
