import pytest
from app.services.ai_service import ask_ai
from app.services.document_service import doc_service

@pytest.mark.asyncio
async def test_ai_reply():
    answer = await ask_ai("Что такое СРО?")
    assert len(answer) > 10

@pytest.mark.asyncio
async def test_document_search():
    docs = await doc_service.search("СРО")
    assert isinstance(docs, list)
    if docs:
        assert "name" in docs[0]
        assert "text" in docs[0]
        assert "score" in docs[0]
