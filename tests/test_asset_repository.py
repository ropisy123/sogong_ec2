import unittest
from unittest.mock import patch
from datetime import datetime
import pandas as pd
import os
import tempfile
import shutil
import logging

from adapters.asset_repository import AssetRepository

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AssetRepositoryTest")

class TestAssetRepository(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo = AssetRepository(target_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_all_assets(self):
        expected_assets = {
            "sp500", "kospi", "bitcoin", "gold", "real_estate", "us_interest", "kr_interest"
        }
        self.assertEqual(set(self.repo.asset_symbol_map.keys()), expected_assets)
        logger.info("✅ test_get_all_assets passed.")

    @patch("adapters.asset_repository.yf.download")
    def test_fetch_from_yahoo_and_save(self, mock_download):
        asset = "sp500"
        mock_df = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Close": [100, 101, 102, 103, 104]
        }).set_index("Date")
        mock_download.return_value = mock_df

        self.repo.fetch_from_yahoo(asset, "^GSPC")
        path = os.path.join(self.repo.output_dir, f"{asset}.csv")
        self.assertTrue(os.path.exists(path))
        logger.info("✅ test_fetch_from_yahoo_and_save passed.")

    @patch("fredapi.Fred.get_series")
    def test_fetch_from_fred_and_save(self, mock_get_series):
        asset = "us_interest"
        mock_df = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=5),
            asset: [1.5, 1.6, 1.7, 1.8, 1.9]
        })
        mock_get_series.return_value = mock_df.set_index("date").squeeze()
        self.repo.fetch_from_fred(asset, "FEDFUNDS")
        path = os.path.join(self.repo.output_dir, f"{asset}.csv")
        self.assertTrue(os.path.exists(path))
        logger.info("✅ test_fetch_from_fred_and_save passed.")

    def test_fetch_and_save_invalid_asset(self):
        with self.assertRaises(ValueError):
            self.repo.fetch_and_save("invalid_asset")
        logger.info("✅ test_fetch_and_save_invalid_asset passed.")

    @patch("adapters.asset_repository.yf.download")
    def test_fetch_from_yahoo_empty_data(self, mock_download):
        asset = "sp500"
        mock_download.return_value = pd.DataFrame()
        self.repo.fetch_from_yahoo(asset, "^GSPC")
        path = os.path.join(self.repo.output_dir, f"{asset}.csv")
        self.assertFalse(os.path.exists(path))
        logger.info("✅ test_fetch_from_yahoo_empty_data passed.")

    @patch("fredapi.Fred.get_series")
    def test_fetch_from_fred_with_exception(self, mock_get_series):
        asset = "us_interest"
        mock_get_series.side_effect = Exception("API failure")
        self.repo.fetch_from_fred(asset, "FEDFUNDS")
        path = os.path.join(self.repo.output_dir, f"{asset}.csv")
        self.assertFalse(os.path.exists(path))
        logger.info("✅ test_fetch_from_fred_with_exception passed.")

    @patch("adapters.asset_repository.yf.download")
    def test_fetch_from_yahoo_missing_close_column(self, mock_download):
        asset = "sp500"
        mock_df = pd.DataFrame({
            "Open": [100, 101, 102],
            "High": [110, 111, 112]
        })
        mock_df.index.name = "Date"
        mock_download.return_value = mock_df

        try:
            self.repo.fetch_from_yahoo(asset, "^GSPC")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")
        logger.info("✅ test_fetch_from_yahoo_missing_close_column passed.")

    @patch("adapters.asset_repository.yf.download")
    @patch.object(pd.DataFrame, "to_csv")
    def test_fetch_from_yahoo_should_attempt_to_save(self, mock_to_csv, mock_download):
        asset = "sp500"
        mock_df = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Close": [100, 101, 102, 103, 104]
        }).set_index("Date")
        mock_download.return_value = mock_df

        self.repo.fetch_from_yahoo(asset, "^GSPC")
        mock_to_csv.assert_called_once()
        logger.info("✅ test_fetch_from_yahoo_should_attempt_to_save passed.")

    @patch("adapters.asset_repository.yf.download")
    def test_fetch_from_yahoo_should_save_correct_data(self, mock_download):
        asset = "sp500"
        raw_df = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Close": [100, 101, 102, 103, 104]
        }).set_index("Date")
        raw_df.index.name = "Date"
        mock_download.return_value = raw_df

        self.repo.fetch_from_yahoo(asset, "^GSPC")
        path = os.path.join(self.repo.output_dir, f"{asset}.csv")
        self.assertTrue(os.path.exists(path))

        saved_df = pd.read_csv(path)
        base_dates = pd.date_range(start="2005-01-01", end=datetime.today(), freq="D")
        expected_partial = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=5),
            asset: [100, 101, 102, 103, 104]
        })
        expected_full = pd.DataFrame({"date": base_dates})
        expected_full = pd.merge(expected_full, expected_partial, on="date", how="left")
        expected_full[asset] = expected_full[asset].ffill().fillna(0)
        expected_full["date"] = expected_full["date"].dt.strftime("%Y-%m-%d")
        saved_df["date"] = saved_df["date"].astype(str)

        pd.testing.assert_frame_equal(saved_df, expected_full)
        logger.info("✅ test_fetch_from_yahoo_should_save_correct_data passed.")

if __name__ == "__main__":
    unittest.main()
