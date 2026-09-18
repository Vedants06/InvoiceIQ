"""Helpers for building synthetic documents in tests."""

import fitz  # PyMuPDF


def make_pdf(lines: list[str], path: str) -> str:
    """Create a real (text-based) PDF containing the given lines."""
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 20
    doc.save(path)
    doc.close()
    return path
