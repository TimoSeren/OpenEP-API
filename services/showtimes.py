"""
Showtimes Service.
Processes show times and links them with POI data.
"""

import logging
from typing import Optional

from pydantic import BaseModel

from services.cache import get_cache_service, CACHE_KEYS

logger = logging.getLogger(__name__)


class Location(BaseModel):
    """Location."""
    latitude: float
    longitude: float


class ShowTimeEntry(BaseModel):
    """Show time entry."""
    id: int
    name: str
    location: Optional[Location] = None
    times_today: list[str]
    times_tomorrow: list[str]


async def get_show_info_map() -> dict[int, dict]:
    """
    Create a mapping from show ID to show information from POI data.
    Shows are nested under showlocation POIs.
    """
    cache = get_cache_service()
    pois_data = await cache.load(CACHE_KEYS["pois"])
    
    if not pois_data or "data" not in pois_data:
        return {}
    
    show_map = {}
    for poi in pois_data["data"].get("pois", []):
        scopes = poi.get("scopes", [])
        
        # Europapark only (no Rulantica)
        if "europapark" not in scopes:
            continue
        
        shows = poi.get("shows", [])
        for show in shows:
            show_id = show.get("id")
            if show_id:
                show_map[show_id] = {
                    "name": show.get("name", "Unknown"),
                    "latitude": poi.get("latitude"),
                    "longitude": poi.get("longitude"),
                }
    
    return show_map


async def get_processed_showtimes() -> list[ShowTimeEntry]:
    """Get processed show times with names and location."""
    cache = get_cache_service()
    
    showtimes_data = await cache.load(CACHE_KEYS["showtimes"])
    if not showtimes_data or "data" not in showtimes_data:
        return []
    
    show_map = await get_show_info_map()
    
    results = []
    for entry in showtimes_data["data"]:
        show_id = entry.get("showId")
        
        show_info = show_map.get(show_id)
        if not show_info:
            continue
        
        location = None
        if show_info.get("latitude") and show_info.get("longitude"):
            location = Location(
                latitude=show_info["latitude"],
                longitude=show_info["longitude"]
            )
        
        results.append(ShowTimeEntry(
            id=show_id,
            name=show_info["name"],
            location=location,
            times_today=entry.get("today", []),
            times_tomorrow=entry.get("tomorrow", [])
        ))
    
    return results


async def get_showtime_by_id(show_id: int) -> Optional[ShowTimeEntry]:
    """Get show times for a specific show."""
    showtimes = await get_processed_showtimes()
    
    for entry in showtimes:
        if entry.id == show_id:
            return entry
    
    return None
