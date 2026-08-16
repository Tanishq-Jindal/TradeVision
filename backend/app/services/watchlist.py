import logging
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.trading import WatchlistItemResponse, WatchlistResponse
from app.services.market_data import UNIVERSE, get_quote

logger = logging.getLogger(__name__)


async def get_or_create_watchlist(db: AsyncSession, user_id: int) -> Watchlist:
    """
    Retrieves or creates the user's default watchlist.
    """
    stmt = (
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.user_id == user_id)
    )
    result = await db.execute(stmt)
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        watchlist = Watchlist(user_id=user_id)
        db.add(watchlist)
        await db.commit()
        # Seed default popular symbols
        defaults = ["NVDA", "AAPL", "MSFT", "TSLA"]
        for sym in defaults:
            db.add(WatchlistItem(watchlist_id=watchlist.id, symbol=sym))
        await db.commit()

        # Re-fetch with items loaded
        result = await db.execute(stmt)
        watchlist = result.scalar_one()

    return watchlist


async def get_user_watchlists(db: AsyncSession, user_id: int) -> List[WatchlistResponse]:
    """
    Returns all watchlists owned by the user.
    """
    stmt = (
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.user_id == user_id)
    )
    result = await db.execute(stmt)
    watchlists = result.scalars().all()

    if not watchlists:
        default_wl = await get_or_create_watchlist(db, user_id)
        watchlists = [default_wl]

    responses: List[WatchlistResponse] = []
    for wl in watchlists:
        items_resp: List[WatchlistItemResponse] = []
        for item in wl.items:
            try:
                quote = await get_quote(item.symbol)
                price = quote.c
                change = quote.d
                change_pct = quote.dp
            except Exception:
                price, change, change_pct = 100.0, 0.0, 0.0

            meta = UNIVERSE.get(item.symbol, {"name": item.symbol})
            items_resp.append(
                WatchlistItemResponse(
                    id=item.id,
                    symbol=item.symbol,
                    name=meta["name"],
                    price=price,
                    change=change,
                    change_pct=change_pct,
                    added_at=item.added_at,
                )
            )

        responses.append(
            WatchlistResponse(
                id=wl.id,
                user_id=wl.user_id,
                created_at=wl.created_at,
                items=items_resp,
            )
        )

    return responses


async def create_watchlist(db: AsyncSession, user_id: int) -> WatchlistResponse:
    """
    Creates a new watchlist for the user.
    """
    wl = Watchlist(user_id=user_id)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return WatchlistResponse(
        id=wl.id,
        user_id=wl.user_id,
        created_at=wl.created_at,
        items=[],
    )


async def delete_watchlist(db: AsyncSession, user_id: int, watchlist_id: int) -> None:
    """
    Deletes a watchlist owned by the user.
    """
    stmt = select(Watchlist).where(Watchlist.id == watchlist_id)
    result = await db.execute(stmt)
    wl = result.scalar_one_or_none()

    if not wl:
        raise NotFoundError(message=f"Watchlist #{watchlist_id} not found.", code="WATCHLIST_NOT_FOUND")

    if wl.user_id != user_id:
        raise ForbiddenError(message="You do not have permission to delete this watchlist.", code="FORBIDDEN")

    await db.delete(wl)
    await db.commit()


async def get_watchlist_items(db: AsyncSession, user_id: int, watchlist_id: int) -> List[WatchlistItemResponse]:
    """
    Retrieves live items for a specific watchlist.
    """
    stmt = (
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.id == watchlist_id)
    )
    result = await db.execute(stmt)
    wl = result.scalar_one_or_none()

    if not wl:
        raise NotFoundError(message=f"Watchlist #{watchlist_id} not found.", code="WATCHLIST_NOT_FOUND")

    if wl.user_id != user_id:
        raise ForbiddenError(message="You do not have permission to access this watchlist.", code="FORBIDDEN")

    responses: List[WatchlistItemResponse] = []
    for item in wl.items:
        try:
            quote = await get_quote(item.symbol)
            price = quote.c
            change = quote.d
            change_pct = quote.dp
        except Exception:
            price, change, change_pct = 100.0, 0.0, 0.0

        meta = UNIVERSE.get(item.symbol, {"name": item.symbol})
        responses.append(
            WatchlistItemResponse(
                id=item.id,
                symbol=item.symbol,
                name=meta["name"],
                price=price,
                change=change,
                change_pct=change_pct,
                added_at=item.added_at,
            )
        )

    return responses


async def add_item_to_watchlist(
    db: AsyncSession, user_id: int, watchlist_id: int, symbol: str
) -> WatchlistItemResponse:
    """
    Adds a symbol to a specific watchlist.
    """
    sym = symbol.strip().upper()

    stmt = (
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.id == watchlist_id)
    )
    result = await db.execute(stmt)
    wl = result.scalar_one_or_none()

    if not wl:
        raise NotFoundError(message=f"Watchlist #{watchlist_id} not found.", code="WATCHLIST_NOT_FOUND")

    if wl.user_id != user_id:
        raise ForbiddenError(message="You do not have permission to modify this watchlist.", code="FORBIDDEN")

    # Check for duplicate
    for item in wl.items:
        if item.symbol == sym:
            raise ConflictError(
                message=f"{sym} is already in your watchlist.",
                code="DUPLICATE_SYMBOL",
                details={"symbol": sym, "watchlist_id": watchlist_id},
            )

    # Validate quote / symbol
    quote = await get_quote(sym)

    new_item = WatchlistItem(watchlist_id=wl.id, symbol=sym)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    meta = UNIVERSE.get(sym, {"name": sym})
    return WatchlistItemResponse(
        id=new_item.id,
        symbol=sym,
        name=meta["name"],
        price=quote.c,
        change=quote.d,
        change_pct=quote.dp,
        added_at=new_item.added_at,
    )


async def remove_item_from_watchlist(
    db: AsyncSession, user_id: int, watchlist_id: int, symbol: str
) -> None:
    """
    Removes a symbol from a specific watchlist.
    """
    sym = symbol.strip().upper()

    stmt = (
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.id == watchlist_id)
    )
    result = await db.execute(stmt)
    wl = result.scalar_one_or_none()

    if not wl:
        raise NotFoundError(message=f"Watchlist #{watchlist_id} not found.", code="WATCHLIST_NOT_FOUND")

    if wl.user_id != user_id:
        raise ForbiddenError(message="You do not have permission to modify this watchlist.", code="FORBIDDEN")

    item_to_remove = next((item for item in wl.items if item.symbol == sym), None)
    if not item_to_remove:
        raise NotFoundError(
            message=f"Symbol '{sym}' not found in watchlist #{watchlist_id}.",
            code="ITEM_NOT_FOUND",
            details={"symbol": sym, "watchlist_id": watchlist_id},
        )

    await db.delete(item_to_remove)
    await db.commit()


# Convenience methods for default watchlist
async def get_user_watchlist(db: AsyncSession, user_id: int) -> List[WatchlistItemResponse]:
    watchlist = await get_or_create_watchlist(db, user_id)
    return await get_watchlist_items(db, user_id, watchlist.id)


async def add_to_watchlist(db: AsyncSession, user_id: int, symbol: str) -> WatchlistItemResponse:
    watchlist = await get_or_create_watchlist(db, user_id)
    return await add_item_to_watchlist(db, user_id, watchlist.id, symbol)


async def remove_from_watchlist(db: AsyncSession, user_id: int, symbol: str) -> None:
    watchlist = await get_or_create_watchlist(db, user_id)
    await remove_item_from_watchlist(db, user_id, watchlist.id, symbol)
