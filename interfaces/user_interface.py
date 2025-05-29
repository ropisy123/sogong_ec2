# interfaces/user_interface.py

from managers.asset_manager import AssetManager

from dependencies import ai_recommender
from adapters.asset_repository import AssetRepository
from adapters.ai_forecast_repository import AIForecastRepository
from core.schemas import AdviceEntry
from typing import List

ASSET_NAME_MAP = {
    "sp500": "S&P500",
    "bitcoin": "비트코인",
    "kospi": "KOSPI",
    "gold": "금",
    "real_estate": "부동산",
    "kr_interest": "한국금리",
    "us_interest": "미국금리",
    # 필요시 추가
}

class UserInterface:
    def __init__(self):
        self.asset_manager = AssetManager(AssetRepository())
        self.ai_recommender = ai_recommender

    def get_chart_data(self, assets: list[str], resolution: str):
        return self.asset_manager.get_asset_data(assets, resolution)

    def get_correlation_sliding_series(self, asset1: str, asset2: str, period: str):
        return self.asset_manager.get_correlation_sliding_series(asset1, asset2, period)
    '''
    def get_probability_forecast(self, asset: str):
        return self.ai_recommender.get_probability_forecast(asset)

    def get_contextual_advices(self, duration: str, tolerance: str):
        return list(self.ai_recommender.get_contextual_advices(duration, tolerance).values())
    '''
    def get_portfolio_advice(self, duration: str, tolerance: str):
        return self.ai_recommender.get_loaded_advices(duration, tolerance)
    
    def get_forecast(self, asset: str):
        asset_key = asset.lower()
        normalized_name = ASSET_NAME_MAP.get(asset_key, asset)
        return self.ai_recommender.get_loaded_forecast(normalized_name)

