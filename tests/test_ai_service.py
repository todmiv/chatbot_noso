import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_service import ask_ai
from app.config import settings

@pytest.mark.asyncio
async def test_ask_ai_test_mode():
    original_key = settings.deepseek_api_key
    settings.deepseek_api_key = "test_key"
    
    result = await ask_ai("Что такое СРО?")
    assert result.startswith("Тестовый ответ на вопрос:")
    
    settings.deepseek_api_key = original_key

@pytest.mark.asyncio
async def test_ask_ai_success():
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Ответ от ИИ"))]
    mock_client.chat.completions.create.return_value = mock_response

    with patch('app.services.ai_service.client', mock_client):
        result = await ask_ai("Что такое СРО?")
        assert result == "Ответ от ИИ"

@pytest.mark.asyncio
async def test_ask_ai_error():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch('app.services.ai_service.client', mock_client):
        result = await ask_ai("Что такое СРО?")
        assert result == "Ошибка при получении ответа"

@pytest.mark.asyncio
async def test_ask_ai_with_context():
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Ответ с контекстом"))]
    mock_client.chat.completions.create.return_value = mock_response

    with patch('app.services.ai_service.client', mock_client):
        result = await ask_ai("Что такое СРО?", "Контекст из документов")
        assert "Ответ с контекстом" in result
