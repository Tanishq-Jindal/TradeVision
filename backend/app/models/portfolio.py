from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.position import Position
    from app.models.trade import Trade
    from app.models.transaction import Transaction


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    cash_balance: Mapped[float] = mapped_column(
        Numeric(precision=14, scale=2),
        default=100000.00,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolio")
    positions: Mapped[List["Position"]] = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades: Mapped[List["Trade"]] = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
