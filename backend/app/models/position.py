from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(precision=14, scale=4), nullable=False)
    avg_entry_price: Mapped[float] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_symbol"),
    )
