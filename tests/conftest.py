import pytest
from unittest.mock import MagicMock, Mock, AsyncMock
from app.services.document_service import DocumentService

@pytest.fixture
def mock_doc_service():
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])
    mock._load_documents = Mock(return_value=None)
    mock._build_index = Mock(return_value=None)
    mock._extract_text_from_pdf = Mock(return_value="")
    mock._extract_text_from_docx = Mock(return_value="")
    return mock

@pytest.fixture
def mock_message():
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 123
    message.answer = AsyncMock()
    return message

@pytest.fixture(autouse=True)
def override_doc_service(monkeypatch, mock_doc_service):
    monkeypatch.setattr("app.services.document_service.doc_service", mock_doc_service)
