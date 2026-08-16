"""Trading and Watchlist Schema (positions, trades, transactions, watchlists, watchlist_items)

Revision ID: 0002_trading_and_watchlist
Revises: 0001_initial_foundation
Create Date: 2026-08-16 03:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_trading_and_watchlist"
down_revision: Union[str, None] = "0001_initial_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create positions table
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("avg_entry_price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_symbol"),
    )
    op.create_index(op.f("ix_positions_id"), "positions", ["id"], unique=False)
    op.create_index(op.f("ix_positions_portfolio_id"), "positions", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_positions_symbol"), "positions", ["symbol"], unique=False)

    # 2. Create trades table
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_id"), "trades", ["id"], unique=False)
    op.create_index(op.f("ix_trades_portfolio_id"), "trades", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_trades_symbol"), "trades", ["symbol"], unique=False)

    # 3. Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("related_trade_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_trade_id"], ["trades.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    op.create_index(op.f("ix_transactions_portfolio_id"), "transactions", ["portfolio_id"], unique=False)

    # 4. Create watchlists table
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_watchlists_id"), "watchlists", ["id"], unique=False)

    # 5. Create watchlist_items table
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )
    op.create_index(op.f("ix_watchlist_items_id"), "watchlist_items", ["id"], unique=False)
    op.create_index(op.f("ix_watchlist_items_watchlist_id"), "watchlist_items", ["watchlist_id"], unique=False)


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_table("transactions")
    op.drop_table("trades")
    op.drop_table("positions")
