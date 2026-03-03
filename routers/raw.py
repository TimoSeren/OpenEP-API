"""Raw API Router."""

from fastapi import APIRouter, HTTPException

from services.europapark_api import (
    get_waiting_times,
    get_pois,
    get_seasons,
    get_opening_times,
    get_show_times
)

router = APIRouter(prefix="/raw", tags=["Raw"])


@router.get("/waittimes", summary="Raw wait times")
async def raw_waittimes():
    """Returns unprocessed wait times from Europapark API."""
    try:
        return await get_waiting_times()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pois", summary="Raw POIs")
async def raw_pois():
    """Returns unprocessed POI data from Europapark API."""
    try:
        return await get_pois()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seasons", summary="Raw seasons")
async def raw_seasons():
    """Returns unprocessed season data from Europapark API."""
    try:
        return await get_seasons()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openingtimes", summary="Raw opening times")
async def raw_opening_times():
    """Returns unprocessed opening times from Europapark API."""
    try:
        return await get_opening_times()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/showtimes", summary="Raw show times")
async def raw_show_times():
    """Returns unprocessed show times from Europapark API."""
    try:
        return await get_show_times()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
