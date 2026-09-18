"""Document file serving for in-app preview (P1, PRD §27).

Only files physically stored under the configured upload directory are
served (path-traversal safe). Demo documents (demo:// pseudo-paths) are not
served — the frontend renders a structured preview for those.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Document

router = APIRouter(prefix="/api/documents", tags=["documents"])

_EXTENSION_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

settings = get_settings()


@router.get("/{document_id}/raw")
def get_document_raw(document_id: uuid.UUID, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Document not found.")
    if document.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Demo documents have no raw file.")

    upload_root = Path(settings.upload_dir).resolve()
    target = Path(document.file_path).resolve()
    # Prevent any path traversal outside the upload directory.
    if upload_root not in target.parents and target != upload_root:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Document path is not accessible.")
    if not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Document file is missing on disk.")

    media_type = _EXTENSION_MIME.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(
        target,
        media_type=media_type,
        filename=document.file_name,
        content_disposition_type="inline",
    )
