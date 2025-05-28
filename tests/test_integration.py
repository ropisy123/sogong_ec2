import unittest
import tempfile
import shutil
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from adapters.asset_repository import AssetRepository
from managers.asset_manager import AssetManager
from managers.cycle_manager import CycleManager
from managers.correlation_manager import CorrelationManager
from core import config


class TestAssetSystemIntegration(unittest.TestCase):
    def setUp(self):
        load_dotenv()

        self.temp_dir = tempfile.mkdtemp()
        self.date_folder = datetime.today().strftime("%Y%m%d")
        self.full_data_path = os.path.join(self.temp_dir, self.date_folder)
        os.makedirs(self.full_data_path, exist_ok=True)

        # monkey patch DATA_DIR
        self.original_data_dir = config.DATA_DIR
        config.DATA_DIR = self.temp_dir

        self.repo = AssetRepository(target_dir=self.full_data_path)
        self.manager = AssetManager(self.repo)

        # Mock Data
        self.mock_dates = pd.date_range("2024-01-01", periods=90)
        self.df1 = pd.DataFrame({"date": self.mock_dates, "sp500": range(90)})
        self.df2 = pd.DataFrame({"date": self.mock_dates, "bitcoin": range(90, 0, -1)})

        self.df1.to_csv(os.path.join(self.full_data_path, "sp500.csv"), index=False)
        self.df2.to_csv(os.path.join(self.full_data_path, "bitcoin.csv"), index=False)

    def tearDown(self):
        config.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir)

    def test_IT01_update_all_assets_creates_files(self):
        self.manager.update_all_assets()
        for asset in self.manager.get_supported_assets():
            path = os.path.join(self.full_data_path, f"{asset}.csv")
            self.assertTrue(os.path.exists(path), f"{asset}.csv not created")

    def test_IT02_cycle_manager_merges_and_resamples(self):
        cycle = CycleManager()
        result = cycle.get_assets(["sp500", "bitcoin"], resolution="weekly")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("sp500", result[0])
        self.assertIn("bitcoin", result[0])

    def test_IT03_correlation_manager_sliding_result(self):
        corr = CorrelationManager()
        result = corr.get_correlation_sliding_series("sp500", "bitcoin", "1개월")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("date", result[0])
        self.assertIn("correlation", result[0])
        self.assertIsInstance(result[0]["correlation"], float)

    def test_IT04_asset_manager_get_asset_data(self):
        result = self.manager.get_asset_data(["sp500", "bitcoin"], "monthly")
        self.assertIsInstance(result, list)
        self.assertIn("sp500", result[0])
        self.assertIn("bitcoin", result[0])

    def test_IT05_asset_manager_correlation_series(self):
        result = self.manager.get_correlation_sliding_series("sp500", "bitcoin", "3개월")
        self.assertIsInstance(result, list)
        self.assertIn("correlation", result[0])
        self.assertIsInstance(result[0]["correlation"], float)

if __name__ == "__main__":
    unittest.main()
