"""
Europapark API Server
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_database, close_database
from routers.attractions import router as attractions_router
from routers.openingtimes import router as openingtimes_router
from routers.raw import router as raw_router
from routers.restaurants import router as restaurants_router
from routers.seasons import router as seasons_router
from routers.services import router as services_router
from routers.shops import router as shops_router
from routers.shows import router as shows_router
from routers.showtimes import router as showtimes_router
from routers.waittimes import router as waittimes_router
from services.auth import get_auth_service, initialize_auth, shutdown_auth
from services.cache import get_cache_service
from services.firebase_health import check_firebase_health, get_firebase_status
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    logger.info("Starting Europapark API Server...")
    
    settings = get_settings()
    logger.info(f"Configuration loaded. Firebase Project: {settings.fb_project_id}")
    
    await init_database()
    
    status = await check_firebase_health()
    if status.is_healthy:
        logger.info(f"Firebase health check successful. Response time: {status.response_time_ms:.2f}ms")
    else:
        logger.warning(f"Firebase health check failed: {status.last_error}")
    
    auth_success = await initialize_auth()
    if auth_success:
        auth_service = get_auth_service()
        logger.info(f"Authentication successful. Token valid until: {auth_service.get_status().get('expires_at')}")
        
        cache_service = get_cache_service()
        cache_service.start()
        logger.info("Cache service started.")
    else:
        logger.warning("Authentication failed.")
    
    start_scheduler()
    logger.info("Server started successfully.")
    
    yield
    
    logger.info("Shutting down server...")
    get_cache_service().stop()
    await shutdown_auth()
    stop_scheduler()
    await close_database()
    logger.info("Server shut down.")


app = FastAPI(
    title="Europapark API",
    description="API server for Europapark data",
    version="1.0.0",
    lifespan=lifespan,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(raw_router)
app.include_router(waittimes_router)
app.include_router(showtimes_router)
app.include_router(openingtimes_router)
app.include_router(seasons_router)
app.include_router(attractions_router)
app.include_router(shows_router)
app.include_router(shops_router)
app.include_router(restaurants_router)
app.include_router(services_router)


@app.get("/", tags=["API"], summary="API Info")
async def api_info():
    """Returns API name and version."""
    return {
        "api": "Europapark API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["API"], summary="Health Check")
async def health_check():
    """Returns service health status."""
    firebase_status = get_firebase_status()
    auth_service = get_auth_service()
    auth_status = auth_service.get_status()
    
    is_healthy = firebase_status.is_healthy and auth_status.get("authenticated", False)
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "firebase": firebase_status.to_dict(),
        "auth": auth_status,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
