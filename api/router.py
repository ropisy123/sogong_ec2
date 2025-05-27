from fastapi import APIRouter, Query
from interfaces.user_interface import UserInterface
from core.schemas import AdviceEntry
from typing import List, Dict

router = APIRouter()
ui = UserInterface()  # 이제 UI 계층에서 모든 비즈니스 로직 호출

@router.get("/chart")
def get_chart_data(
    assets: List[str] = Query(...),
    resolution: str = "daily"
):
    return ui.get_chart_data(assets, resolution)

@router.get("/correlation")
def get_correlation_sliding_series(
    asset1: str = Query(...),
    asset2: str = Query(...),
    period: str = Query(..., enum=["1개월", "3개월", "6개월"])
):
    return ui.get_correlation_sliding_series(asset1, asset2, period)

@router.get("/ai-contextual-advices")
def get_ai_contextual_advices(
    duration: str = Query(..., enum=["1년", "3년", "5년", "10년"]),
    tolerance: str = Query(..., enum=["5%", "10%", "20%"])
):
    return ui.get_contextual_advices(duration, tolerance)

@router.get("/ai-probability-forecast")
def get_ai_forecast(
    asset: str = Query(...)
):
    return ui.get_probability_forecast(asset)
