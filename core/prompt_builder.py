import os
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import EconomicIndicator
from core.config import BASE_DATA_DIR
from collections import defaultdict
from typing import Dict, List
from datetime import datetime
import pandas as pd

class PromptBuilder:
    def __init__(self, indicator_manager: EconomicIndicatorManager):
        self.indicator_manager = indicator_manager

    def build_contextual_advice_prompt(self, investment_period: str, max_loss_tolerance: str) -> str:
        # 거시 지표 요약
        self.indicator_manager.fetch_all()
        indicators = self.indicator_manager.get_all_indicators()
        indicator_summary = self._summarize_indicators(indicators)

        # 자산 통계 요약
        latest_data_path = self._get_latest_data_dir(BASE_DATA_DIR)
        asset_stats = self._summarize_asset_data(latest_data_path)

        # 요약 텍스트 구성
        asset_text = "다음은 최근 1년간 자산별 요약 통계입니다:\n"
        for name, stat in asset_stats.items():
            asset_text += f"- {name}: 최근값={stat['최근값']}, 평균={stat['12개월 평균']}, 증감률={stat['증감률(%)']}%, 표준편차={stat['표준편차']}, 기울기={stat['기울기']}, 일간변동률={stat['일간 변동률 평균(%)']}%\n"

        # 프롬프트 생성
        prompt = (
            f"당신은 경제 분석가입니다. 사용자가 {investment_period} 동안 {max_loss_tolerance}의 손실을 감수할 수 있다고 가정할 때,\n"
            "다음 자산들의 100% 기준 투자 비중 % 및 그 이유를 최근 시장 통계 기반으로 2~4줄씩 요약해 주세요:\n"
            "- S&P500\n- KOSPI\n- 비트코인\n- 금\n- 부동산\n- 현금성자산\n\n"
            "다음은 참고용 거시경제 지표와 자산 통계입니다:\n\n"
            f"{indicator_summary}\n\n{asset_text}\n\n"
            "다음 JSON 형식으로만 응답해주세요. 마크다운 없이 순수 JSON으로:\n"
            "{\n"
            '  "SP500": {"비중": int, "선정이유": str},\n'
            '  "KOSPI": {"비중": int, "선정이유": str},\n'
            '  "비트코인": {"비중": int, "선정이유": str},\n'
            '  "금": {"비중": int, "선정이유": str},\n'
            '  "부동산": {"비중": int, "선정이유": str},\n'
            '  "현금성자산": {"비중": int, "선정이유": str}\n'
            "}"
        )
        return prompt

    def build_probability_forecast_prompt(self, asset: str) -> str:
        return (
            f"당신은 경제 분석가 입니다. {asset}의 향후 예상치의 상승, 하락, 보합 각각의 예상 %와 "
            "확률 가중 기대치가 하락 -100%, 보합 0%, 상승 100% 기준으로 계산 될 때, "
            "-100% ~ 100% 사이의 값으로 몇 %가 되는지 4가지의 값을 다음 형식으로 JSON으로만 응답해주세요. "
            "마크다운 코드블럭 없이 순수한 JSON으로 출력하세요.\n\n"
            '{\n'
            '  "상승": int,\n'
            '  "하락": int,\n'
            '  "보합": int,\n'
            '  "가중": int\n'
            '}'
        )

    def _summarize_indicators(self, indicators: List[EconomicIndicator]) -> str:
        INDICATOR_LABELS = {
            "cpi": "미국 소비자물가지수(CPI)",
            "ppi": "생산자물가지수(PPI)",
            "nonfarm": "비농업 고용자 수",
            "retail": "미국 소매판매지수",
            "unemployment": "미국 실업률"
        }

        grouped = defaultdict(list)
        for indicator in indicators:
            grouped[indicator.name].append(indicator)

        summary_lines = ["아래의 최근 1년간 월간 경제 지표를 참조해서"]
        for idx, (name, entries) in enumerate(grouped.items(), 1):
            label = INDICATOR_LABELS.get(name, name)

            values: List[float] = []
            for entry in sorted(entries, key=lambda x: x.date):
                if isinstance(entry.value, list):
                    values.extend([v for v in entry.value if isinstance(v, (int, float))])
                elif isinstance(entry.value, (int, float)):
                    values.append(entry.value)

            if values:
                summary_lines.append(f"{idx}. {label}: {values}")
            else:
                summary_lines.append(f"{idx}. {label}: 데이터 없음")

        return "\n".join(summary_lines)

    def _summarize_asset_data(self, data_dir: str) -> dict:
        asset_files = {
            "S&P500": "sp500.csv",
            "KOSPI": "kospi.csv",
            "비트코인": "bitcoin.csv",
            "금": "gold.csv",
            "부동산": "real_estate.csv"
        }

        value_columns = {
            "S&P500": "sp500",
            "KOSPI": "kospi",
            "비트코인": "bitcoin",
            "금": "gold",
            "부동산": "real_estate"
        }

        def calc_stats(df, value_col):
            df = df.rename(columns={"date": "date", value_col: "value"})
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").dropna()
            df.set_index("date", inplace=True)

            recent = df[df.index >= df.index.max() - pd.DateOffset(months=36)]
            slope = lambda s: ((s.dropna().iloc[-1] - s.dropna().iloc[0]) / len(s.dropna())) if len(s.dropna()) > 1 else 0
            ma_12 = recent['value'].rolling(window=252).mean()

            return {
                "최근값": round(df["value"].iloc[-1], 2),
                "12개월 평균": round(recent["value"].mean(), 2),
                "증감률(%)": round((df["value"].iloc[-1] - df["value"].iloc[-252]) / df["value"].iloc[-252] * 100, 2) if len(df) > 252 else None,
                "표준편차": round(recent["value"].std(), 2),
                "기울기": round(slope(ma_12), 2),
                "일간 변동률 평균(%)": round(recent["value"].pct_change().abs().mean() * 100, 2),
            }

        summary = {}
        for name, file in asset_files.items():
            path = os.path.join(data_dir, file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                stats = calc_stats(df, value_columns[name])
                summary[name] = stats
        return summary

    def _get_latest_data_dir(self, base_dir: str) -> str:
        folders = [
            f for f in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, f)) and f.isdigit()
        ]
        if not folders:
            raise FileNotFoundError("📂 데이터 폴더가 존재하지 않습니다.")

        # 문자열 → 날짜로 정렬
        latest = max(folders)
        return os.path.join(base_dir, latest)
