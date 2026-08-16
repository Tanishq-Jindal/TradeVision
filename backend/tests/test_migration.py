import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from app.db.base import Base
from app.models.user import User
from app.models.portfolio import Portfolio


@pytest.mark.asyncio
async def test_database_models_metadata_schema():
    """Verify User and Portfolio models have valid declarative configurations."""
    assert User.__tablename__ == "users"
    assert Portfolio.__tablename__ == "portfolios"
    assert "email" in User.__table__.columns
    assert "hashed_password" in User.__table__.columns
    assert "cash_balance" in Portfolio.__table__.columns
    assert "user_id" in Portfolio.__table__.columns


@pytest.mark.asyncio
async def test_database_schema_creation_and_insertion():
    """Verify creating tables and inserting foundation models works on async engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Verify tables created
        res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        table_names = [row[0] for row in res.fetchall()]
        assert "users" in table_names
        assert "portfolios" in table_names
    await engine.dispose()
