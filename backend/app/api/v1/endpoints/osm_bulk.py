from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.endpoints.auth import get_current_user
from app.models import User
from app.services.osm_bulk.indexer import OsmBulkIndexService

router = APIRouter()


class BulkIndexLeadItem(BaseModel):
    osm_id: int
    osm_type: str = "node"
    business_name: str
    category: str
    latitude: float
    longitude: float
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    address_line: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    tag_key: Optional[str] = "amenity"
    tag_value: Optional[str] = "commercial"


class BulkIndexRequest(BaseModel):
    items: List[BulkIndexLeadItem] = Field(default_factory=list)


@router.get("/info")
def get_osm_bulk_info(
    current_user: User = Depends(get_current_user)
):
    """
    Returns hardware/disk requirements, Geofabrik official India extract mirrors,
    transparency disclaimer, and local indexing status.
    """
    service = OsmBulkIndexService()
    return service.get_bulk_index_info()


@router.post("/index")
def index_bulk_osm_leads(
    payload: BulkIndexRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Indexes batch of verified OSM business records into the local SQLite bulk index.
    Preserves OSM identifiers, address tags, contacts, and ODbL 1.0 license attribution.
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OSM items provided for indexing."
        )

    service = OsmBulkIndexService()
    dict_items = [it.model_dump() for it in payload.items]
    indexed_count = service.index_lead_items(dict_items)

    return {
        "success": True,
        "indexed_count": indexed_count,
        "message": f"Successfully indexed {indexed_count} businesses into local OSM database."
    }


@router.get("/search")
def search_local_osm_index(
    city: str = Query(..., description="Indian city center for radius search"),
    category: str = Query(..., description="Commercial industry category"),
    radius_km: float = Query(default=15.0, ge=1.0, le=100.0),
    max_results: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """
    Executes fast, rate-limit-free local discovery search against offline indexed OSM records.
    """
    service = OsmBulkIndexService()
    results = service.search_local_index(
        city=city,
        category=category,
        radius_km=radius_km,
        max_results=max_results
    )
    return {
        "success": True,
        "city": city,
        "category": category,
        "radius_km": radius_km,
        "count": len(results),
        "results": results
    }

