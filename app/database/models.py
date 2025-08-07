import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    inn: Mapped[str] = mapped_column(sa.String(12), nullable=True)
    is_member: Mapped[bool] = mapped_column(default=False)
