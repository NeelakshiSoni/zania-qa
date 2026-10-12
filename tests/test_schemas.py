import pytest
from pydantic import ValidationError

from app.schemas import ChatRequest


def test_valid_chat_request():
    request = ChatRequest(
        document_id="doc-123",
        question="Where is Acme headquartered?",
    )

    assert request.document_id == "doc-123"
    assert request.session_id is None


def test_empty_question_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(document_id="doc-123", question="")


def test_question_over_2000_characters_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(
            document_id="doc-123",
            question="a" * 2001,
        )


def test_missing_document_id_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(question="Hello")


def test_missing_question_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(document_id="doc-123")