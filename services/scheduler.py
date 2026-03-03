"""
Scheduler Service für periodische Tasks.
Führt den täglichen Firebase Health-Check durch.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_scheduler_task: Optional[asyncio.Task] = None


def _calculate_next_run(target_time: time) -> datetime:
    """Berechnet den nächsten Ausführungszeitpunkt."""
    now = datetime.now()
    next_run = datetime.combine(now.date(), target_time)
    
    if now.time() >= target_time:
        next_run += timedelta(days=1)
    
    return next_run


async def daily_health_check_loop():
    """
    Endlosschleife die den täglichen Health-Check durchführt.
    Läuft jeden Tag um 03:00 Uhr.
    """
    from services.firebase_health import check_and_refresh_secrets
    
    target_time = time(hour=3, minute=0, second=0)
    
    while True:
        try:
            next_run = _calculate_next_run(target_time)
            sleep_seconds = (next_run - datetime.now()).total_seconds()
            
            logger.info(
                f"Nächster Health-Check geplant für {next_run.isoformat()}. "
                f"Warte {sleep_seconds / 3600:.2f} Stunden."
            )
            
            await asyncio.sleep(sleep_seconds)
            
            logger.info("Starte geplanten täglichen Health-Check...")
            status, secrets_refreshed = await check_and_refresh_secrets()
            
            if status.is_healthy:
                logger.info("Täglicher Health-Check erfolgreich.")
            else:
                logger.warning(f"Täglicher Health-Check fehlgeschlagen: {status.last_error}")
            
            if secrets_refreshed:
                logger.info("Secrets wurden während des Health-Checks aktualisiert.")
                
        except asyncio.CancelledError:
            logger.info("Scheduler wird beendet...")
            break
        except Exception as e:
            logger.error(f"Fehler im Scheduler: {e}")
            await asyncio.sleep(3600)


def start_scheduler():
    """Startet den Scheduler als Background-Task."""
    global _scheduler_task
    
    if _scheduler_task is not None and not _scheduler_task.done():
        logger.warning("Scheduler läuft bereits.")
        return
    
    _scheduler_task = asyncio.create_task(daily_health_check_loop())
    logger.info("Scheduler gestartet.")


def stop_scheduler():
    """Stoppt den Scheduler."""
    global _scheduler_task
    
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        _scheduler_task = None
        logger.info("Scheduler gestoppt.")
