"""Restaurants Router."""

from fastapi import APIRouter, HTTPException

from services.pois import get_all_restaurants, get_restaurant_by_id

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/restaurants", summary="All restaurants")
async def restaurants():
    """Returns all restaurants and gastronomy with locations."""
    entries = await get_all_restaurants()
    
    if not entries:
        raise HTTPException(status_code=503, detail="No data available")
    
    return {
        "count": len(entries),
        "restaurants": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/restaurants/{restaurant_id}", summary="Restaurant details")
async def restaurant_info(restaurant_id: int):
    """Returns restaurant details."""
    info = await get_restaurant_by_id(restaurant_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return info.model_dump(exclude_none=True)
