"""Shops Router."""

from fastapi import APIRouter, HTTPException

from services.pois import get_all_shops, get_shop_by_id

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/shops", summary="All shops")
async def shops():
    """Returns all shops with locations."""
    entries = await get_all_shops()
    
    if not entries:
        raise HTTPException(status_code=503, detail="No data available")
    
    return {
        "count": len(entries),
        "shops": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/shops/{shop_id}", summary="Shop details")
async def shop_info(shop_id: int):
    """Returns shop details."""
    info = await get_shop_by_id(shop_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return info.model_dump(exclude_none=True)
