import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

# Базовый класс для всех моделей SQLAlchemy
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Модель пользователя бота (члены СРО и гости)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    inn: Mapped[str] = mapped_column(sa.String(12), nullable=True)
    is_member: Mapped[bool] = mapped_column(default=False)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(sa.String(10), default='guest')
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())

    __table_args__ = (sa.CheckConstraint("role IN ('guest', 'member', 'admin')", name='check_role'),)

# Модель документа СРО (PDF/DOCX файлы)
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(sa.Text)
    path: Mapped[str] = mapped_column(sa.Text)
    version: Mapped[int] = mapped_column(sa.Integer)
    uploaded_by: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())

# Модель подписки пользователя на документы
class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey('users.id'), primary_key=True)
    document_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('documents.id'), primary_key=True)

# Модель для логгирования действий бота
class BotLog(Base):
    __tablename__ = "bot_logs"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(sa.BigInteger)
    type: Mapped[str] = mapped_column(sa.String(20))
    status: Mapped[str] = mapped_column(sa.String(10))
    latency_ms: Mapped[int] = mapped_column(sa.Integer)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())
