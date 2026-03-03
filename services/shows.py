"""Shows Service."""

import logging
from typing import Optional

from pydantic import BaseModel

from services.cache import get_cache_service, CACHE_KEYS
from services.showtimes import get_showtime_by_id, ShowTimeEntry

logger = logging.getLogger(__name__)


class Location(BaseModel):
    latitude: float
    longitude: float


class ImageUrls(BaseModel):
    small: Optional[str] = None
    medium: Optional[str] = None


class ShowListItem(BaseModel):
    """Compact show for list view."""
    id: int
    name: str
    type: str = "show"
    area_id: Optional[int] = None
    location: Optional[Location] = None
    icon: Optional[str] = None


class ShowInfo(BaseModel):
    """Full show information."""
    id: int
    name: str
    description: Optional[str] = None
    location_name: Optional[str] = None
    location: Optional[Location] = None
    duration: Optional[int] = None
    image: Optional[ImageUrls] = None
    icon: Optional[str] = None
    showtimes: Optional[ShowTimeEntry] = None


def extract_image_urls(image_data: Optional[dict]) -> Optional[ImageUrls]:
    if not image_data:
        return None
    return ImageUrls(small=image_data.get("small"), medium=image_data.get("medium"))


def extract_location(poi: dict) -> Optional[Location]:
    if poi.get("latitude") and poi.get("longitude"):
        return Location(latitude=poi["latitude"], longitude=poi["longitude"])
    return None


async def get_all_shows_from_pois() -> list[dict]:
    """Get all shows from POI data."""
    cache = get_cache_service()
    pois_data = await cache.load(CACHE_KEYS["pois"])
    
    if not pois_data or "data" not in pois_data:
        return []
    
    shows = []
    for poi in pois_data["data"].get("pois", []):
        scopes = poi.get("scopes", [])
        if "europapark" not in scopes:
            continue
        
        for show in poi.get("shows", []):
            shows.append({"show": show, "location_poi": poi})
    
    return shows


async def get_show_by_id(show_id: int) -> Optional[dict]:
    """Get raw show data by ID."""
    all_shows = await get_all_shows_from_pois()
    for item in all_shows:
        if item["show"].get("id") == show_id:
            return item
    return None


async def get_show_info(show_id: int) -> Optional[ShowInfo]:
    """Get full show details."""
    item = await get_show_by_id(show_id)
    if not item:
        return None
    
    show = item["show"]
    location_poi = item["location_poi"]
    showtimes = await get_showtime_by_id(show_id)
    
    return ShowInfo(
        id=show["id"],
        name=show.get("name", "Unknown"),
        description=show.get("excerpt"),
        location_name=location_poi.get("name"),
        location=extract_location(location_poi),
        duration=show.get("duration"),
        image=extract_image_urls(show.get("image")),
        icon=show.get("icon", {}).get("small") if show.get("icon") else None,
        showtimes=showtimes
    )


async def get_all_shows() -> list[ShowListItem]:
    """Get all shows (compact list)."""
    all_shows = await get_all_shows_from_pois()
    
    results = []
    for item in all_shows:
        show = item["show"]
        location_poi = item["location_poi"]
        
        results.append(ShowListItem(
            id=show["id"],
            name=show.get("name", "Unknown"),
            type="show",
            area_id=location_poi.get("areaId"),
            location=extract_location(location_poi),
            icon=show.get("icon", {}).get("small") if show.get("icon") else None
        ))
    
    return results
