from fastapi import APIRouter
from app.schemas.command import CommandParseRequest, CommandParseResponse
from app.services.command_palette import parse_trade_command

router = APIRouter()


@router.post(
    "/parse",
    response_model=CommandParseResponse,
    summary="Parse natural language trading command",
    description="Parses user commands (e.g. 'Buy 20 shares of NVDA') into actionable intent.",
)
async def parse_command(req: CommandParseRequest) -> CommandParseResponse:
    return await parse_trade_command(req)
