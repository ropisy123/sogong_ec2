import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock
from builders.prompt_builder import PromptBuilder
from core.schemas import ForecastResult


class TestPromptBuilder(unittest.TestCase):

    def setUp(self):
        self.mock_summary_builder = MagicMock()
        self.mock_summary_builder.get_macro_summary.return_value = "Macro Summary"
        self.mock_summary_builder.get_asset_summary_all_text.return_value = "Asset Summary All"
        self.mock_summary_builder.get_asset_summary_single_text.return_value = "Asset Summary Single"

        self.prompt_builder = PromptBuilder(self.mock_summary_builder)

    def test_bullish_prompt(self):
        prompt = self.prompt_builder.build_bullish_prompt("금")
        self.assertIn("금에 대해 낙관적인", prompt)

    def test_bearish_prompt(self):
        prompt = self.prompt_builder.build_bearish_prompt("비트코인")
        self.assertIn("비트코인에 대해 비관적인", prompt)

    def test_bullish_rebuttal_prompt(self):
        prompt = self.prompt_builder.build_bullish_rebuttal_prompt("비트코인은 상승할 것이다", "비트코인")
        self.assertIn("비관적 분석을 반박하는 낙관적 애널리스트", prompt)

    def test_bearish_rebuttal_prompt(self):
        prompt = self.prompt_builder.build_bearish_rebuttal_prompt("금은 안전자산이다", "금")
        self.assertIn("낙관적 분석을 반박하는 비관적 애널리스트", prompt)

    def test_trader_prompt(self):
        prompt = self.prompt_builder.build_trader_prompt("논쟁 요약", "금")
        self.assertIn("투자의견", prompt)
        self.assertIn("기대수익률", prompt)

    def test_portfolio_advice_prompt(self):
        forecast = ForecastResult(
            asset_name="채권",  # ✅ 필수 필드 추가
            bullish=0.6,
            neutral=0.2,
            bearish=0.2,
            expected_value=5.4
        )
        prompt = self.prompt_builder.build_portfolio_advice_prompt(
            forecasts={"채권": forecast},
            investment_period="3년",
            max_loss_tolerance="20%"
        )
        self.assertIn("포트폴리오를 구성해 주세요", prompt)
        self.assertIn("총합 100%", prompt)

    def test_macro_summary_inclusion(self):
        prompt = self.prompt_builder.build_contextual_advice_prompt("5년", "10%")
        self.assertIn("Macro Summary", prompt)

    def test_asset_summary_inclusion(self):
        prompt = self.prompt_builder.build_contextual_advice_prompt("5년", "10%")
        self.assertIn("Asset Summary All", prompt)

