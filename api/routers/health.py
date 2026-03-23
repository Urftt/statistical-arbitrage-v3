"""Health check endpoint."""

from fastapi import APIRouter, Depends

from api.schemas import HealthResponse
from src.statistical_arbitrage.data.cache_manager import (
    DataCacheManager,
    get_cache_manager,
)

router = APIRouter(prefix="/api", tags=["health"])


def get_cache_mgr() -> DataCacheManager:
    """Dependency: returns the singleton DataCacheManager."""
    return get_cache_manager()


@router.get("/health", response_model=HealthResponse)
def health_check(
    cache_mgr: DataCacheManager = Depends(get_cache_mgr),
) -> HealthResponse:
    """Return API status and the number of cached pair datasets."""
    cached = cache_mgr.list_cached()
    return HealthResponse(status="ok", pairs_cached=len(cached))
