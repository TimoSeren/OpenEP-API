"""
Seasons Service.
Processes season data from cache (Europapark only).
"""

from typing import Optional

from pydantic import BaseModel

from services.cache import get_cache_service, CACHE_KEYS


class SeasonInfo(BaseModel):
    """Season information."""
    id: int
    saison: Optional[str] = None
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


async def get_seasons() -> list[SeasonInfo]:
    """Get all Europapark seasons."""
    cache = get_cache_service()
    data = await cache.load(CACHE_KEYS["seasons"])
    
    if not data or "data" not in data:
        return []
    
    results = []
    for season in data["data"]:
        scopes = season.get("scopes", [])
        
        # Europapark only
        if "europapark" not in scopes:
            continue
        
        start = season.get("startAt")
        end = season.get("endAt")
        
        # Icon from iconSvg.reference
        icon = None
        if season.get("iconSvg") and season["iconSvg"].get("reference"):
            icon = season["iconSvg"]["reference"]
        
        results.append(SeasonInfo(
            id=season["id"],
            saison=season.get("theme"),
            name=season.get("name", "Unknown"),
            description=season.get("description"),
            icon=icon,
            start=start[:10] if start else None,
            end=end[:10] if end else None
        ))
    
    return results
