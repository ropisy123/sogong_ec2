import os
from typing import Dict
from datetime import datetime
from fredapi import Fred
import pandas as pd
from pandas.tseries.offsets import DateOffset
from core.config import settings

INDICATOR_IDS = {
    "cpi": "CPIAUCNS",         # 소비자물가지수
    "ppi": "PPIACO",           # 생산자물가지수
    "nonfarm": "PAYEMS",       # 비농업 고용자 수
    "retail": "RSAFS",         # 소매판매지수
    "unemployment": "UNRATE"   # 실업률
}

class EconomicRepository:
    def __init__(self):
        fred_api_key = settings.fred_api_key
        if not fred_api_key:
            raise ValueError("환경변수 FRED_API_KEY가 설정되지 않았습니다.")
        self.fred = Fred(api_key=fred_api_key)


    def fetch_indicator_series(self, key: str, series_id: str) -> Dict[str, float]:
        try:
            end_date = datetime.today().replace(day=1)
            start_date = end_date - DateOffset(months=12)

            raw_series = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )

            monthly_series = raw_series.resample("M").last().dropna()

            return {
                date.strftime("%Y-%m"): round(value, 3)
                for date, value in monthly_series.items()
            }

        except Exception as e:
            print(f"[ERROR] FRED API '{series_id}' 조회 실패: {e}")
            return {}

    def fetch_all(self) -> Dict[str, Dict[str, float]]:
        all_data = {}
        for key, series_id in INDICATOR_IDS.items():
            print(f"[INFO] Fetching: {key} → {series_id}")
            result = self.fetch_indicator_series(key, series_id)
            all_data[key] = result
            print(result)
        return all_data
