from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.services.discovery.google_places import GooglePlacesDiscoveryProvider
from app.services.discovery.google_search import GoogleSearchDiscoveryProvider
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.services.discovery.demo_provider import DemoDiscoveryProvider

router = APIRouter()


@router.get("")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Check database
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check providers
    places = GooglePlacesDiscoveryProvider()
    search = GoogleSearchDiscoveryProvider()
    overpass = OverpassDiscoveryProvider()

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "type": "sqlite" if settings.is_sqlite else "postgresql"
        },
        "discovery": {
            "active_provider": getattr(settings, "DISCOVERY_PROVIDER", "overpass"),
            "demo_mode": getattr(settings, "DEMO_MODE", False),
        },
        "free_testing_mode": {
            "enabled": getattr(settings, "DEMO_MODE", False),
            "demo_provider": DemoDiscoveryProvider().health_check()
        },
        "live_providers": {
            "overpass": overpass.health_check(),
            "google_places": places.health_check(),
            "google_search": search.health_check()
        }
    }

