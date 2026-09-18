"""Demo mode endpoint (PRD §43).

Creates a fully-analyzed deterministic demo invoice using the same pipeline
and response structure as real analysis. This is hackathon reliability
infrastructure: if the AI API, network, or document parsing fails, the entire
end-to-end experience still works.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice
from app.schemas.invoice import InvoiceDetail
from app.services import demo_service

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/{scenario}", response_model=InvoiceDetail,
             status_code=status.HTTP_201_CREATED)
def create_demo_invoice(scenario: str, db: Session = Depends(get_db)) -> Invoice:
    try:
        return demo_service.create_demo(db, scenario)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
