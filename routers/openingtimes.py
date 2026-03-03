"""Openingtimes Router."""

from fastapi import APIRouter, HTTPException

from services.openingtimes import get_opening_times

router = APIRouter(prefix="/times", tags=["Times"])


@router.get("/openingtimes", summary="Opening hours")
async def openingtimes():
    """Returns current opening hours (today, tomorrow, next)."""
    info = await get_opening_times()
    
    if not info:
        raise HTTPException(status_code=503, detail="No data available")
    
    return info.model_dump(exclude_none=True)
