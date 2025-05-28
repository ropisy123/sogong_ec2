import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import unittest 
from unittest.mock import patch, MagicMock
from managers.ai_recommender import AIRecommender
from core.schemas import ForecastResult, AdviceEntry
from builders.prompt_builder import PromptBuilder
from builders.summary_text_builder import SummaryTextBuilder
from managers.economic_indicator_manager import EconomicIndicatorManager
from adapters.economic_repository import EconomicRepository

class TestAIRecommender(unittest.TestCase):

    def setUp(self):
        self.mock_llm = MagicMock()
        self.recommender = AIRecommender(llm_adapter=self.mock_llm)

    def test_TC01_generate_forecast_success(self):
        self.mock_llm.call_beta.return_value = '''
        {
            "상승확률": 0.6,
            "보합확률": 0.2,
            "하락확률": 0.2,
            "기대수익률": 4.5
        }
        '''
        result = self.recommender._parse_forecast("비트코인", self.mock_llm.call_beta.return_value, True)
        self.assertEqual(result.asset_name, "비트코인")
        self.assertAlmostEqual(result.bullish, 0.6)
        self.assertAlmostEqual(result.neutral, 0.2)
        self.assertAlmostEqual(result.bearish, 0.2)
        self.assertAlmostEqual(result.expected_value, 4.5)

    def test_TC02_generate_forecast_invalid_json(self):
        result = self.recommender._parse_forecast("금", "invalid json", True)
        self.assertIsNone(result)

    def test_TC03_generate_portfolio_advice_success(self):
        self.mock_llm.call_beta.return_value = '''
        {
            "금": {"권장비중": 50, "선정이유": "안정적"},
            "비트코인": {"권장비중": 50, "선정이유": "성장성"}
        }
        '''
        forecasts = {
            "금": ForecastResult(
                asset_name="금", bullish=0.5, neutral=0.2, bearish=0.3, expected_value=2.1
            ),
            "비트코인": ForecastResult(
                asset_name="비트코인", bullish=0.6, neutral=0.2, bearish=0.2, expected_value=5.4
            )
        }
        advice = self.recommender.generate_portfolio_advice(forecasts, "1년", "10%")
        self.assertEqual(len(advice), 2)
        self.assertEqual(advice["금"].allocation_ratio, 50.0)

    def test_TC04_generate_portfolio_advice_invalid_json(self):
        self.mock_llm.call_beta.return_value = "Invalid JSON"
        result = self.recommender._parse_advice(self.mock_llm.call_beta.return_value)
        self.assertEqual(result, {})

    def test_TC05_extract_json_block_code_block(self):
        text = '''```json
        {
            "상승": 60,
            "보합": 20,
            "하락": 20,
            "가중": 3
        }
        ```'''
        self.assertTrue(self.recommender._extract_json_block(text).startswith("{"))

    def test_TC06_extract_json_block_plain_json(self):
        text = '''
        {
            "상승": 60,
            "보합": 20,
            "하락": 20,
            "가중": 3
        }
        '''
        self.assertTrue(self.recommender._extract_json_block(text).startswith("{"))

    def test_TC07_get_loaded_forecast(self):
        with patch.object(self.recommender.repository, 'load_forecast') as mock_load:
            mock_load.return_value = ForecastResult(
                asset_name="S&P500", bullish=0.5, neutral=0.3, bearish=0.2, expected_value=3.1
            )
            result = self.recommender.get_loaded_forecast("S&P500")
            self.assertEqual(result.asset_name, "S&P500")

    def test_TC08_get_loaded_advices(self):
        with patch.object(self.recommender.repository, 'load_advice') as mock_load:
            mock_load.return_value = [
                AdviceEntry(asset_name="금", allocation_ratio=40.0, rationale="안정성"),
                AdviceEntry(asset_name="비트코인", allocation_ratio=60.0, rationale="성장성")
            ]
            result = self.recommender.get_loaded_advices("1년", "10%")
            self.assertEqual(len(result), 2)

    @patch("builders.summary_text_builder.pd.read_csv")
    def test_TC09_run_debate_and_get_trader_result(self, mock_read_csv):
        # 1. CSV mock
        mock_df = pd.DataFrame({
            "date": ["2025-01-01", "2025-01-02"],
            "close": [100, 105]
        })
        mock_read_csv.return_value = mock_df

        # 2. 의존성 mock
        mock_repo = MagicMock(spec=EconomicRepository)
        indicator_manager = EconomicIndicatorManager(repository=mock_repo)
        summary_builder = SummaryTextBuilder(indicator_manager)
        prompt_builder = PromptBuilder(indicator_manager)
        recommender = AIRecommender(prompt_builder)

        # 3. 실행
        result = recommender._run_debate_and_get_trader_result("비트코인", "/tmp")

        # 4. 검증
        self.assertIsInstance(result, dict)
        self.assertIn("trader", result)
        self.assertIn("reason", result)

    def test_TC10_generate_and_save_forecasts_and_advice(self):
        with patch.object(self.recommender, 'generate_forecast') as mock_forecast, \
             patch.object(self.recommender.repository, 'save_forecast'), \
             patch.object(self.recommender.repository, 'save_advice'), \
             patch.object(self.recommender, 'generate_portfolio_advice') as mock_advice:
            mock_forecast.return_value = ForecastResult(
                asset_name="금", bullish=0.5, neutral=0.3, bearish=0.2, expected_value=2.5
            )
            mock_advice.return_value = {
                "금": AdviceEntry(asset_name="금", allocation_ratio=50.0, rationale="안정성")
            }
            self.recommender.generate_and_save_forecasts_and_advice()

if __name__ == '__main__':
    unittest.main()

