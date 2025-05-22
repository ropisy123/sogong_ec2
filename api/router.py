from fastapi import APIRouter, Query
from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository
from typing import List

router = APIRouter()
manager = AssetManager(AssetRepository())

@router.get("/chart")
def get_chart_data(
    assets: List[str] = Query(...),
    resolution: str = "daily"
):
    return manager.get_asset_data(assets, resolution)

@router.get("/correlation")
def get_correlation_sliding_series(
    asset1: str = Query(...),
    asset2: str = Query(...),
    period: str = Query(..., enum=["1개월", "3개월", "6개월"])
):
    return manager.get_correlation_sliding_series(asset1, asset2, period)
