from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.transaction import Transaction


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="trades")
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction", back_populates="trade", uselist=False)
