"""Market read endpoints (T039 completion): candles + latest indicators.

API-key protected, read-only. Symbols carry a slash (e.g. BTC/USDT), so the path is greedy.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.api.deps import get_session, require_api_key
from aegis.domain import Timeframe
from aegis.persistence.repositories.market import MarketRepository

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/candles/{symbol:path}")
async def get_candles(
    symbol: str,
    tf: Timeframe = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    candles = await MarketRepository(session).get_candles(symbol, tf)
    return [c.model_dump(mode="json") for c in candles]


@router.get("/indicators/{symbol:path}")
async def get_indicators(
    symbol: str,
    tf: Timeframe = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    indicators = await MarketRepository(session).get_latest_indicators(symbol, tf)
    if indicators is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no indicators yet")
    return indicators.model_dump(mode="json")
