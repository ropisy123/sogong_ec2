import unittest
from unittest.mock import MagicMock, patch
from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository
from managers.cycle_manager import CycleManager
from managers.correlation_manager import CorrelationManager
import pandas as pd
import os
import tempfile

class TestAssetManager(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock(spec=AssetRepository)
        self.mock_cycle = MagicMock(spec=CycleManager)
        self.mock_corr = MagicMock(spec=CorrelationManager)

        patcher_cycle = patch("managers.asset_manager.CycleManager", return_value=self.mock_cycle)
        patcher_corr = patch("managers.asset_manager.CorrelationManager", return_value=self.mock_corr)

        self.addCleanup(patcher_cycle.stop)
        self.addCleanup(patcher_corr.stop)

        self.mock_cycle_class = patcher_cycle.start()
        self.mock_corr_class = patcher_corr.start()

        self.manager = AssetManager(repo=self.mock_repo)

    def test_get_supported_assets(self):
        expected = [
            "sp500", "kospi", "bitcoin",
            "gold", "real_estate", "us_interest", "kr_interest"
        ]
        self.assertEqual(self.manager.get_supported_assets(), expected)

    def test_update_all_assets_calls_repo(self):
        self.manager.update_all_assets()
        calls = [unittest.mock.call(asset) for asset in self.manager.asset_list]
        self.mock_repo.fetch_and_save.assert_has_calls(calls, any_order=False)

    def test_update_all_assets_handles_exceptions(self):
        self.mock_repo.fetch_and_save.side_effect = Exception("fail")
        try:
            self.manager.update_all_assets()
        except Exception:
            self.fail("Exception should be caught and not raised")

    def test_get_asset_data_delegates_to_cycle_manager(self):
        self.manager.get_asset_data(["sp500", "bitcoin"], "daily")
        self.mock_cycle.get_assets.assert_called_once_with(["sp500", "bitcoin"], "daily")

    def test_get_correlation_sliding_series_delegates(self):
        self.manager.get_correlation_sliding_series("sp500", "bitcoin", "3개월")
        self.mock_corr.get_correlation_sliding_series.assert_called_once_with("sp500", "bitcoin", "3개월")

    def test_get_asset_df_returns_valid_dataframe(self):
        # 임시 파일 생성
        asset = "sp500"
        temp_dir = tempfile.mkdtemp()
        test_path = os.path.join(temp_dir, f"{asset}.csv")
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            asset: [100.0, 101.0]
        })
        df.to_csv(test_path, index=False)

        # BASE_DATA_DIR 에 접근하지 않도록 경로를 속이기 위해 monkey patch
        from managers import asset_manager
        asset_manager.BASE_DATA_DIR = temp_dir

        result_df = self.manager.get_asset_df(asset)
        pd.testing.assert_frame_equal(
            result_df,
            pd.DataFrame({
                "date": ["2024-01-01", "2024-01-02"],
                "value": [100.0, 101.0]
            })
        )

    def test_get_latest_available_folder_empty_raises(self):
        from managers import asset_manager
        empty_dir = tempfile.mkdtemp()
        asset_manager.DATA_DIR = empty_dir
        with self.assertRaises(FileNotFoundError):
            self.manager.get_latest_available_folder()

    def test_get_latest_available_folder_returns_latest(self):
        from managers import asset_manager
        base_dir = tempfile.mkdtemp()
        # 날짜 폴더 생성
        os.makedirs(os.path.join(base_dir, "20240101"))
        os.makedirs(os.path.join(base_dir, "20240525"))
        os.makedirs(os.path.join(base_dir, "20240415"))
        asset_manager.DATA_DIR = base_dir
        result = self.manager.get_latest_available_folder()
        self.assertEqual(result, "20240525")

if __name__ == "__main__":
    unittest.main()
