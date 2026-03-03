"""Seasons Router."""

from fastapi import APIRouter, HTTPException

from services.seasons import get_seasons

router = APIRouter(prefix="/times", tags=["Times"])


@router.get("/seasons", summary="All seasons")
async def seasons():
    """Returns all Europapark seasons with dates."""
    entries = await get_seasons()
    
    if not entries:
        raise HTTPException(status_code=503, detail="No data available")
    
    return {
        "count": len(entries),
        "seasons": [e.model_dump(exclude_none=True) for e in entries]
    }
