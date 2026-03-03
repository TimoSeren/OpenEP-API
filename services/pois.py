"""POI Service."""

import logging
from typing import Optional

from pydantic import BaseModel

from services.cache import get_cache_service, CACHE_KEYS

logger = logging.getLogger(__name__)


class Location(BaseModel):
    latitude: float
    longitude: float


class ImageUrls(BaseModel):
    small: Optional[str] = None
    medium: Optional[str] = None


class POIListItem(BaseModel):
    """Compact POI for list view."""
    id: int
    name: str
    type: str
    area_id: Optional[int] = None
    location: Optional[Location] = None
    icon: Optional[str] = None


class POIInfo(BaseModel):
    """Full POI information."""
    id: int
    name: str
    description: Optional[str] = None
    type: str
    area_id: Optional[int] = None
    location: Optional[Location] = None
    image: Optional[ImageUrls] = None
    icon: Optional[str] = None


def extract_image_urls(image_data: Optional[dict]) -> Optional[ImageUrls]:
    if not image_data:
        return None
    return ImageUrls(small=image_data.get("small"), medium=image_data.get("medium"))


def extract_location(poi: dict) -> Optional[Location]:
    if poi.get("latitude") and poi.get("longitude"):
        return Location(latitude=poi["latitude"], longitude=poi["longitude"])
    return None


async def get_pois_by_type(poi_type: str) -> list[POIListItem]:
    """Get all POIs of a type (compact list)."""
    cache = get_cache_service()
    pois_data = await cache.load(CACHE_KEYS["pois"])
    
    if not pois_data or "data" not in pois_data:
        return []
    
    results = []
    for poi in pois_data["data"].get("pois", []):
        scopes = poi.get("scopes", [])
        if poi.get("type") != poi_type or "europapark" not in scopes:
            continue
        
        results.append(POIListItem(
            id=poi["id"],
            name=poi.get("name", "Unknown"),
            type=poi.get("type"),
            area_id=poi.get("areaId"),
            location=extract_location(poi),
            icon=poi.get("icon", {}).get("small") if poi.get("icon") else None
        ))
    
    return results


async def get_poi_by_id_and_type(poi_id: int, poi_type: str) -> Optional[POIInfo]:
    """Get full POI details by ID and type."""
    cache = get_cache_service()
    pois_data = await cache.load(CACHE_KEYS["pois"])
    
    if not pois_data or "data" not in pois_data:
        return None
    
    for poi in pois_data["data"].get("pois", []):
        scopes = poi.get("scopes", [])
        if (poi.get("id") == poi_id and 
            poi.get("type") == poi_type and 
            "europapark" in scopes):
            return POIInfo(
                id=poi["id"],
                name=poi.get("name", "Unknown"),
                description=poi.get("excerpt"),
                type=poi.get("type"),
                area_id=poi.get("areaId"),
                location=extract_location(poi),
                image=extract_image_urls(poi.get("image")),
                icon=poi.get("icon", {}).get("small") if poi.get("icon") else None
            )
    return None


async def get_all_shops() -> list[POIListItem]:
    return await get_pois_by_type("shopping")


async def get_shop_by_id(shop_id: int) -> Optional[POIInfo]:
    return await get_poi_by_id_and_type(shop_id, "shopping")


async def get_all_restaurants() -> list[POIListItem]:
    return await get_pois_by_type("gastronomy")


async def get_restaurant_by_id(restaurant_id: int) -> Optional[POIInfo]:
    return await get_poi_by_id_and_type(restaurant_id, "gastronomy")


async def get_all_services() -> list[POIListItem]:
    return await get_pois_by_type("service")


async def get_service_by_id(service_id: int) -> Optional[POIInfo]:
    return await get_poi_by_id_and_type(service_id, "service")
