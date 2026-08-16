from typing import List, Union
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.trading import WatchlistAddRequest, WatchlistItemResponse, WatchlistResponse
from app.services.watchlist import (
    add_item_to_watchlist,
    add_to_watchlist,
    create_watchlist,
    delete_watchlist,
    get_user_watchlist,
    get_user_watchlists,
    get_watchlist_items,
    remove_from_watchlist,
    remove_item_from_watchlist,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[WatchlistItemResponse],
    summary="Get user default watchlist",
    description="Returns all stock symbols in the user's default watchlist with real-time prices and 24h percentage change.",
)
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WatchlistItemResponse]:
    return await get_user_watchlist(db, current_user.id)


@router.get(
    "/all",
    response_model=List[WatchlistResponse],
    summary="Get all user watchlists",
    description="Returns all watchlists and their items owned by the authenticated user.",
)
async def list_all_watchlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WatchlistResponse]:
    return await get_user_watchlists(db, current_user.id)


@router.post(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new watchlist",
    description="Creates a new empty watchlist for the authenticated user.",
)
async def create_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    return await create_watchlist(db, current_user.id)


@router.delete(
    "/{watchlist_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a watchlist",
    description="Deletes the specified watchlist if owned by the authenticated user.",
)
async def delete_user_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await delete_watchlist(db, current_user.id, watchlist_id)
    return {"message": f"Watchlist #{watchlist_id} deleted successfully."}


@router.get(
    "/{watchlist_id}/items",
    response_model=List[WatchlistItemResponse],
    summary="Get items in a specific watchlist",
    description="Retrieves live quotes for all items in the specified watchlist.",
)
async def get_items_for_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WatchlistItemResponse]:
    return await get_watchlist_items(db, current_user.id, watchlist_id)


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add symbol to a specific watchlist",
    description="Adds a stock symbol to the specified watchlist.",
)
async def add_item_to_specific_watchlist(
    watchlist_id: int,
    request: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    return await add_item_to_watchlist(db, current_user.id, watchlist_id, request.symbol)


@router.delete(
    "/{watchlist_id}/items/{symbol}",
    status_code=status.HTTP_200_OK,
    summary="Remove symbol from a specific watchlist",
    description="Removes a stock symbol from the specified watchlist.",
)
async def remove_item_from_specific_watchlist(
    watchlist_id: int,
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await remove_item_from_watchlist(db, current_user.id, watchlist_id, symbol)
    return {"message": f"{symbol.upper()} removed from watchlist #{watchlist_id}."}


@router.post(
    "/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add symbol to default watchlist",
    description="Adds a ticker symbol to the user's default watchlist.",
)
async def add_item(
    request: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    return await add_to_watchlist(db, current_user.id, request.symbol)


@router.delete(
    "/items/{symbol}",
    status_code=status.HTTP_200_OK,
    summary="Remove symbol from default watchlist",
    description="Removes a ticker symbol from the user's default watchlist.",
)
async def remove_item(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await remove_from_watchlist(db, current_user.id, symbol)
    return {"message": f"{symbol.upper()} removed from watchlist."}
