from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    discovery,
    leads,
    duplicates,
    locations,
    exports,
    health,
    sources,
    osm_bulk,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["Discovery Jobs"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(duplicates.router, prefix="/duplicates", tags=["Duplicates Review"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources Compliance"])
api_router.include_router(osm_bulk.router, prefix="/osm-bulk", tags=["Local OSM Bulk Index"])

