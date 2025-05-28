import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import EconomicIndicator

class TestEconomicIndicatorManager(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.manager = EconomicIndicatorManager(repository=self.mock_repo)

    def test_TC01_fetch_all_populates_indicators(self):
        self.mock_repo.fetch_all.return_value = {
            "cpi": {"2024-01": 3.2, "2024-02": 3.3}
        }

        self.manager.fetch_all()
        indicators = self.manager.indicators["cpi"]
        self.assertEqual(len(indicators), 2)
        self.assertIsInstance(indicators[0], EconomicIndicator)
        self.assertEqual(indicators[0].value, 3.2)

    def test_TC02_get_indicator_calls_repository_if_not_cached(self):
        self.mock_repo.get_by_name.return_value = [
            EconomicIndicator(name="ppi", date="2024-01", value=2.1)
        ]
        result = self.manager.get_indicator("ppi")
        self.mock_repo.get_by_name.assert_called_once_with("ppi")
        self.assertEqual(result[0].name, "ppi")

    def test_TC03_get_indicator_uses_cache_if_exists(self):
        self.mock_repo.fetch_all.return_value = {
            "cpi": {"2024-01": 3.2}
        }
        self.manager.fetch_all()
        result = self.manager.get_indicator("cpi")
        self.mock_repo.get_by_name.assert_not_called()
        self.assertEqual(result[0].name, "cpi")

    def test_TC04_get_all_indicators_returns_flat_list(self):
        self.mock_repo.fetch_all.return_value = {
            "cpi": {"2024-01": 3.2},
            "ppi": {"2024-01": 2.0}
        }
        self.manager.fetch_all()
        all_indicators = self.manager.get_all_indicators()
        self.assertEqual(len(all_indicators), 2)
        names = [i.name for i in all_indicators]
        self.assertIn("cpi", names)
        self.assertIn("ppi", names)

    def test_TC05_get_indicator_returns_empty_list_if_not_found(self):
        self.mock_repo.get_by_name.return_value = []
        result = self.manager.get_indicator("nonexistent")
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
