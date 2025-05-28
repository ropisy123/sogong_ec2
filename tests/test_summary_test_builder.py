import unittest
import shutil
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from unittest.mock import MagicMock
from builders.summary_text_builder import SummaryTextBuilder
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import EconomicIndicator


class TestSummaryTextBuilder(unittest.TestCase):
    def setUp(self):
        # 테스트용 폴더 및 파일 생성
        self.test_dir = "test_data"
        self.today_folder = datetime.today().strftime("%Y%m%d")
        self.full_path = os.path.join(self.test_dir, self.today_folder)
        os.makedirs(self.full_path, exist_ok=True)

        # 테스트 자산 데이터 생성
        date_range = pd.date_range(end=datetime.today(), periods=300)
        df = pd.DataFrame({
            "date": date_range,
            "sp500": [1000 + i for i in range(300)],
        })
        df.to_csv(os.path.join(self.full_path, "sp500.csv"), index=False)

        # Mock된 EconomicIndicatorManager
        self.mock_manager = MagicMock(spec=EconomicIndicatorManager)
        indicators = [
            EconomicIndicator(name="cpi", date="2024-01", value=3.1),
            EconomicIndicator(name="cpi", date="2024-02", value=3.3),
            EconomicIndicator(name="unemployment", date="2024-01", value=4.2),
        ]
        self.mock_manager.get_all_indicators.return_value = indicators

        self.builder = SummaryTextBuilder(self.mock_manager)
        self.builder.data_dir = self.test_dir  # 테스트 경로로 override

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_TC01_macro_summary_success(self):
        summary = self.builder.get_macro_summary()
        self.assertIn("소비자물가지수", summary)
        self.assertIn("실업률", summary)

    def test_TC02_macro_summary_cache(self):
        self.builder._macro_summary_cache = "캐시된 결과"
        result = self.builder.get_macro_summary()
        self.assertEqual(result, "캐시된 결과")

    def test_TC03_asset_summary_all_success(self):
        result = self.builder.get_asset_summary_all_text()
        self.assertIn("S&P500", result)
        self.assertIn("최근값", result)

    def test_TC04_asset_summary_all_cache(self):
        self.builder._asset_summary_cache["_all"] = "자산 캐시 요약"
        result = self.builder.get_asset_summary_all_text()
        self.assertEqual(result, "자산 캐시 요약")

    def test_TC05_asset_summary_single_success(self):
        result = self.builder.get_asset_summary_single_text("S&P500")
        self.assertIn("최근 통계 요약", result)

    def test_TC06_asset_summary_single_cache(self):
        self.builder._asset_summary_cache["S&P500"] = {
            "최근값": 1200,
            "12개월 평균": 1100,
            "증감률(%)": 8.0,
            "표준편차": 2.3,
            "기울기": 1.2,
            "일간 변동률 평균(%)": 0.5
        }
        result = self.builder.get_asset_summary_single_text("S&P500")
        self.assertIn("최근값: 1200", result)

    def test_TC07_asset_summary_invalid_asset(self):
        with self.assertRaises(ValueError):
            self.builder.get_asset_summary_single_text("INVALID")

    def test_TC08_calc_stats_valid(self):
        df = pd.read_csv(os.path.join(self.full_path, "sp500.csv"))
        stats = self.builder._calc_stats(df, "sp500")
        self.assertIn("최근값", stats)
        self.assertIn("12개월 평균", stats)

    def test_TC09_get_latest_folder_success(self):
        result = self.builder._get_latest_data_dir(self.test_dir)
        self.assertTrue(result.endswith(self.today_folder))

    def test_TC10_get_latest_folder_fail(self):
        shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        with self.assertRaises(FileNotFoundError):
            self.builder._get_latest_data_dir(self.test_dir)


if __name__ == "__main__":
    unittest.main()
