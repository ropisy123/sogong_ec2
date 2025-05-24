import os
import csv
import json
import logging
from typing import Dict
from adapters.llm_adapter import LLMAdapter
from adapters.economic_repository import EconomicRepository
from core.config import AI_FORCAST_DIR
from core.prompt_builders import PromptBuilder
from core.schemas import ForecastResult, AdviceEntry
from managers.economic_indicator_manager import EconomicIndicatorManager

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class AIRecommender:
    def __init__(self):
        logger.info("AIRecommender 초기화 중...")
        self.llm = LLMAdapter()
        self.prompt_builder = PromptBuilder(EconomicIndicatorManager(EconomicRepository))
        self.base_data_dir = AI_FORCAST_DIR
        logger.info("AIRecommender 초기화 완료")

    def generate_forecast(self, asset: str, save_dir: str) -> ForecastResult:
        logger.info(f"{asset} 예측 중...")
        forecast_result = self._run_debate_and_get_trader_result(asset, save_dir)
        parsed_forecast = self._parse_forecast(forecast_result)
        return parsed_forecast

    def generate_portfolio_advice(self, forecasts: Dict[str, ForecastResult], duration: str, tolerance: str) -> Dict[str, AdviceEntry]:
        prompt = self.prompt_builder.build_portfolio_advice_prompt(forecasts, duration, tolerance)
        result = self.llm.call(prompt)
        return self._parse_advice(result)

    def _run_debate_and_get_trader_result(self, asset: str, save_dir: str) -> dict:
        logger.info(f"[{asset}] 토론 시작")
        prompts_responses = {}

        def _call_and_store(name, prompt_func, *args):
            prompt = prompt_func(*args)
            response = self.llm.call(prompt)
            prompts_responses[name] = {"prompt": prompt, "response": response}
            return response

        bull1 = _call_and_store("bull1", self.prompt_builder.build_bullish_prompt, asset)
        bear1 = _call_and_store("bear1", self.prompt_builder.build_bearish_prompt, asset)
        bear2 = _call_and_store("bear2", self.prompt_builder.build_bearish_rebuttal_prompt, bull1, asset)
        bull2 = _call_and_store("bull2", self.prompt_builder.build_bullish_rebuttal_prompt, bear1, asset)

        debate_summary = (
            f"[애널리스트 A: Bullish 분석]\n{bull1}\n\n"
            f"[애널리스트 B: A에 대한 반박 (Bearish 시각)]\n{bear1}\n\n"
            f"[애널리스트 C: 별도 Bearish 분석]\n{bear2}\n\n"
            f"[애널리스트 D: C에 대한 반박 (Bullish 시각)]\n{bull2}"
        )
        trader_prompt = self.prompt_builder.build_trader_prompt(debate_summary, asset)
        trader_result = self.llm.call(trader_prompt, return_json=True)
        prompts_responses["trader"] = {"prompt": trader_prompt, "response": trader_result}

        json_path = os.path.join(save_dir, f"{asset.replace(' ', '_')}_raw_ai_forecast.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(prompts_responses, jf, ensure_ascii=False, indent=2)

        logger.info(f"[{asset}] 토론 결과 완료 → 결과: {trader_result}")
        return trader_result

    def _parse_forecast(self, result: dict) -> ForecastResult:
        try:
            return ForecastResult(
                bullish=float(result.get("상승확률", 0.0)),
                neutral=float(result.get("보합확률", 0.0)),
                bearish=float(result.get("하락확률", 0.0)),
                expected_value=float(result.get("기대수익률", 0.0))
            )
        except Exception as e:
            logger.error(f"Forecast parsing failed: {e}")
            return ForecastResult(0.0, 0.0, 0.0, 0.0)

    def _parse_advice(self, result: str) -> Dict[str, AdviceEntry]:
        try:
            parsed = eval(result) if isinstance(result, str) else result
            return {
                asset: AdviceEntry(
                    asset_name=entry.get("자산명", asset),
                    allocation_ratio=float(entry.get("권장비중", 0.0)),
                    rationale=entry.get("선정이유", "정보 없음")
                )
                for asset, entry in parsed.items()
            }
        except Exception as e:
            logger.error(f"Advice parsing failed: {e}")
            return {}
