"""
Waittimes Service.
Processes wait times and links them with POI data.
"""

import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from services.cache import get_cache_service, CACHE_KEYS

logger = logging.getLogger(__name__)


class AttractionStatus(str, Enum):
    """Status of an attraction."""
    OPERATIONAL = "operational"
    CLOSED = "closed"
    REFURBISHMENT = "refurbishment"
    WEATHER = "weather"
    ICE = "ice"
    DOWN = "down"
    VQUEUE_TEMP_FULL = "vqueue_temporarily_full"
    VQUEUE_FULL = "vqueue_full"
    UNKNOWN = "unknown"


class WaitTimeEntry(BaseModel):
    """Wait time entry."""
    id: int
    name: str
    time: Optional[int]
    status: AttractionStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def get_status_from_time(time_value: int) -> tuple[AttractionStatus, Optional[int]]:
    """
    Determine status and cleaned wait time from time value.
    
    Time codes:
    - <= 90: Wait time in minutes
    - 91: 90+ minutes
    - 222: Maintenance/Refurbishment
    - 333: Closed
    - 444: Weather
    - 555: Ice
    - 666: Virtual queue temporarily full
    - 777: Virtual queue full
    - 999: Down/Technical issues
    """
    if time_value <= 90:
        return AttractionStatus.OPERATIONAL, time_value
    elif time_value == 91:
        return AttractionStatus.OPERATIONAL, 90  # 90+ minutes
    elif time_value == 222:
        return AttractionStatus.REFURBISHMENT, None
    elif time_value == 333:
        return AttractionStatus.CLOSED, None
    elif time_value == 444:
        return AttractionStatus.WEATHER, None
    elif time_value == 555:
        return AttractionStatus.ICE, None
    elif time_value == 666:
        return AttractionStatus.VQUEUE_TEMP_FULL, None
    elif time_value == 777:
        return AttractionStatus.VQUEUE_FULL, None
    elif time_value == 999:
        return AttractionStatus.DOWN, None
    else:
        return AttractionStatus.UNKNOWN, None


async def get_poi_name_map() -> dict[int, dict]:
    """Create a mapping from POI code to POI data."""
    cache = get_cache_service()
    pois_data = await cache.load(CACHE_KEYS["pois"])
    
    if not pois_data or "data" not in pois_data:
        return {}
    
    poi_map = {}
    for poi in pois_data["data"].get("pois", []):
        code = poi.get("code")
        scopes = poi.get("scopes", [])
        
        # Europapark POIs only (no Rulantica)
        if code and "europapark" in scopes:
            poi_map[code] = {
                "id": poi.get("id"),
                "name": poi.get("name", "Unknown"),
                "type": poi.get("type"),
                "latitude": poi.get("latitude"),
                "longitude": poi.get("longitude"),
            }
    
    return poi_map


async def get_processed_waittimes() -> list[WaitTimeEntry]:
    """Get processed wait times with names and status."""
    cache = get_cache_service()
    
    waittimes_data = await cache.load(CACHE_KEYS["waittimes"])
    if not waittimes_data or "data" not in waittimes_data:
        return []
    
    poi_map = await get_poi_name_map()
    
    results = []
    for entry in waittimes_data["data"]:
        code = entry.get("code")
        time_value = entry.get("time", 0)
        
        poi_info = poi_map.get(code, {})
        poi_id = poi_info.get("id")
        poi_name = poi_info.get("name", f"Attraction #{code}")
        
        # Only attractions with known ID
        if poi_id is None:
            continue
        
        status, clean_time = get_status_from_time(time_value)
        
        results.append(WaitTimeEntry(
            id=poi_id,
            name=poi_name,
            time=clean_time,
            status=status,
            latitude=poi_info.get("latitude"),
            longitude=poi_info.get("longitude")
        ))
    
    return results


async def get_waittime_by_id(attraction_id: int) -> Optional[WaitTimeEntry]:
    """Get wait time for a specific attraction."""
    waittimes = await get_processed_waittimes()
    
    for entry in waittimes:
        if entry.id == attraction_id:
            return entry
    
    return None
