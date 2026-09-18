"""Pydantic schemas for document metadata."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentType


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: DocumentType
    file_name: str
    mime_type: str | None = None
    is_demo: bool = False
    created_at: datetime
