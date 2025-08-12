from celery import Celery
from app.config import settings

celery = Celery(
    'chatbot_noso',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.services.tasks']
)