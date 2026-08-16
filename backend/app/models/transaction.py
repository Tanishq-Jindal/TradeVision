from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.trade import Trade


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # TRADE, DEPOSIT, ADJUSTMENT
    amount: Mapped[float] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    related_trade_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("trades.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
    trade: Mapped[Optional["Trade"]] = relationship("Trade", back_populates="transaction")
