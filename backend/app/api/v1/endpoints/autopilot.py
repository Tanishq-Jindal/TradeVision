from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.autopilot import AutopilotConfig, AutopilotStatusResponse
from app.services.autopilot import (
    evaluate_and_run_autopilot_cycle,
    get_user_autopilot_config,
    update_user_autopilot_config,
)

router = APIRouter()


@router.get(
    "/status",
    response_model=AutopilotStatusResponse,
    summary="Get user autopilot configuration and execution status",
)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutopilotStatusResponse:
    return await evaluate_and_run_autopilot_cycle(db, current_user.id)


@router.post(
    "/config",
    response_model=AutopilotStatusResponse,
    summary="Update autopilot guardrails and toggle active state",
)
async def set_config(
    config: AutopilotConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutopilotStatusResponse:
    update_user_autopilot_config(current_user.id, config)
    return await evaluate_and_run_autopilot_cycle(db, current_user.id)
