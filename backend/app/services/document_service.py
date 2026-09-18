"""File upload handling (PRD §9, §38).

Responsibilities:
  * Validate file extensions per document type
  * Enforce the upload size limit (streamed, so oversize files never land
    fully on disk)
  * Sanitize the original filename
  * Persist bytes under the configured upload directory with a unique name
"""

import base64
import re
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.models.enums import DocumentType

settings = get_settings()

ALLOWED_EXTENSIONS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.INVOICE: (".pdf", ".png", ".jpg", ".jpeg"),
    DocumentType.CONTRACT: (".pdf",),
    DocumentType.TIMESHEET: (".csv", ".xlsx"),
}

_INVALID_FILE_MSG = (
    "Unable to process this file. Please upload a supported PDF, PNG, JPG, "
    "CSV or XLSX file."
)
_FILENAME_SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _extension(file_name: str) -> str:
    return Path(file_name).suffix.lower()


def validate_extension(document_type: DocumentType, file_name: str) -> None:
    """Raise 400 if the file extension is not allowed for this document type."""
    ext = _extension(file_name)
    if ext not in ALLOWED_EXTENSIONS[document_type]:
        allowed = ", ".join(ALLOWED_EXTENSIONS[document_type])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{_INVALID_FILE_MSG} Expected for {document_type.value}: {allowed}.",
        )


def sanitize_filename(file_name: str) -> str:
    """Reduce a user-supplied filename to a safe basename (PRD §38)."""
    base = Path(file_name).name  # strip any path components
    base = _FILENAME_SANITIZE_RE.sub("_", base).strip("._") or "document"
    return base[:120]


def _unique_storage_name(invoice_id: uuid.UUID, document_type: DocumentType,
                         file_name: str) -> str:
    ext = _extension(file_name)
    return f"{invoice_id}_{document_type.value.lower()}_{uuid.uuid4().hex[:8]}{ext}"


def save_upload(
    invoice_id: uuid.UUID,
    document_type: DocumentType,
    upload: UploadFile,
) -> tuple[str, str, str]:
    """Validate and persist an uploaded file.

    Returns (stored_file_path, sanitized_original_name, mime_type).
    Raises HTTP 400 on invalid type or oversize content.
    """
    original_name = sanitize_filename(upload.filename or "document")
    validate_extension(document_type, original_name)

    storage_name = _unique_storage_name(invoice_id, document_type, original_name)
    destination = Path(settings.upload_dir) / storage_name

    # Stream to disk while enforcing the size limit, so an oversize upload
    # never fully materializes on disk.
    max_bytes = settings.max_upload_bytes
    total = 0
    try:
        with destination.open("wb") as out:
            while chunk := upload.file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"File exceeds the maximum upload size of "
                            f"{settings.max_upload_mb} MB."
                        ),
                    )
                out.write(chunk)
    finally:
        upload.file.close()

    if total == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    return str(destination), original_name, (upload.content_type or "")


class DocumentParseError(Exception):
    """Raised when a document cannot be read into text for extraction."""


def read_pdf_text(file_path: str) -> str:
    """Extract embedded text from a PDF using PyMuPDF."""
    try:
        with fitz.open(file_path) as doc:
            pages = [page.get_text("text") for page in doc]
    except Exception as exc:
        raise DocumentParseError(f"Could not read PDF: {exc}") from exc
    text = "\n".join(pages).strip()
    if not text:
        raise DocumentParseError(
            "The PDF contains no extractable text (it may be a scanned image)."
        )
    return text


def read_image_base64(file_path: str) -> str:
    """Base64-encode an image for vision-based extraction."""
    return base64.b64encode(Path(file_path).read_bytes()).decode("ascii")


_IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def image_media_type(file_path: str) -> str:
    return _IMAGE_MIME.get(Path(file_path).suffix.lower(), "image/png")


def read_document_text(file_path: str) -> str:
    """Read a stored invoice/contract document to text.

    PDFs are parsed with PyMuPDF. Image invoices (PNG/JPG) are handled by the
    vision model in extraction_service rather than as text.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return read_pdf_text(file_path)
    raise DocumentParseError(f"Text extraction is not supported for '{suffix}' files.")


def is_image_file(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in (".png", ".jpg", ".jpeg")
