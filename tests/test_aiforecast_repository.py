import unittest
import os
import shutil
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from adapters.ai_forecast_repository import AIForecastRepository
from core.schemas import ForecastResult, AdviceEntry

class TestAIForecastRepository(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_ai_forecast"
        os.makedirs(self.test_dir, exist_ok=True)
        self.repo = AIForecastRepository(base_dir=self.test_dir)

        self.today_folder = datetime.today().strftime("%Y%m%d")
        self.full_path = os.path.join(self.test_dir, self.today_folder)
        os.makedirs(self.full_path, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_forecast_save_and_load(self):
        forecast = {
            "bitcoin": ForecastResult(
                asset_name="bitcoin",
                bullish=0.5,
                neutral=0.3,
                bearish=0.2,
                expected_value=0.6
            )
        }

        self.repo.save_forecast(forecast)
        result = self.repo.load_forecast("bitcoin")
        self.assertEqual(result.asset_name, "bitcoin")
        self.assertAlmostEqual(result.bullish, 0.5)
        self.assertAlmostEqual(result.neutral, 0.3)
        self.assertAlmostEqual(result.bearish, 0.2)
        self.assertAlmostEqual(result.expected_value, 0.6)

    def test_forecast_missing_file_returns_default(self):
        result = self.repo.load_forecast("nonexistent")
        self.assertEqual(result.asset_name, "NONE")
        self.assertEqual(result.expected_value, 0.0)

    def test_advice_save_and_load(self):
        os.makedirs(self.full_path, exist_ok=True)
        advice_map = {
            "bitcoin": AdviceEntry(
                asset_name="bitcoin",
                allocation_ratio=0.6,
                rationale="High potential"
            ),
            "gold": AdviceEntry(
                asset_name="gold",
                allocation_ratio=0.4,
                rationale="Stable asset"
            )
        }
        self.repo.save_advice(advice_map, "1y", "10%")

        result = self.repo.load_advice("1y", "10%")
        self.assertEqual(len(result), 2)
        asset_names = [entry.asset_name for entry in result]
        self.assertIn("bitcoin", asset_names)
        self.assertIn("gold", asset_names)

    def test_advice_missing_file_returns_empty(self):
        result = self.repo.load_advice("5y", "20%")
        self.assertEqual(result, [])

    def test_get_latest_folder_returns_most_recent(self):
        os.makedirs(os.path.join(self.test_dir, "20240101"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, self.today_folder), exist_ok=True)
        latest = self.repo.get_latest_folder()
        self.assertEqual(latest, self.today_folder)

    def test_get_latest_folder_raises_if_empty(self):
        shutil.rmtree(self.full_path)
        shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        with self.assertRaises(FileNotFoundError):
            self.repo.get_latest_folder()

    def test_save_forecast_creates_file(self):
        forecast = {
            "sp500": ForecastResult(
                asset_name="sp500",
                bullish=0.1,
                neutral=0.2,
                bearish=0.7,
                expected_value=-0.5)
        }
        self.repo.save_forecast(forecast)
        file_path = os.path.join(self.test_dir, self.today_folder, self.repo.forecast_filename)
        self.assertTrue(os.path.exists(file_path))

    def test_save_advice_appends_data(self):
        advice_map1 = {
            "bitcoin": AdviceEntry(asset_name="bitcoin", allocation_ratio=0.5, rationale="First entry") 
        }
        advice_map2 = {
            "gold": AdviceEntry(asset_name="gold", allocation_ratio=0.5, rationale="Second entry")
        }
        self.repo.save_advice(advice_map1, "3y", "5%")
        self.repo.save_advice(advice_map2, "3y", "5%")
        result = self.repo.load_advice("3y", "5%")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].rationale, "First entry")
        self.assertEqual(result[1].rationale, "Second entry")


if __name__ == "__main__":
    unittest.main()
