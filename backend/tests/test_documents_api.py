"""Document preview endpoint tests (PRD §27, §38)."""

from tests.helpers import make_pdf


def test_raw_document_served_inline(client, tmp_path):
    pdf = make_pdf(["INVOICE INV-9", "Acme", "Total 100"], str(tmp_path / "inv.pdf"))
    con = make_pdf(["AGREEMENT Acme"], str(tmp_path / "con.pdf"))
    with open(pdf, "rb") as a, open(con, "rb") as b:
        up = client.post(
            "/api/invoices/upload",
            files={
                "invoice": ("inv.pdf", a, "application/pdf"),
                "contract": ("con.pdf", b, "application/pdf"),
            },
        )
    assert up.status_code == 201, up.text
    iid = up.json()["invoice_id"]
    detail = client.get(f"/api/invoices/{iid}").json()
    invoice_doc = next(d for d in detail["documents"] if d["document_type"] == "INVOICE")
    assert invoice_doc["is_demo"] is False

    raw = client.get(f"/api/documents/{invoice_doc['id']}/raw")
    assert raw.status_code == 200
    assert raw.headers["content-type"] == "application/pdf"
    assert "inline" in raw.headers["content-disposition"]


def test_demo_document_has_no_raw(client):
    body = client.post("/api/demo/critical").json()
    doc = body["documents"][0]
    assert doc["is_demo"] is True
    raw = client.get(f"/api/documents/{doc['id']}/raw")
    assert raw.status_code == 404


def test_unknown_document_404(client):
    raw = client.get("/api/documents/00000000-0000-0000-0000-000000000000/raw")
    assert raw.status_code == 404
