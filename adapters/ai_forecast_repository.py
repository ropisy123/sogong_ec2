import os
import csv
import shutil
from datetime import datetime
from typing import Dict, List
from core.config import AI_FORCAST_DIR, AI_FORCAST_FAIL_DIR
from core.schemas import ForecastResult, AdviceEntry

class AIForecastRepository:
    def __init__(self, base_dir: str = AI_FORCAST_DIR,
                 forecast_filename: str = "forecast.csv",
                 advice_filename: str = "portfolio_advice.csv"):
        self.base_dir = base_dir
        self.base_fail_dir = AI_FORCAST_FAIL_DIR
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
                            asset_name=asset,
                            bullish=float(row["bullish"]),
                            neutral=float(row["neutral"]),
                            bearish=float(row["bearish"]),
                            expected_value=float(row["expected_value"])
                        )
        except Exception as e:
            print(f"[load_forecast] Error: {e}")
        return ForecastResult(
            asset_name="NONE",
            bullish=0.0,
            neutral=0.0,
            bearish=0.0,
            expected_value=0.0
        )

    def load_advice(self, duration: str, tolerance: str) -> List[AdviceEntry]:
        folder = self.get_latest_folder()
        path = os.path.join(self.base_dir, folder, self.advice_filename)
        results = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["duration"] == duration and row["tolerance"] == tolerance:
                        entry = AdviceEntry(
                            asset_name=row["asset"],
                            allocation_ratio=float(row["allocation_ratio"]),
                            rationale=row["rationale"]
                        )
                        results.append(entry)
        except Exception as e:
            print(f"[load_advice] Error: {e}")
        return results

    def save_forecast(self, forecasts: Dict[str, 'ForecastResult'], is_failed: bool = False) -> None:
        folder = datetime.today().strftime("%Y%m%d")
        target_base = self.base_fail_dir if is_failed else self.base_dir
        save_dir = os.path.join(target_base, folder)
        os.makedirs(save_dir, exist_ok=True)

        csv_path = os.path.join(save_dir, self.forecast_filename)
        self._save_forecast_csv(forecasts, csv_path)

        if is_failed:
            self._move_all_json_to_fail(folder)

    def _save_forecast_csv(self, forecasts: Dict[str, 'ForecastResult'], path: str) -> None:
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["asset", "bullish", "neutral", "bearish", "expected_value"])
                for asset, result in forecasts.items():
                    if result is not None:
                        writer.writerow([
                            asset, result.bullish, result.neutral, result.bearish, result.expected_value
                        ])
                    else:
                        writer.writerow([asset, "N/A", "N/A", "N/A", "N/A"])
        except Exception as e:
            print(f"[save_forecast_csv] CSV 저장 실패: {e}")

    def _move_all_json_to_fail(self, folder: str) -> None:
        src_dir = os.path.join(self.base_dir, folder)
        dst_dir = os.path.join(self.base_fail_dir, folder)
        os.makedirs(dst_dir, exist_ok=True)

        try:
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.endswith(".json"):
                        src_file = os.path.join(root, file)
                        relative_path = os.path.relpath(src_file, src_dir)
                        dst_file = os.path.join(dst_dir, relative_path)

                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.move(src_file, dst_file)
                        print(f"[move_json] {src_file} → {dst_file}")
        except Exception as e:
            print(f"[move_json] JSON 이동 중 오류 발생: {e}")


    def save_advice(self, advice_map: Dict[str, 'AdviceEntry'], duration: str, tolerance: str) -> None:
        from datetime import datetime
        import csv
        import os

        folder = datetime.today().strftime("%Y%m%d")
        dir_path = os.path.join(self.base_dir, folder)
        os.makedirs(dir_path, exist_ok=True)

        path = os.path.join(dir_path, self.advice_filename)

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["asset", "duration", "tolerance", "allocation_ratio", "rationale"])
                for asset, advice in advice_map.items():
                    writer.writerow([
                        asset,
                        duration,
                        tolerance,
                        advice.allocation_ratio,
                        advice.rationale
                    ])
        except Exception as e:
            print(f"[save_advice] 저장 실패: {e}")