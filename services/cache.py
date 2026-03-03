"""
Cache-Service für Europapark API-Daten.
Speichert Daten in der Datenbank und aktualisiert sie periodisch.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select

from database import CacheModel, get_session
from services.europapark_api import (
    get_waiting_times,
    get_pois,
    get_seasons,
    get_opening_times,
    get_show_times
)

logger = logging.getLogger(__name__)

CACHE_KEYS = {
    "waittimes": "waittimes",
    "showtimes": "showtimes",
    "pois": "pois",
    "seasons": "seasons",
    "openingtimes": "openingtimes"
}


class CacheService:
    """Verwaltet den Cache für API-Daten."""
    
    def __init__(self):
        self._refresh_task_5min: Optional[asyncio.Task] = None
        self._refresh_task_daily: Optional[asyncio.Task] = None
    
    async def save(self, key: str, data: Any) -> None:
        """Speichert Daten im Cache."""
        async with get_session() as session:
            result = await session.execute(
                select(CacheModel).where(CacheModel.key == key)
            )
            existing = result.scalar_one_or_none()
            
            json_data = json.dumps(data, ensure_ascii=False)
            
            if existing:
                existing.data = json_data
                existing.updated_at = datetime.now()
            else:
                session.add(CacheModel(
                    key=key,
                    data=json_data,
                    updated_at=datetime.now()
                ))
            
            await session.commit()
            logger.debug(f"Cache gespeichert: {key}")
    
    async def load(self, key: str) -> Optional[dict]:
        """Lädt Daten aus dem Cache."""
        async with get_session() as session:
            result = await session.execute(
                select(CacheModel).where(CacheModel.key == key)
            )
            cached = result.scalar_one_or_none()
            
            if cached:
                return {
                    "data": json.loads(cached.data),
                    "updated_at": cached.updated_at.isoformat()
                }
            return None
    
    async def refresh_waittimes(self) -> None:
        """Aktualisiert Wartezeiten."""
        try:
            data = await get_waiting_times()
            await self.save(CACHE_KEYS["waittimes"], data)
            logger.info("Wartezeiten aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Wartezeiten: {e}")
    
    async def refresh_showtimes(self) -> None:
        """Aktualisiert Showzeiten."""
        try:
            data = await get_show_times()
            await self.save(CACHE_KEYS["showtimes"], data)
            logger.info("Showzeiten aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Showzeiten: {e}")
    
    async def refresh_pois(self) -> None:
        """Aktualisiert POIs."""
        try:
            data = await get_pois()
            await self.save(CACHE_KEYS["pois"], data)
            logger.info("POIs aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der POIs: {e}")
    
    async def refresh_seasons(self) -> None:
        """Aktualisiert Seasons."""
        try:
            data = await get_seasons()
            await self.save(CACHE_KEYS["seasons"], data)
            logger.info("Seasons aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Seasons: {e}")
    
    async def refresh_openingtimes(self) -> None:
        """Aktualisiert Öffnungszeiten."""
        try:
            data = await get_opening_times()
            await self.save(CACHE_KEYS["openingtimes"], data)
            logger.info("Öffnungszeiten aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Öffnungszeiten: {e}")
    
    async def refresh_all_5min(self) -> None:
        """Aktualisiert alle 5-Minuten-Daten (parallel)."""
        await asyncio.gather(
            self.refresh_waittimes(),
            self.refresh_showtimes()
        )
    
    async def refresh_all_daily(self) -> None:
        """Aktualisiert alle täglichen Daten (parallel)."""
        await asyncio.gather(
            self.refresh_pois(),
            self.refresh_seasons(),
            self.refresh_openingtimes()
        )
    
    async def _loop_5min(self) -> None:
        """5-Minuten-Refresh-Loop."""
        while True:
            try:
                await self.refresh_all_5min()
                await asyncio.sleep(300)  # 5 Minuten
            except asyncio.CancelledError:
                logger.info("5-Minuten Cache Loop beendet.")
                break
            except Exception as e:
                logger.error(f"Fehler im 5-Minuten Cache Loop: {e}")
                await asyncio.sleep(60)
    
    async def _loop_daily(self) -> None:
        """Täglicher Refresh-Loop."""
        while True:
            try:
                await self.refresh_all_daily()
                await asyncio.sleep(86400)  # 24 Stunden
            except asyncio.CancelledError:
                logger.info("Täglicher Cache Loop beendet.")
                break
            except Exception as e:
                logger.error(f"Fehler im täglichen Cache Loop: {e}")
                await asyncio.sleep(3600)
    
    def start(self) -> None:
        """Startet die Cache-Scheduler."""
        if self._refresh_task_5min is None or self._refresh_task_5min.done():
            self._refresh_task_5min = asyncio.create_task(self._loop_5min())
            logger.info("5-Minuten Cache Scheduler gestartet.")
        
        if self._refresh_task_daily is None or self._refresh_task_daily.done():
            self._refresh_task_daily = asyncio.create_task(self._loop_daily())
            logger.info("Täglicher Cache Scheduler gestartet.")
    
    def stop(self) -> None:
        """Stoppt die Cache-Scheduler."""
        if self._refresh_task_5min:
            self._refresh_task_5min.cancel()
            self._refresh_task_5min = None
        
        if self._refresh_task_daily:
            self._refresh_task_daily.cancel()
            self._refresh_task_daily = None
        
        logger.info("Cache Scheduler gestoppt.")


_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
