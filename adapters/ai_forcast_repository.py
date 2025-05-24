import os
import csv
from typing import Dict
from core.config import AI_FORCAST_DIR
from core.schemas import ForecastResult, AdviceEntry

class AIForecastRepository:
    def __init__(self, base_dir: str = AI_FORCAST_DIR,
                 forecast_filename: str = "forecast.csv",
                 advice_filename: str = "portfolio_advice.csv"):
        self.base_dir = base_dir
        self.forecast_filename = forecast_filename
        self.advice_filename = advice_filename

    def get_latest_folder(self) -> str:
        folders = [
            f for f in os.listdir(self.base_dir)
            if os.path.isdir(os.path.join(self.base_dir, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("No forecast folders found.")
        return max(folders)

    def load_forecast(self, asset: str) -> ForecastResult:
        folder = self.get_latest_folder()
        path = os.path.join(self.base_dir, folder, self.forecast_filename)
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["asset"] == asset:
                        return ForecastResult(
                            bullish=float(row["bullish"]),
                            neutral=float(row["neutral"]),
                            bearish=float(row["bearish"]),
                            expected_value=float(row["expected_value"])
                        )
        except Exception as e:
            print(f"[load_forecast] Error: {e}")
        return ForecastResult(0.0, 0.0, 0.0, 0.0)

    def load_advice(self, asset: str, duration: str, tolerance: str) -> AdviceEntry:
        folder = self.get_latest_folder()
        path = os.path.join(self.base_dir, folder, self.advice_filename)
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["asset"] == asset and row["duration"] == duration and row["tolerance"] == tolerance:
                        return AdviceEntry(
                            asset_name=asset,
                            allocation_ratio=float(row["allocation_ratio"]),
                            rationale=row["rationale"]
                        )
        except Exception as e:
            print(f"[load_advice] Error: {e}")
        return AdviceEntry(asset, 0.0, "정보 없음")

    def save_forecast(self, folder: str, forecasts: Dict[str, ForecastResult]) -> None:
        path = os.path.join(self.base_dir, folder, self.forecast_filename)
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["asset", "bullish", "neutral", "bearish", "expected_value"])
                for asset, result in forecasts.items():
                    writer.writerow([
                        asset,
                        result.bullish,
                        result.neutral,
                        result.bearish,
                        result.expected_value
                    ])
        except Exception as e:
            print(f"[save_forecast] Error: {e}")

    def save_advice(self, folder: str, advice_map: Dict[str, AdviceEntry], duration: str, tolerance: str) -> None:
        path = os.path.join(self.base_dir, folder, self.advice_filename)
        try:
            write_header = not os.path.exists(path) or os.stat(path).st_size == 0
            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["asset", "duration", "tolerance", "allocation_ratio", "rationale"])
                for asset, advice in advice_map.items():
                    writer.writerow([
                        asset, duration, tolerance,
                        advice.allocation_ratio,
                        advice.rationale
                    ])
        except Exception as e:
            print(f"[save_advice] Error: {e}")
