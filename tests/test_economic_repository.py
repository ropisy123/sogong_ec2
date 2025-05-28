import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

# ✅ 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.economic_repository import EconomicRepository

class TestEconomicRepository(unittest.TestCase):
    def setUp(self):
        self.fred_api_key = "dummy_key"
        os.environ["FRED_API_KEY"] = self.fred_api_key

    def tearDown(self):
        if "FRED_API_KEY" in os.environ:
            del os.environ["FRED_API_KEY"]

    def test_init_with_key_env_set(self):
        repo = EconomicRepository()
        self.assertIsNotNone(repo.fred)

    @patch("adapters.economic_repository.settings")
    def test_init_without_key_raises(self, mock_settings):
        mock_settings.fred_api_key = None
        with self.assertRaises(ValueError):
            EconomicRepository()

    @patch("adapters.economic_repository.Fred")
    def test_fetch_indicator_series_success(self, mock_fred_class):
        mock_fred = MagicMock()
        mock_series = pd.Series(
            [300.1, 301.2, 302.3],
            index=pd.date_range("2023-01-01", periods=3, freq="M")
        )
        mock_fred.get_series.return_value = mock_series
        mock_fred_class.return_value = mock_fred

        repo = EconomicRepository()
        result = repo.fetch_indicator_series("cpi", "CPIAUCNS")
        self.assertEqual(len(result), 3)

    @patch("adapters.economic_repository.Fred")
    def test_fetch_indicator_series_empty(self, mock_fred_class):
        mock_fred = MagicMock()
        mock_series = pd.Series([], dtype=float)
        mock_fred.get_series.return_value = mock_series
        mock_fred_class.return_value = mock_fred

        repo = EconomicRepository()
        result = repo.fetch_indicator_series("ppi", "PPIACO")
        self.assertEqual(result, {})

    @patch("adapters.economic_repository.Fred")
    def test_fetch_indicator_series_api_exception(self, mock_fred_class):
        mock_fred = MagicMock()
        mock_fred.get_series.side_effect = Exception("FRED API error")
        mock_fred_class.return_value = mock_fred

        repo = EconomicRepository()
        result = repo.fetch_indicator_series("nonfarm", "PAYEMS")
        self.assertEqual(result, {})

    @patch.object(EconomicRepository, "fetch_indicator_series")
    def test_fetch_all_success(self, mock_fetch_series):
        mock_fetch_series.return_value = {
            "2023-01": 300.0,
            "2023-02": 301.0
        }
        repo = EconomicRepository()
        result = repo.fetch_all()
        self.assertEqual(len(result), 5)

    @patch.object(EconomicRepository, "fetch_indicator_series")
    def test_fetch_all_partial_failures(self, mock_fetch_series):
        def side_effect(key, series_id):
            if key == "cpi":
                return {"2023-01": 300.0}
            else:
                return {}
        mock_fetch_series.side_effect = side_effect
        repo = EconomicRepository()
        result = repo.fetch_all()
        self.assertIn("cpi", result)
        for k in ["ppi", "nonfarm", "retail", "unemployment"]:
            self.assertEqual(result[k], {})

if __name__ == "__main__":
    unittest.main()
