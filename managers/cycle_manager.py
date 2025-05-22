import os
import pandas as pd
from typing import List
from datetime import datetime
from core.config import DATA_DIR

class CycleManager:
    def __init__(self):
        self.latest_folder = self._get_latest_data_folder()

    def get_assets(self, asset_names: List[str], resolution: str = "daily") -> List[dict]:
        merged_df = None

        for asset in asset_names:
            df = self._load_asset(asset)
            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="date", how="outer")

        if merged_df is None or merged_df.empty:
            return []

        merged_df = merged_df.sort_values("date").ffill()
        merged_df["date"] = pd.to_datetime(merged_df["date"])
        merged_df = merged_df.set_index("date")

        # 리샘플링
        if resolution == "weekly":
            merged_df = merged_df.resample("W").mean()
        elif resolution == "monthly":
            merged_df = merged_df.resample("M").mean()

        merged_df = merged_df.reset_index()
        merged_df["date"] = merged_df["date"].dt.strftime("%Y-%m-%d")
        return merged_df.to_dict(orient="records")

    def _load_asset(self, asset: str) -> pd.DataFrame:
        path = os.path.join(DATA_DIR, self.latest_folder, f"{asset}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{asset}.csv not found in latest folder")
        df = pd.read_csv(path)
        return df[["date", asset]]

    def _get_latest_data_folder(self) -> str:
        folders = [
            f for f in os.listdir(DATA_DIR)
            if os.path.isdir(os.path.join(DATA_DIR, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("No data folders found in /data/")
        return max(folders)
