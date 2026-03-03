"""
Firebase Health Check Service.
Überprüft die Verbindung zur Firebase API.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from config import Settings, get_settings, refresh_settings

logger = logging.getLogger(__name__)


class FirebaseHealthStatus:
    """Speichert den aktuellen Firebase Health Status."""

    def __init__(self):
        self.is_healthy: bool = False
        self.last_check: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.response_time_ms: Optional[float] = None

    def to_dict(self) -> dict:
        """Konvertiert den Status zu einem Dictionary."""
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_error": self.last_error,
            "response_time_ms": self.response_time_ms,
        }


firebase_status = FirebaseHealthStatus()


async def check_firebase_health(settings: Optional[Settings] = None) -> FirebaseHealthStatus:
    """
    Führt einen Health-Check der Firebase API durch.
    Prüft die Erreichbarkeit durch einen Test-Request.
    """
    if settings is None:
        settings = get_settings()

    firebase_status.last_check = datetime.now()
    
    try:
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            firebase_url = (
                f"https://identitytoolkit.googleapis.com/v1/accounts:signUp"
                f"?key={settings.fb_api_key}"
            )
            
            response = await client.post(
                firebase_url,
                json={"returnSecureToken": False},
                headers={"Content-Type": "application/json"},
            )
            
            end_time = datetime.now()
            firebase_status.response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Status 400 ist OK - API ist erreichbar
            if response.status_code in [200, 400]:
                firebase_status.is_healthy = True
                firebase_status.last_error = None
                logger.info(
                    f"Firebase Health Check erfolgreich. "
                    f"Response Time: {firebase_status.response_time_ms:.2f}ms"
                )
            else:
                firebase_status.is_healthy = False
                firebase_status.last_error = f"Unexpected status code: {response.status_code}"
                logger.warning(f"Firebase Health Check fehlgeschlagen. Status: {response.status_code}")
                
    except httpx.TimeoutException as e:
        firebase_status.is_healthy = False
        firebase_status.last_error = f"Timeout: {str(e)}"
        firebase_status.response_time_ms = None
        logger.error(f"Firebase Health Check Timeout: {e}")
        
    except httpx.RequestError as e:
        firebase_status.is_healthy = False
        firebase_status.last_error = f"Request Error: {str(e)}"
        firebase_status.response_time_ms = None
        logger.error(f"Firebase Health Check Request Error: {e}")
        
    except Exception as e:
        firebase_status.is_healthy = False
        firebase_status.last_error = f"Unexpected Error: {str(e)}"
        firebase_status.response_time_ms = None
        logger.error(f"Firebase Health Check Unexpected Error: {e}")

    return firebase_status


async def check_and_refresh_secrets() -> tuple[FirebaseHealthStatus, bool]:
    """
    Führt einen Health-Check durch und aktualisiert die Secrets falls nötig.
    """
    logger.info("Starte täglichen Health-Check mit Secret-Aktualisierung...")
    
    old_settings = get_settings()
    new_settings = refresh_settings()
    
    secrets_changed = (
        old_settings.api_username != new_settings.api_username or
        old_settings.api_password != new_settings.api_password or
        old_settings.fb_api_key != new_settings.fb_api_key
    )
    
    if secrets_changed:
        logger.info("Secrets wurden aktualisiert.")
    
    status = await check_firebase_health(new_settings)
    return status, secrets_changed


def get_firebase_status() -> FirebaseHealthStatus:
    """Gibt den aktuellen Firebase Health Status zurück."""
    return firebase_status
