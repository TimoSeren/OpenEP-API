"""
Authentifizierungs-Service für OAuth2 Token Management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from config import get_settings
from services.firebase_config import get_firebase_config_service
from services.token_storage import TokenData, TokenStorage, get_token_storage

logger = logging.getLogger(__name__)


class AuthService:
    """Verwaltet die OAuth2-Authentifizierung."""
    
    REFRESH_BUFFER_SECONDS = 600  # 10 Minuten vor Ablauf erneuern
    MIN_REFRESH_INTERVAL_SECONDS = 60
    
    def __init__(self):
        self.settings = get_settings()
        self.token_storage = get_token_storage()
        self.firebase_config = get_firebase_config_service()
        
        self._current_token: Optional[TokenData] = None
        self._refresh_task: Optional[asyncio.Task] = None
    
    @property
    def is_authenticated(self) -> bool:
        if self._current_token is None:
            return False
        return not self._current_token.is_expired(self.REFRESH_BUFFER_SECONDS)
    
    @property
    def access_token(self) -> Optional[str]:
        if self._current_token and not self._current_token.is_expired():
            return self._current_token.access_token
        return None
    
    def get_auth_header(self) -> dict:
        """Gibt den jwtauthorization Header für API-Requests zurück."""
        if not self.access_token:
            raise RuntimeError("Nicht authentifiziert.")
        return {"jwtauthorization": f"Bearer {self.access_token}"}
    
    async def initialize(self) -> bool:
        logger.info("Initialisiere Authentifizierung...")
        
        saved_token = await self.token_storage.load()
        
        if saved_token and not saved_token.is_expired(self.REFRESH_BUFFER_SECONDS):
            logger.info("Gültiger gespeicherter Token gefunden.")
            self._current_token = saved_token
            self._start_refresh_scheduler()
            return True
        
        try:
            await self._request_new_token()
            self._start_refresh_scheduler()
            return True
        except Exception as e:
            logger.error(f"Token-Anforderung fehlgeschlagen: {e}")
            return False
    
    async def _request_new_token(self) -> None:
        logger.info("Fordere neuen OAuth2 Token an...")
        
        credentials = await self.firebase_config.get_decrypted_credentials()
        logger.info(f"Verwende client_id: {credentials['username'][:8]}...")
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": credentials["username"],
            "client_secret": credentials["password"]
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"EuropaParkApp/{self.settings.app_version} (Android)"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.settings.auth_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Token Request fehlgeschlagen: {response.status_code} - {response.text}")
            
            data = response.json()
        
        expires_in = data.get("expires_in", 86400)
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        self._current_token = TokenData(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at
        )
        
        await self.token_storage.save(self._current_token)
        logger.info(f"Token erhalten. Gültig bis: {expires_at}")
    
    def _start_refresh_scheduler(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._refresh_loop())
        logger.info("Token Refresh Scheduler gestartet.")
    
    def _stop_refresh_scheduler(self) -> None:
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None
            logger.info("Token Refresh Scheduler gestoppt.")
    
    async def _refresh_loop(self) -> None:
        while True:
            try:
                if self._current_token is None:
                    await asyncio.sleep(60)
                    continue
                
                time_until_expiry = (
                    self._current_token.expires_at - datetime.now()
                ).total_seconds()
                
                sleep_time = max(
                    time_until_expiry - self.REFRESH_BUFFER_SECONDS,
                    self.MIN_REFRESH_INTERVAL_SECONDS
                )
                
                await asyncio.sleep(sleep_time)
                await self._request_new_token()
                    
            except asyncio.CancelledError:
                logger.info("Token Refresh Loop beendet.")
                break
            except Exception as e:
                logger.error(f"Fehler im Token Refresh: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self) -> None:
        self._stop_refresh_scheduler()
        logger.info("Auth-Service heruntergefahren.")
    
    def get_status(self) -> dict:
        if self._current_token is None:
            return {"authenticated": False, "expires_at": None}
        
        return {
            "authenticated": self.is_authenticated,
            "expires_at": self._current_token.expires_at.isoformat(),
            "created_at": self._current_token.created_at.isoformat()
        }


_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


async def initialize_auth() -> bool:
    return await get_auth_service().initialize()


async def shutdown_auth() -> None:
    global _auth_service
    if _auth_service:
        await _auth_service.shutdown()
