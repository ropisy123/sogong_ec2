import os
from typing import List, Dict
from adapters.asset_repository import AssetRepository
from managers.cycle_manager import CycleManager
from managers.correlation_manager import CorrelationManager
from core.config import DATA_DIR
from datetime import datetime, timedelta
import pandas as pd

class AssetManager:
    def __init__(self, repo: AssetRepository):
        self.asset_list = [
            "sp500", "kospi", "bitcoin",
            "gold", "kr_real_estate", "us_interest", "kr_interest"
        ]
        self.repo = repo
        self.cycle_manager = CycleManager()
        self.correlation_manager = CorrelationManager()

    def update_all_assets(self):
        for asset in self.asset_list:
            try:
                self.repo.fetch_and_save(asset)
            except Exception as e:
                print(f"[ERROR] Failed to update {asset}: {e}")

    def get_supported_assets(self) -> List[str]:
        return self.asset_list

    def get_asset_data(self, asset_names: List[str], resolution: str = "daily") -> List[dict]:
        """
        asset_names: 예) ["sp500", "bitcoin"]
        resolution: "daily", "weekly", "monthly"
        """
        return self.cycle_manager.get_assets(asset_names, resolution)

    def get_correlation_sliding_series(self, asset1: str, asset2: str, period: str):
        return self.correlation_manager.get_correlation_sliding_series(asset1, asset2, period)


    def get_asset_df(self, asset: str) -> pd.DataFrame:
        path = os.path.join(BASE_DATA_DIR, f"{asset}.csv")
        df = pd.read_csv(path)
        df = df.rename(columns={asset: "value"})
        return df[["date", "value"]]

    def get_latest_available_folder(self) -> str:
        """가장 최근 날짜 폴더 반환 (예: 20240522)"""
        folders = [
            f for f in os.listdir(DATA_DIR)
            if os.path.isdir(os.path.join(DATA_DIR, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("No data folders found in /data/")
        return max(folders)
