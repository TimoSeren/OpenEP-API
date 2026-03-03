"""Services Router."""

from fastapi import APIRouter, HTTPException

from services.pois import get_all_services, get_service_by_id

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/services", summary="All services")
async def services():
    """Returns all service facilities (restrooms, info, first aid)."""
    entries = await get_all_services()
    
    if not entries:
        raise HTTPException(status_code=503, detail="No data available")
    
    return {
        "count": len(entries),
        "services": [e.model_dump(exclude_none=True) for e in entries]
    }


@router.get("/services/{service_id}", summary="Service details")
async def service_info(service_id: int):
    """Returns service facility details."""
    info = await get_service_by_id(service_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return info.model_dump(exclude_none=True)
