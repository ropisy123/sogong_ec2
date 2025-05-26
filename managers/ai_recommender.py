from adapters.llm_adapter import LLMAdapter
from core.prompt_builder import PromptBuilder
from adapters.llm_adapter import LLMAdapter
from adapters.economic_repository import EconomicRepository
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import ForecastResult, AdviceEntry
from typing import Dict, Tuple, Optional
import json
import re

class AIRecommender:
    def __init__(self, llm_adapter=None, prompt_builder=None):
        self.llm = llm_adapter or LLMAdapter()
        self.prompt_builder = PromptBuilder(EconomicIndicatorManager(EconomicRepository()))

        # 자산별 예측치 저장
        self.probabilityForecast: Dict[str, ForecastResult] = {}

        # 자산별 권장비중 및 선정 이유 저장
        self.contextualAdvice: Dict[Tuple[str, str], Dict[str, AdviceEntry]] = {}

    def fetch_probability_forecast(self):
        for asset in ["sp500", "kospi", "bitcoin", "gold", "kr_real_estate", "us_interest", "kr_interest"]:
            prompt = self.prompt_builder.build_probability_forecast_prompt(asset)
            result = self.llm.call(prompt)
            self.probabilityForecast[asset] = self._parse_forecast(asset, result)

    def fetch_contextual_advice(self):
        durations = ["1년", "3년", "5년", "10년"]
        tolerances = ["5%", "10%", "20%"]

        for duration in durations:
            for tolerance in tolerances:
                print(duration)
                print(tolerance)
                try:
                    prompt = self.prompt_builder.build_contextual_advice_prompt(duration, tolerance)
                    result = self.llm.call(prompt)
                    result = re.sub(r"```(json)?", "", result).strip()
                    parsed_advice = self._parse_advice(result)

                    self.contextualAdvice[(duration, tolerance)] = parsed_advice

                    print(parsed_advice)
                    print(f"[INFO] ✅ contextualAdvice 저장 완료 - 기간: {duration}, 손실허용: {tolerance}, 자산 수: {len(parsed_advice)}")

                except Exception as e:
                    print(f"[ERROR] contextualAdvice 갱신 실패 - 기간: {duration}, 손실허용: {tolerance}")
                    print(f"[DEBUG] 오류: {e}")

    def get_probability_forecast(self, asset: str) -> ForecastResult:
        return self.probabilityForecast.get(
            asset,
            ForecastResult(
                asset_name=asset,
            rise_probability_percent=0,
            fall_probability_percent=0,
            neutral_probability_percent=0,
            expected_value_percent=0,
        )
    )

    def get_contextual_advice(self, asset: str, duration: str, tolerance: str) -> AdviceEntry:
        key = (duration, tolerance)
        asset = asset.lower()  # ✅ 소문자로 변환

        print(self.contextualAdvice)
        if key in self.contextualAdvice:
            asset_map = self.contextualAdvice[key]
            if asset in asset_map:
                return asset_map[asset]

        return AdviceEntry(
            asset_name=asset,
            weight=0.0,
            reason="해당 자산에 대한 AI 조언이 없습니다."
        )

    def get_contextual_advices(self, duration: str, tolerance: str) -> Dict[str, AdviceEntry]:
        key = (duration, tolerance)
        return self.contextualAdvice.get(key, {})

    def _parse_forecast(self,asset_name: str, response_text: str) -> Optional[ForecastResult]:
        try:
            parsed = json.loads(response_text)

            return ForecastResult(
                asset_name=asset_name,
                rise_probability_percent=parsed.get("상승", 0),
                fall_probability_percent=parsed.get("하락", 0),
                neutral_probability_percent=parsed.get("보합", 0),
                expected_value_percent=parsed.get("가중", 0)
            )
        except Exception as e:
            print(f"[ERROR] Forecast parsing failed: {e}")
            return None

    def _parse_advice(self, result: str) -> Dict[str, AdviceEntry]:
        try:
            parsed = json.loads(result)  # 문자열 → 딕셔너리
        
            advice_dict = {}
            for asset_name, entry in parsed.items():
                weight = entry.get("비중", 0)
                reason = entry.get("선정이유", "이유 없음")

                # AdviceEntry 객체 생성
                advice = AdviceEntry(
                    asset_name=asset_name,
                    weight=float(weight),
                    reason=reason.strip()
                )
                advice_dict[asset_name.lower()] = advice 
            return advice_dict

        except Exception as e:
            print(f"[ERROR] Advice parsing failed: {e}")
            print(f"[DEBUG] raw result: {result}")
            return {}
