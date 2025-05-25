import unittest
import pandas as pd
import os
import tempfile
import sys
from datetime import datetime
from shutil import rmtree

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from managers import correlation_manager  # 이제 import 가능

class TestCorrelationManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.today = datetime.today().strftime("%Y%m%d")
        self.latest_dir = os.path.join(self.test_dir, self.today)
        os.makedirs(self.latest_dir, exist_ok=True)

        # DATA_DIR monkey patch
        self.original_data_dir = correlation_manager.DATA_DIR
        correlation_manager.DATA_DIR = self.test_dir

        # 더미 자산 데이터 생성
        self.asset1 = "asset1"
        self.asset2 = "asset2"
        dates = pd.date_range("2024-01-01", periods=180)
        df1 = pd.DataFrame({"date": dates, self.asset1: range(180)})
        df2 = pd.DataFrame({"date": dates, self.asset2: range(180, 0, -1)})
        df1.to_csv(os.path.join(self.latest_dir, f"{self.asset1}.csv"), index=False)
        df2.to_csv(os.path.join(self.latest_dir, f"{self.asset2}.csv"), index=False)

        self.manager = correlation_manager.CorrelationManager()

    def tearDown(self):
        correlation_manager.DATA_DIR = self.original_data_dir
        rmtree(self.test_dir)

    def test_get_correlation_sliding_series_valid(self):
        result = self.manager.get_correlation_sliding_series(self.asset1, self.asset2, "3개월")
        self.assertTrue(len(result) > 0)
        self.assertIn("date", result[0])
        self.assertIn("correlation", result[0])
        self.assertIsInstance(result[0]["correlation"], float)

    def test_get_correlation_sliding_series_invalid_period(self):
        with self.assertRaises(ValueError):
            self.manager.get_correlation_sliding_series(self.asset1, self.asset2, "12개월")

    def test_get_correlation_sliding_series_with_missing_file(self):
        os.remove(os.path.join(self.latest_dir, f"{self.asset2}.csv"))
        with self.assertRaises(FileNotFoundError):
            self.manager.get_correlation_sliding_series(self.asset1, self.asset2, "1개월")

    def test_get_latest_data_folder(self):
        latest = self.manager._get_latest_data_folder()
        self.assertEqual(latest, self.today)

if __name__ == "__main__":
    unittest.main()
