import os
import pandas as pd
from collections import defaultdict

from core.config import BASE_DATA_DIR
from managers.economic_indicator_manager import EconomicIndicatorManager

class SummaryTextBuilder:
    def __init__(self, indicator_manager: EconomicIndicatorManager):
        self.indicator_manager = indicator_manager
        self.data_dir = BASE_DATA_DIR
        self._macro_summary_cache = None
        self._asset_summary_cache = {}

    def get_macro_summary(self) -> str:
        if self._macro_summary_cache:
            return self._macro_summary_cache

        try:
            self.indicator_manager.fetch_all()
            indicators = self.indicator_manager.get_all_indicators()

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
                values = []

                for entry in sorted(entries, key=lambda x: x.date):
                    if isinstance(entry.value, list):
                        values.extend([v for v in entry.value if isinstance(v, (int, float))])
                    elif isinstance(entry.value, (int, float)):
                        values.append(entry.value)

                if values:
                    summary_lines.append(f"{idx}. {label}: {values}")
                else:
                    summary_lines.append(f"{idx}. {label}: 데이터 없음")

            self._macro_summary_cache = "\n".join(summary_lines)
            return self._macro_summary_cache

        except Exception as e:
            print("[WARNING] 경제 지표 요약 실패:", e)

        return (
            "Current Market Price: 520\n"
            "Interest Rate: 6.5%\n"
            "CPI: 4.8%\n"
            "Unemployment Rate: 5.7%\n"
            "Fear and Greed Index: 18\n"
            "3-Month Return: -12.3%"
        )

    def get_asset_summary_all_text(self) -> str:
        if "_all" in self._asset_summary_cache:
            return self._asset_summary_cache["_all"]

        try:
            latest_data_path = self._get_latest_data_dir(self.data_dir)
            summary = self._summarize_asset_data(latest_data_path)
        except Exception as e:
            print("[WARNING] 최신 자산 데이터 요약 실패:", e)
            return "자산 요약 정보를 불러오는 데 실패했습니다."

        lines = ["다음은 최근 1년간 자산별 요약 통계입니다:"]
        for name, stat in summary.items():
            self._asset_summary_cache[name] = stat  # 개별 캐시도 함께 저장
            lines.append(
                f"- {name}: 최근값={stat['최근값']}, 평균={stat['12개월 평균']}, "
                f"증감률={stat['증감률(%)']}%, 표준편차={stat['표준편차']}, "
                f"기울기={stat['기울기']}, 일간변동률={stat['일간 변동률 평균(%)']}%"
            )

        self._asset_summary_cache["_all"] = "\n".join(lines)
        return self._asset_summary_cache["_all"]

    def get_asset_summary_single_text(self, asset_name: str) -> str:
        if asset_name in self._asset_summary_cache:
            stat = self._asset_summary_cache[asset_name]
        else:
            try:
                latest_data_path = self._get_latest_data_dir(self.data_dir)
                stat = self._summarize_single_asset(asset_name, latest_data_path)
                self._asset_summary_cache[asset_name] = stat
            except Exception as e:
                print(f"[WARNING] 자산 통계 로딩 실패 ({asset_name}):", e)
                raise  # 예외를 다시 발생시켜 테스트에서 감지 가능하게 함

        return (
            f"{asset_name} 최근 통계 요약:\n"
            f"- 최근값: {stat['최근값']}, 평균: {stat['12개월 평균']}, "
            f"증감률: {stat['증감률(%)']}%\n"
            f"- 표준편차: {stat['표준편차']}, 기울기: {stat['기울기']}, "
            f"일간 변동률 평균: {stat['일간 변동률 평균(%)']}%"
        )

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

        summary = {}
        for name, file in asset_files.items():
            path = os.path.join(data_dir, file)
            if os.path.exists(path):
                df = pd.read_csv(path)
                stats = self._calc_stats(df, value_columns[name])
                summary[name] = stats
        return summary

    def _summarize_single_asset(self, asset_name: str, data_dir: str = None) -> dict:
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

        if asset_name not in asset_files:
            raise ValueError(f"지원하지 않는 자산명: {asset_name}")

        # 최신 경로 지정이 있으면 사용하고, 없으면 기본 경로 사용
        data_dir = data_dir or self.data_dir
        path = os.path.join(data_dir, asset_files[asset_name])
        print("sr.kim")
        print(path)
        # 파일 존재 여부 확인
        if not os.path.exists(path):
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")

        # 파일이 CSV 형식인지 확인
        if not path.endswith(".csv"):
            raise ValueError(f"잘못된 파일 형식: {path}, CSV 파일이어야 합니다.")

        # CSV 파일 읽기
        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise ValueError(f"CSV 파일 읽기 실패: {e}")

        return self._calc_stats(df, value_columns[asset_name])

    def _calc_stats(self, df: pd.DataFrame, value_col: str) -> dict:
        df = df.rename(columns={value_col: "value"})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").dropna()
        df.set_index("date", inplace=True)

        recent = df[df.index >= df.index.max() - pd.DateOffset(months=36)]
        ma_12 = recent['value'].rolling(window=252).mean()
        slope = lambda s: ((s.dropna().iloc[-1] - s.dropna().iloc[0]) / len(s.dropna())) if len(s.dropna()) > 1 else 0

        return {
            "최근값": round(df["value"].iloc[-1], 2),
            "12개월 평균": round(recent["value"].mean(), 2),
            "증감률(%)": round((df["value"].iloc[-1] - df["value"].iloc[-252]) / df["value"].iloc[-252] * 100, 2) if len(df) > 252 else None,
            "표준편차": round(recent["value"].std(), 2),
            "기울기": round(slope(ma_12), 2),
            "일간 변동률 평균(%)": round(recent["value"].pct_change().abs().mean() * 100, 2),
        }

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
