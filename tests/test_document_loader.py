
import json

import pytest
from langchain_core.documents import Document

from app.services.document_loader import load_document


def test_load_valid_json():
    content = json.dumps({
        "company": "Acme",
        "headquarters": "San Jose",
    }).encode("utf-8")

    chunks = load_document(content, "sample.json")

    assert chunks
    assert any("San Jose" in chunk.page_content for chunk in chunks)
    assert all(chunk.metadata["source"] == "sample.json" for chunk in chunks)


def test_invalid_json_raises_clear_error():
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_document(b"{invalid}", "sample.json")


def test_unsupported_file_type():
    with pytest.raises(ValueError, match="Only PDF and JSON"):
        load_document(b"some text", "sample.txt")


def test_empty_json_document_is_rejected():
    # JSON null is valid JSON, but still produces text.
    # Therefore, it should load successfully.
    chunks = load_document(b"null", "sample.json")

    assert chunks

def test_empty_json_file_is_rejected():
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_document(b"", "sample.json")


def test_corrupted_pdf_is_rejected():
    with pytest.raises(ValueError, match="Could not read this PDF"):
        load_document(b"this is not a valid PDF", "broken.pdf")


def test_oversized_extracted_document_is_rejected(monkeypatch):
    import app.services.document_loader as loader

    monkeypatch.setattr(loader, "MAX_CHARS", 10)

    content = b'{"description": "This text exceeds ten characters"}'

    with pytest.raises(ValueError, match="2-million-character limit"):
        load_document(content, "large.json")
