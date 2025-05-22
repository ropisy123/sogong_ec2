import os
import pandas as pd
from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
from typing import List, Dict
from core.config import DATA_DIR


class CorrelationManager:
    def __init__(self):
        self.latest_folder = self._get_latest_data_folder()

    def get_correlation_sliding_series(self, asset1: str, asset2: str, period: str) -> List[Dict[str, object]]:
        period_map = {
            "1개월": 1,
            "3개월": 3,
            "6개월": 6
        }

        if period not in period_map:
            raise ValueError("Invalid period: must be one of 1개월, 3개월, 6개월")

        months = period_map[period]

        df1 = self._load_asset(asset1)
        df2 = self._load_asset(asset2)

        merged = pd.merge(df1, df2, on="date", how="inner")
        merged = merged.sort_values(by="date").ffill()
        merged["date"] = pd.to_datetime(merged["date"])
        merged = merged.set_index("date")

        results = []

        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = today.replace(day=1)  # e.g. 2025-05-01
        min_date = merged.index.min()

        while True:
            window_start = window_end - DateOffset(months=months)

            if window_start < min_date:
                break

            window = merged.loc[window_start:window_end]
            s1 = window[asset1]
            s2 = window[asset2]
    
            if s1.empty or s2.empty or s1.std() == 0 or s2.std() == 0:
                window_end -= DateOffset(months=months)
                continue

            corr = s1.corr(s2)
            if pd.notna(corr):
                results.append({
                    "date": window_end.strftime("%Y-%m-%d"),  # e.g. 2025-05-01
                    "correlation": round(corr, 4)
                })

            window_end -= DateOffset(months=months)

        # 오름차순 정렬해서 리턴
        return list(reversed(results))

    def _load_asset(self, asset: str) -> pd.DataFrame:
        path = os.path.join(DATA_DIR, self.latest_folder, f"{asset}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found")
        df = pd.read_csv(path)
        return df[["date", asset]]

    def _get_latest_data_folder(self) -> str:
        folders = [
            f for f in os.listdir(DATA_DIR)
            if os.path.isdir(os.path.join(DATA_DIR, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("No date folders found in /data/")
        return max(folders)
