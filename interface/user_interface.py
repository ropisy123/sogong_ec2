# interfaces/user_interface.py

from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository
from adapters.ai_forcast_repository import AIForecastRepository

class UserInterface:
    def __init__(self):
        self.asset_manager = AssetManager(AssetRepository())
        self.ai_forcast_repository = AIForecastRepository(AIForecastRepository())

    def get_chart_data(self, assets: list[str], resolution: str):
        return self.asset_manager.get_asset_data(assets, resolution)

    def get_correlation(self, asset1: str, asset2: str, period: str):
        return self.asset_manager.get_correlation_sliding_series(asset1, asset2, period)

    def get_probability_forecast(self, asset: str):
        return self.ai_forcast_repository.load_forecast(asset)

    def get_contextual_advice(self, asset: str, duration: str, tolerance: str):
        return self.ai_forcast_repository.load_advice(asset, duration, tolerance)
