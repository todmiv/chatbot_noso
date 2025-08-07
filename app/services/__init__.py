"""
Бизнес-логика: ИИ, работа с документами, уведомления.
"""
from .ai_service import ask_ai
from .document_service import doc_service

__all__ = ["ask_ai", "doc_service"]
