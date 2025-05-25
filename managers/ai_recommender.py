from adapters.llm_adapter import LLMAdapter
from core.prompt_builder import PromptBuilder
from adapters.llm_adapter import LLMAdapter
from adapters.economic_repository import EconomicRepository
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import ForecastResult, AdviceEntry
from typing import Dict, Tuple

class AIRecommender:
    def __init__(self, llm_adapter=None, prompt_builder=None):
        self.llm = llm_adapter or LLMAdapter()
        self.prompt_builder = PromptBuilder(EconomicIndicatorManager(EconomicRepository()))

        # 자산별 예측치 저장
        self.probabilityForecast: Dict[str, ForecastResult] = {}

        # 자산별 권장비중 및 선정 이유 저장
        self.contextualAdvice: Dict[Tuple[str, str], Dict[str, AdviceEntry]] = {}

    def fetch_probability_forecast(self):
        for asset in ["sp500", "kospi", "bitcoin", "gold", "real_estate"]:
            prompt = self.prompt_builder.build_probability_forecast_prompt(asset)
            result = self.llm.call(prompt)
            self.probabilityForecast[asset] = self._parse_forecast(result)

    def fetch_contextual_advice(self):
        durations = ["1년", "3년", "5년", "10년"]
        tolerances = ["5%", "10%", "20%"]
        for duration in durations:
            for tolerance in tolerances:
                prompt = self.prompt_builder.build_contextual_advice_prompt(duration, tolerance)
                result = self.llm.call(prompt)
                parsed = self._parse_advice(result)
                self.contextualAdvice[(duration, tolerance)] = parsed

    def get_probability_forecast(self, asset: str) -> ForecastResult:
        return self.probabilityForecast.get(asset, ForecastResult(0.0, 0.0, 0.0, 0.0))

    def get_contextual_advice(self, asset: str, duration: str, tolerance: str) -> AdviceEntry:
        advice_map = self.contextualAdvice.get((duration, tolerance), {})
        return advice_map.get(asset, AdviceEntry(
            asset_name=asset,
            allocation_ratio=0.0,
            rationale="해당 자산에 대한 정보가 없습니다."
        ))

    def _parse_forecast(self, result: str) -> ForecastResult:
        try:
            parsed = eval(result)
            return ForecastResult(
                asset_name="unknown",  # 실제 자산명은 외부에서 지정
                rise=float(parsed["상승"]),
                hold=float(parsed["보합"]),
                fall=float(parsed["하락"]),
                expected_value=float(parsed["상승"]) * 1 + float(parsed["보합"]) * 0 + float(parsed["하락"]) * -1,
            )
        except Exception as e:
            print(f"[ERROR] Forecast parsing failed: {e}")
            return ForecastResult(asset_name="unknown", rise=0.0, hold=0.0, fall=0.0, expected_value=0.0)


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
            print(f"[ERROR] Advice parsing failed: {e}")
            return {}
