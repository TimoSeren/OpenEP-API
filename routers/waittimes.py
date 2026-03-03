"""Waittimes Router."""

from fastapi import APIRouter, HTTPException

from services.waittimes import get_processed_waittimes, get_waittime_by_id

router = APIRouter(prefix="/times", tags=["Times"])


@router.get("/waittimes", summary="All wait times")
async def waittimes():
    """Returns current wait times for all attractions with status."""
    entries = await get_processed_waittimes()
    
    if not entries:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    
    return {
        "count": len(entries),
        "waittimes": [e.model_dump() for e in entries]
    }


@router.get("/waittimes/{attraction_id}", summary="Wait time by ID")
async def waittime_by_id(attraction_id: int):
    """Returns wait time for a specific attraction."""
    entry = await get_waittime_by_id(attraction_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Attraction not found")
    
    return entry.model_dump()
