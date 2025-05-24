import os
import csv
import logging
from datetime import datetime
from typing import Dict, Tuple
from adapters.llm_adapter import LLMAdapter
from adapters.economic_repository import EconomicRepository
from core.config import AI_FORCAST_DIR
from core.prompt_builders import PromptBuilder
from core.schemas import ForecastResult, AdviceEntry
from managers.economic_indicator_manager import EconomicIndicatorManager

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # 필요 시 DEBUG로 변경 가능
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class AIRecommender:
    def __init__(self):
        logger.info("AIRecommender 초기화 중...")
        self.llm = LLMAdapter()
        self.prompt_builder = PromptBuilder(EconomicIndicatorManager(EconomicRepository))
        self.base_data_dir = AI_FORCAST_DIR
        self.probabilityForecast: Dict[str, ForecastResult] = {}
        self.contextualAdvice: Dict[Tuple[str, str], Dict[str, AdviceEntry]] = {}
        logger.info("AIRecommender 초기화 완료")

    def fetch_probability_forecast(self):
        logger.info("자산별 예측 생성 시작")
        date_folder = datetime.today().strftime("%Y%m%d")
        save_dir = os.path.join(self.base_data_dir, date_folder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "forecast.csv")
        logger.info(f"예측 결과 저장 경로: {save_path}")

        try:
            with open(save_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["asset", "bullish", "neutral", "bearish", "expected_value"])

                for asset in ["S&P 500"]:
                    logger.info(f"{asset} 예측 중...")
                    result = self._run_debate_and_get_trader_result(asset)
                    parsed = self._parse_forecast(result)
                    writer.writerow([asset, parsed.bullish, parsed.neutral, parsed.bearish, parsed.expected_value])
                    logger.info(f"{asset} 예측 완료: {parsed}")
        except Exception as e:
            logger.error(f"예측 결과 저장 실패: {e}")

    def fetch_contextual_advice(self):
        logger.info("권장 비중 생성 시작")
        durations = ["1년", "3년", "5년", "10년"]
        tolerances = ["5%", "10%", "20%"]
        for duration in durations:
            for tolerance in tolerances:
                logger.info(f"Contextual Advice: 기간={duration}, 허용 MDD={tolerance}")
                prompt = self.prompt_builder.build_contextual_advice_prompt(duration, tolerance)
                result = self.llm.call(prompt)
                parsed = self._parse_advice(result)
                self.contextualAdvice[(duration, tolerance)] = parsed
                logger.info(f"→ 자산 수: {len(parsed)}")

    def get_probability_forecast(self, asset: str) -> ForecastResult:
        latest_folder = self._get_latest_available_folder()
        path = os.path.join(self.base_data_dir, latest_folder, "forecast.csv")
        logger.info(f"{asset} 예측 결과 불러오기: {path}")
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["asset"] == asset:
                        result = ForecastResult(
                            bullish=float(row["bullish"]),
                            neutral=float(row["neutral"]),
                            bearish=float(row["bearish"]),
                            expected_value=float(row["expected_value"])
                        )
                        logger.debug(f"로드된 예측 결과: {result}")
                        return result
        except Exception as e:
            logger.error(f"CSV 읽기 실패: {e}")

        return ForecastResult(0.0, 0.0, 0.0, 0.0)

    def get_contextual_advice(self, asset: str, duration: str, tolerance: str) -> AdviceEntry:
        advice_map = self.contextualAdvice.get((duration, tolerance), {})
        return advice_map.get(asset, AdviceEntry(
            asset_name=asset,
            allocation_ratio=0.0,
            rationale="해당 자산에 대한 정보가 없습니다."
        ))

    def _get_latest_available_folder(self) -> str:
        logger.debug(f"최신 결과 폴더 탐색 중 in {self.base_data_dir}")
        folders = [
            f for f in os.listdir(self.base_data_dir)
            if os.path.isdir(os.path.join(self.base_data_dir, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("No data folders found in forecast_results/")
        latest = max(folders)
        logger.debug(f"최신 폴더: {latest}")
        return latest

    def _run_debate_and_get_trader_result(self, asset: str):
        logger.info(f"[{asset}] 토론 시작")

        p_bull1 = self.prompt_builder.build_bullish_prompt(asset)
        bull1 = self.llm.call(p_bull1)
        logger.debug(f"[{asset}] [PROMPT] Bullish #1:\n{p_bull1}")
        logger.debug(f"[{asset}] [RESPONSE] Bullish #1:\n{bull1}")

        p_bear1 = self.prompt_builder.build_bearish_prompt(asset)
        bear1 = self.llm.call(p_bear1)
        logger.debug(f"[{asset}] [PROMPT] Bearish #1:\n{p_bear1}")
        logger.debug(f"[{asset}] [RESPONSE] Bearish #1:\n{bear1}")

        p_bear2 = self.prompt_builder.build_bearish_rebuttal_prompt(bull1, asset)
        bear2 = self.llm.call(p_bear2)
        logger.debug(f"[{asset}] [PROMPT] Bearish #2 (rebut Bull #1):\n{p_bear2}")
        logger.debug(f"[{asset}] [RESPONSE] Bearish #2:\n{bear2}")

        p_bull2 = self.prompt_builder.build_bullish_rebuttal_prompt(bear1, asset)
        bull2 = self.llm.call(p_bull2)
        logger.debug(f"[{asset}] [PROMPT] Bullish #2 (rebut Bear #1):\n{p_bull2}")
        logger.debug(f"[{asset}] [RESPONSE] Bullish #2:\n{bull2}")

        debate_summary = (
            f"[Bullish #1]\n{bull1}\n\n"
            f"[Bearish #1]\n{bear1}\n\n"
            f"[Bearish #2]\n{bear2}\n\n"
            f"[Bullish #2]\n{bull2}"
        )
        p_trader = self.prompt_builder.build_trader_prompt(debate_summary, asset)
        result = self.llm.call(p_trader, return_json=True)

        if not result:
            logger.warning(f"[{asset}] LLM 응답이 비어 있습니다. 원문 출력:")
            result_raw = self.llm.call(p_trader, return_json=False)
            logger.debug(result_raw)

        logger.debug(f"[{asset}] [PROMPT] Trader Judgment:\n{p_trader}")
        logger.info(f"[{asset}] 토론 결과 완료 → 결과: {result}")

        return result

    def _parse_forecast(self, result: dict) -> ForecastResult:
        try:
            parsed = ForecastResult(
                bullish=float(result.get("상승확률", 0.0)),
                neutral=float(result.get("보합확률", 0.0)),
                bearish=float(result.get("하락확률", 0.0)),
                expected_value=float(result.get("기대수익률", 0.0))
            )
            logger.debug(f"파싱된 예측 결과: {parsed}")
            return parsed
        except Exception as e:
            logger.error(f"Forecast parsing failed: {e}")
            return ForecastResult(0.0, 0.0, 0.0, 0.0)

    def _parse_advice(self, result: str) -> Dict[str, AdviceEntry]:
        try:
            parsed = eval(result) if isinstance(result, str) else result
            advice_map = {
                asset: AdviceEntry(
                    asset_name=entry.get("자산명", asset),
                    allocation_ratio=float(entry.get("권장비중", 0.0)),
                    rationale=entry.get("선정이유", "정보 없음")
                )
                for asset, entry in parsed.items()
            }
            logger.debug(f"파싱된 조언: {advice_map}")
            return advice_map
        except Exception as e:
            logger.error(f"Advice parsing failed: {e}")
            return {}
