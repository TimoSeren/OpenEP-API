"""Shows Router."""

from fastapi import APIRouter, HTTPException

from services.shows import get_show_info, get_all_shows

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/shows", summary="All shows")
async def shows():
    """Returns all shows with locations and times."""
    entries = await get_all_shows()
    
    if not entries:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    
    return {
        "count": len(entries),
        "shows": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/shows/{show_id}", summary="Show details")
async def show_info(show_id: int):
    """Returns full show details including location, duration, and times."""
    info = await get_show_info(show_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Show not found")
    
    return info.model_dump(exclude_none=True)
