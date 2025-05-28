import unittest
from unittest.mock import patch
import os
import sys
import pandas as pd
import tempfile
import shutil

# ✅ 루트 경로를 PYTHONPATH에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from managers.cycle_manager import CycleManager


class TestCycleManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_folder = os.path.join(self.test_dir, "20240525")
        os.makedirs(self.test_folder, exist_ok=True)

        self.asset_name = "sp500"
        self.asset_file = os.path.join(self.test_folder, f"{self.asset_name}.csv")
        self.sample_data = pd.DataFrame({
            "date": pd.date_range(start="2024-01-01", periods=3).strftime("%Y-%m-%d"),
            self.asset_name: [100, None, 102]
        })
        self.sample_data.to_csv(self.asset_file, index=False)

        patcher = patch("managers.cycle_manager.DATA_DIR", self.test_dir)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.manager = CycleManager()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_latest_data_folder(self):
        folders = ["20240101", "20240525", "20240415"]
        for f in folders:
            os.makedirs(os.path.join(self.test_dir, f), exist_ok=True) 

        # latest 폴더 추정
        expected_latest = max(folders)

        with patch("managers.cycle_manager.DATA_DIR", self.test_dir):
            manager = CycleManager()
            self.assertEqual(manager._get_latest_data_folder(), expected_latest)

    def test_get_assets_daily_ffill(self):
        result = self.manager.get_assets([self.asset_name], "daily")
        expected = [
            {"date": "2024-01-01", self.asset_name: 100.0},
            {"date": "2024-01-02", self.asset_name: 100.0},
            {"date": "2024-01-03", self.asset_name: 102.0}
        ]
        self.assertEqual(result, expected)

    def test_get_assets_weekly_resample(self):
        result = self.manager.get_assets([self.asset_name], "weekly")
        self.assertTrue(isinstance(result, list))
        self.assertTrue(all("date" in r and self.asset_name in r for r in result))

    def test_get_assets_monthly_resample(self):
        result = self.manager.get_assets([self.asset_name], "monthly")
        self.assertTrue(isinstance(result, list))
        self.assertTrue(all("date" in r and self.asset_name in r for r in result))

    def test_get_assets_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.get_assets(["nonexistent_asset"])

    def test_get_assets_empty_returns_empty(self):
        result = self.manager.get_assets([])
        self.assertEqual(result, [])

    def test_get_assets_empty_data_returns_empty(self):
        pd.DataFrame(columns=["date", self.asset_name]).to_csv(self.asset_file, index=False)
        result = self.manager.get_assets([self.asset_name])
        self.assertEqual(result, [])

    def test_get_latest_data_folder_empty_raises(self):
        shutil.rmtree(self.test_folder)
        with self.assertRaises(FileNotFoundError):
            self.manager._get_latest_data_folder()


if __name__ == "__main__":
    unittest.main()
