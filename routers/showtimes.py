"""Showtimes Router."""

from fastapi import APIRouter, HTTPException

from services.showtimes import get_processed_showtimes, get_showtime_by_id

router = APIRouter(prefix="/times", tags=["Times"])


@router.get("/showtimes", summary="All show times")
async def showtimes():
    """Returns show times for today and tomorrow."""
    entries = await get_processed_showtimes()
    
    if not entries:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    
    return {
        "count": len(entries),
        "showtimes": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/showtimes/{show_id}", summary="Show times by ID")
async def showtime_by_id(show_id: int):
    """Returns show times for a specific show."""
    entry = await get_showtime_by_id(show_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Show not found")
    
    return entry.model_dump(exclude_none=True)
