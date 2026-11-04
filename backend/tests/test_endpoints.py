import pytest
from fastapi import HTTPException

try:
    from app.main import (
        home,
        health_check,
        validate_pdf_filename,
        validate_upload_content,
        verify_api_key,
        DocumentComparisonRequest
    )
except ImportError:
    from backend.app.main import (
        home,
        health_check,
        validate_pdf_filename,
        validate_upload_content,
        verify_api_key,
        DocumentComparisonRequest
    )


def test_home_endpoint():
    result = home()
    assert result["status"] == "running"
    assert "Enterprise Knowledge Assistant" in result["message"]


def test_health_endpoint():
    result = health_check()
    assert result["status"] == "healthy"


def test_validate_pdf_filename_valid():
    assert validate_pdf_filename("policy_report_2026.pdf") == "policy_report_2026.pdf"
    assert validate_pdf_filename("annual leave.pdf") == "annual leave.pdf"
    assert validate_pdf_filename("DOC-1.0.pdf") == "DOC-1.0.pdf"


def test_validate_pdf_filename_invalid():
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_filename("../../etc/passwd.pdf")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_filename("malicious.exe")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_filename(".pdf")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_filename("bad;rm -rf.pdf")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_filename("")
    assert exc_info.value.status_code == 400


def test_verify_api_key_dev_mode(monkeypatch):
    monkeypatch.delenv("APP_API_KEY", raising=False)
    assert verify_api_key(None) is True


def test_verify_api_key_enforced(monkeypatch):
    monkeypatch.setenv("APP_API_KEY", "secret-test-token")
    assert verify_api_key("secret-test-token") is True

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("wrong-token")
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(None)
    assert exc_info.value.status_code == 401


def test_upload_validation_non_pdf():
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_content("document.txt", b"plain text")
    assert exc_info.value.status_code == 400
    assert "Only PDF files are allowed" in exc_info.value.detail


def test_upload_validation_empty_content():
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_content("empty.pdf", b"")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_upload_validation_file_too_large():
    too_large = b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_content("large.pdf", too_large)
    assert exc_info.value.status_code == 413


def test_upload_validation_invalid_pdf_magic():
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_content("fake.pdf", b"This is not a real PDF")
    assert exc_info.value.status_code == 400
    assert "not a valid PDF" in exc_info.value.detail


def test_upload_validation_success():
    valid_content = b"%PDF-1.5 standard valid content"
    filename = validate_upload_content("valid_policy.pdf", valid_content)
    assert filename == "valid_policy.pdf"


def test_compare_same_document_request_logic():
    doc_a = "same.pdf"
    doc_b = "same.pdf"
    assert doc_a == doc_b

    req = DocumentComparisonRequest(
        document_a="doc_a.pdf",
        document_b="doc_b.pdf",
        question="What changed?"
    )
    assert req.document_a == "doc_a.pdf"
    assert req.document_b == "doc_b.pdf"
