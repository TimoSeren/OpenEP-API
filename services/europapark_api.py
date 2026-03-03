"""
Europapark API Client.
Universelle Funktion für API-Requests zur Europapark API.
"""

import logging
from typing import Any, Optional

import httpx

from config import get_settings
from services.auth import get_auth_service

logger = logging.getLogger(__name__)

API_BASE = "https://tickets.mackinternational.de"


async def europapark_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[dict] = None,
    json_data: Optional[dict] = None
) -> Any:
    """
    Führt einen Request zur Europapark API durch.
    
    Args:
        endpoint: API-Endpoint (z.B. "/api/v2/waiting-times")
        method: HTTP-Methode
        params: Query-Parameter
        json_data: JSON-Body für POST-Requests
    
    Returns:
        JSON-Response der API
    
    Raises:
        RuntimeError: Bei Authentifizierungs- oder API-Fehlern
    """
    settings = get_settings()
    auth_service = get_auth_service()
    
    if not auth_service.is_authenticated:
        raise RuntimeError("Nicht authentifiziert")
    
    url = f"{settings.api_base}{endpoint}"
    
    headers = {
        **auth_service.get_auth_header(),
        "Accept": "application/json",
        "Accept-Language": "de",
        "User-Agent": f"EuropaParkApp/{settings.app_version} (Android)"
    }
    
    logger.info(f"API Request: {method} {endpoint}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers
        )
        
        if response.status_code == 401:
            logger.warning("Token ungültig (401). Fordere neuen Token an...")
            await auth_service._request_new_token()
            
            # Retry mit neuem Token
            headers = {
                **auth_service.get_auth_header(),
                "Accept": "application/json",
                "Accept-Language": "de",
                "User-Agent": f"EuropaParkApp/{settings.app_version} (Android)"
            }
            
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers
            )
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            raise RuntimeError(f"API Error: {response.status_code}")
        
        return response.json()


async def get_waiting_times() -> dict:
    """Ruft die aktuellen Wartezeiten ab."""
    return await europapark_request("/api/v2/waiting-times")


async def get_pois() -> dict:
    """Ruft alle POIs (Attraktionen) ab."""
    return await europapark_request("/api/v2/poi-group", params={"status": "live"})


async def get_seasons() -> dict:
    """Ruft Kalender/Saison-Daten ab."""
    return await europapark_request("/api/v2/seasons", params={"status": "live"})


async def get_opening_times() -> dict:
    """Ruft die aktuellen Öffnungszeiten ab."""
    return await europapark_request("/api/v2/season-opentime-details/europapark")


async def get_show_times() -> dict:
    """Ruft die Showzeiten ab."""
    return await europapark_request("/api/v2/show-times", params={"status": "live"})
