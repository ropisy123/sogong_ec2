import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional

from adapters.llm_adapter import LLMAdapter
from adapters.economic_repository import EconomicRepository
from managers.economic_indicator_manager import EconomicIndicatorManager
from builders.prompt_builder import PromptBuilder, SummaryTextBuilder
from core.config import AI_FORCAST_DIR
from core.schemas import ForecastResult, AdviceEntry

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class AIRecommender:
    def __init__(self, llm_adapter=None):
        logger.info("AIRecommender 초기화 중...")
        self.llm = llm_adapter or LLMAdapter()
        self.prompt_builder = PromptBuilder(SummaryTextBuilder(EconomicIndicatorManager(EconomicRepository())))
        self.base_data_dir = AI_FORCAST_DIR
        self.probabilityForecast: Dict[str, ForecastResult] = {} # 자산별 예측치 저장
        self.contextualAdvice: Dict[Tuple[str, str], Dict[str, AdviceEntry]] = {}   # 자산별 권장비중 및 선정 이유 저장

    def generate_forecast(self, asset: str, save_dir: str) -> ForecastResult:
        logger.info(f"{asset} 예측 중...")
        forecast_result = self._run_debate_and_get_trader_result(asset, save_dir)
        parsed_forecast = self._parse_forecast(asset, forecast_result, True)
        return parsed_forecast

    def generate_portfolio_advice(self, forecasts: Dict[str, ForecastResult], duration: str, tolerance: str) -> Dict[str, AdviceEntry]:
        prompt = self.prompt_builder.build_portfolio_advice_prompt(forecasts, duration, tolerance)
        result = self.llm.call_beta(prompt)
        return self._parse_advice(result)

    def generate_and_save_forecasts_and_advice(self, repository):
        date_folder = datetime.today().strftime("%Y%m%d")
        save_dir = os.path.join(self.base_data_dir, date_folder)
        os.makedirs(save_dir, exist_ok=True)

        assets = ["S&P500", "KOSPI", "비트코인", "금", "부동산"]
        all_forecasts = {}

        for asset in assets:
            result = self.generate_forecast(asset, save_dir)
            all_forecasts[asset] = result

        repository.save_forecast(all_forecasts)

        for duration in ["1년", "3년", "5년", "10년"]:
            for tolerance in ["5%", "10%", "20%"]:
                advice = self.generate_portfolio_advice(all_forecasts, duration, tolerance)
                repository.save_advice(date_folder, advice, duration, tolerance)

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

    def _run_debate_and_get_trader_result(self, asset: str, save_dir: str) -> dict:
        logger.info(f"[{asset}] 토론 시작")
        prompts_responses = {}

        def _call_and_store(name, prompt_func, *args):
            prompt = prompt_func(*args)
            response = self.llm.call_beta(prompt)
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
    
    def _parse_forecast(self,asset_name: str, response_text: str, is_beta: bool = False) -> Optional[ForecastResult]:
        try:
            parsed = json.loads(response_text)
            if is_beta:
                return ForecastResult(
                    asset_name=asset_name,
                    rise_probability_percent=parsed.get("상승확률", 0),
                    fall_probability_percent=parsed.get("하락확률", 0),
                    neutral_probability_percent=parsed.get("보합확률", 0),
                    expected_value_percent=parsed.get("기대수익률", 0)
                )
            else: 
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
        """
        LLM으로부터 받은 포트폴리오 추천 응답을 파싱하여 자산별 AdviceEntry로 변환합니다.

        예시 입력:
        {
            "채권": {"자산명": "채권", "권장비중": 20.0, "선정이유": "안정적 수익을 위한 선택"},
            "금": {"자산명": "금", "권장비중": 15.0, "선정이유": "인플레이션 헷지"},
            ...
        }
        """
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
