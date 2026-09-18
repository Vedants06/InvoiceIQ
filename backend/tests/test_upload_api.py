"""Upload & list API tests (PRD §34, §38)."""

import io

from tests.conftest import make_files


def test_upload_creates_invoice_with_documents(client):
    response = client.post("/api/invoices/upload", files=make_files())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "uploaded"
    assert body["has_timesheet"] is False
    invoice_id = body["invoice_id"]

    detail = client.get(f"/api/invoices/{invoice_id}").json()
    assert detail["processing_status"] == "UPLOADED"
    assert detail["status"] == "PENDING_REVIEW"
    doc_types = {d["document_type"] for d in detail["documents"]}
    assert doc_types == {"INVOICE", "CONTRACT"}
    # A contract placeholder row is linked
    assert detail["contract"] is not None


def test_upload_with_timesheet(client):
    files = make_files()
    files["timesheet"] = ("timesheet.csv", b"Employee,Date,Hours\nJohn,2026-08-01,8\n", "text/csv")
    response = client.post("/api/invoices/upload", files=files)
    assert response.status_code == 201
    assert response.json()["has_timesheet"] is True


def test_missing_contract_rejected(client):
    response = client.post(
        "/api/invoices/upload",
        files={"invoice": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 400
    assert "Contract" in response.json()["detail"]


def test_invoice_extension_validation(client):
    files = make_files()
    files["invoice"] = ("invoice.exe", b"MZ bad", "application/octet-stream")
    response = client.post("/api/invoices/upload", files=files)
    assert response.status_code == 400
    assert "supported" in response.json()["detail"].lower()


def test_contract_must_be_pdf(client):
    files = make_files()
    files["contract"] = ("contract.docx", b"pk", "application/msword")
    response = client.post("/api/invoices/upload", files=files)
    assert response.status_code == 400


def test_timesheet_extension_validation(client):
    files = make_files()
    files["timesheet"] = ("timesheet.txt", b"hello", "text/plain")
    response = client.post("/api/invoices/upload", files=files)
    assert response.status_code == 400


def test_path_traversal_filename_sanitized(client):
    files = make_files()
    files["invoice"] = ("../../etc/evil.pdf", b"%PDF-1.4", "application/pdf")
    response = client.post("/api/invoices/upload", files=files)
    assert response.status_code == 201
    detail = client.get(f"/api/invoices/{response.json()['invoice_id']}").json()
    invoice_doc = next(d for d in detail["documents"] if d["document_type"] == "INVOICE")
    assert "/" not in invoice_doc["file_name"]
    assert ".." not in invoice_doc["file_name"]


def test_oversize_upload_rejected(client, monkeypatch):
    import app.services.document_service as doc_service

    # 2 MB limit; send ~3 MB
    monkeypatch.setattr(doc_service.settings, "max_upload_mb", 2)
    big = b"0" * (3 * 1024 * 1024)
    response = client.post(
        "/api/invoices/upload",
        files={
            "invoice": ("big.pdf", io.BytesIO(big), "application/pdf"),
            "contract": ("contract.pdf", b"%PDF-1.4", "application/pdf"),
        },
    )
    assert response.status_code == 413


def test_list_invoices(client):
    client.post("/api/invoices/upload", files=make_files())
    client.post("/api/invoices/upload", files=make_files())
    response = client.get("/api/invoices")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_unknown_invoice_404(client):
    response = client.get("/api/invoices/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
