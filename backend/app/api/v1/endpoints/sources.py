from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.auth import get_current_user
from app.models import User
from app.services.compliance.source_registry import SourceRightsComplianceService

router = APIRouter()


@router.get("/registry", response_model=List[Dict[str, Any]])
def get_source_registry(
    current_user: User = Depends(get_current_user)
):
    """
    Returns legal provenance, permitted use guidelines, ODbL attribution,
    and technical fair-use constraints for all business data sources.
    """
    return SourceRightsComplianceService.get_source_registry()

