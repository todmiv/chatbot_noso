import pytest
from app.services.ai_service import ask_ai

@pytest.mark.asyncio
async def test_ai_reply():
    answer = await ask_ai("Что такое СРО?")
    assert len(answer) > 10
