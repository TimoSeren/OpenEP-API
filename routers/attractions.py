"""Attractions Router."""

from fastapi import APIRouter, HTTPException

from services.attractions import get_attraction_info, get_all_attractions

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/attractions", summary="All attractions")
async def attractions():
    """Returns all attractions with basic info and wait times."""
    entries = await get_all_attractions()
    
    if not entries:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    
    return {
        "count": len(entries),
        "attractions": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/attractions/{attraction_id}", summary="Attraction details")
async def attraction_info(attraction_id: int):
    """Returns full details including requirements, stress levels, and images."""
    info = await get_attraction_info(attraction_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Attraction not found")
    
    return info.model_dump(exclude_none=True)
