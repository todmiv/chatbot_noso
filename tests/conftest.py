import pytest
from unittest.mock import MagicMock
from app.services.document_service import DocumentService

@pytest.fixture
def mock_doc_service():
    mock = MagicMock(spec=DocumentService)
    mock.search.return_value = []
    return mock

@pytest.fixture(autouse=True)
def override_doc_service(monkeypatch, mock_doc_service):
    monkeypatch.setattr("app.services.document_service.doc_service", mock_doc_service)
