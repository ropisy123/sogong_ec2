from managers.economic_indicator_manager import EconomicIndicatorManager
from typing import Dict
from datetime import datetime


def get_current_date_string():
    return datetime.today().strftime("%Y년 %m월 %d일")


class PromptBuilder:
    def __init__(self, indicator_manager: EconomicIndicatorManager):
        self.indicator_manager = indicator_manager

    def _current_date_string(self) -> str:
        return datetime.today().strftime("%Y년 %m월 %d일")

    def _get_economic_data_block(self) -> str:
        try:
            indicators = self.indicator_manager.get_all_indicators()
            lines = [
                f"- 최신 {k.replace('_', ' ')}: {v[-1].value} ({v[-1].date})"
                for k, v in indicators.items() if v
            ]
            if lines:
                return "\n".join(lines)
        except Exception as e:
            print("[WARNING] 경제 지표 불러오기 실패, 기본값 사용:", e)

        return (
            "Current Market Price: 457\n"
            "Interest Rate: 5.25%\n"
            "CPI: 3.2%\n"
            "Unemployment Rate: 3.8%\n"
            "Fear and Greed Index: 45\n"
            "3-Month Return: -10.3%"
        )
    
    def build_contextual_advice_prompt(self, investment_period: str, max_loss_tolerance: str) -> str:
        indicators = self.indicator_manager.get_all_indicators()
        indicator_summary = self._summarize_indicators(indicators)

        return (
            f"당신은 경제 분석가입니다. 사용자가 {investment_period} 동안 {max_loss_tolerance}의 손실을 감수할 수 있다고 가정할 때,\n"
            f"{indicator_summary}"
            "다음 자산들의 100% 기준 투자 비중 % 및 투자 관점에서의 요약을 1~2줄씩 해주세요:\n\n"
            "- 채권\n"
            "- 금\n"
            "- 나스닥\n"
            "- 미국 대형 가치주\n"
            "- 비트코인\n"
            "- 서울 부동산\n\n"
            "친절하지만 간결하게 요약해 주세요."
        )

    def build_probability_forecast_prompt(self, asset_name: str) -> str:
        return (
            f"당신은 경제 분석가입니다. {asset_name}의 향후 예상치의 상승, 하락, 보합 각각의 예상 %를 알려주고, "
            "확률 가중 기대치가 하락 -100%, 보합 0%, 상승 100% 기준으로 표시할 때 "
            "몇 % (-100% ~ 100% 사이의 값) 가 될지 알려줘"
        )

    def _summarize_indicators(self, indicators: Dict[str, list]) -> str:
        summary_lines = []
        for name, series in indicators.items():
            if not series:
                continue
            latest = series[-1]
            summary_lines.append(f"- 최신 {name.replace('_', ' ')}: {latest.value} ({latest.date})")
        return "현재 거시 경제 지표는 다음과 같습니다:\n" + "\n".join(summary_lines) + "\n\n"

    def build_bullish_prompt(self, asset_name: str) -> str:
        current_date = self._current_date_string()
        economic_data = self._get_economic_data_block()
        return f"""당신은 {asset_name}에 대해 낙관적인 관점을 가진 투자 애널리스트입니다.
현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.

현재 시장 지표 요약:
{economic_data}

다음 구조에 따라 5문장 이내로 구조화된 투자 의견을 작성하세요.
1. 거시경제 흐름 기반의 긍정적 요인
2. 밸류에이션 매력 또는 수급상 이점
3. 향후 상승 가능성을 지지하는 촉매 또는 이벤트

주의사항:
- 과거 수익률/가격, 기술적 지표, 재무 약어는 사용하지 마세요.
"""

    def build_bearish_prompt(self, asset_name: str) -> str:
        current_date = self._current_date_string()
        economic_data = self._get_economic_data_block()
        return f"""당신은 {asset_name}에 대해 비관적인 관점을 가진 투자 애널리스트입니다.
현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.

현재 시장 지표 요약:
{economic_data}

다음 구조에 따라 5문장 이내로 구조화된 투자 의견을 작성하세요.
1. 거시경제 리스크 또는 침체 가능성
2. 과대평가 우려 또는 펀더멘털 저하
3. 향후 하락 요인 또는 투자심리 악화 가능성

주의사항:
- 과거 수익률/가격, 기술적 지표, 재무 약어는 사용하지 마세요.
"""

    def build_bearish_rebuttal_prompt(self, previous_response: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        economic_data = self._get_economic_data_block()
        return f"""당신은 {asset_name}에 대한 낙관적 분석을 반박하는 비관적 애널리스트입니다.
현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.

현재 시장 지표 요약:
{economic_data}

다음은 낙관적 관점의 분석입니다:
\"\"\"{previous_response}\"\"\"

이 분석의 약점을 지적하는 비판적 의견을 3~4문장 이내로 작성하세요.
- 과도한 낙관성, 증거 부족, 리스크 무시에 초점을 맞추되, 논리적이고 비공격적으로 작성하세요.

주의사항:
- 과거 수치, 기술적 지표, 재무 약어는 사용하지 마세요.
"""

    def build_bullish_rebuttal_prompt(self, previous_response: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        economic_data = self._get_economic_data_block()
        return f"""당신은 {asset_name}에 대한 비관적 분석을 반박하는 낙관적 애널리스트입니다.
현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.

현재 시장 지표 요약:
{economic_data}

다음은 비관적 관점의 분석입니다:
\"\"\"{previous_response}\"\"\"

이 분석의 약점을 지적하는 반론을 3~4문장 이내로 작성하세요.
- 과도한 우려, 생략된 긍정 요인, 시각적 편향 등에 초점을 맞추되, 논리적인 낙관적 관점을 제시하세요.

주의사항:
- 과거 수치, 기술적 지표, 재무 약어는 사용하지 마세요.
"""

    def build_trader_prompt(self, debate_summary: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        economic_data = self._get_economic_data_block()

        return f"""당신은 {asset_name} 투자 판단을 최종적으로 내리는 전문 트레이더입니다.
당신의 임무는 아래의 시장 지표와 애널리스트 토론 내용을 종합적으로 분석하여,  
향후 3개월 내 {asset_name}의 방향(상승/보합/하락) 과 예상 수익률을 정량적으로 추정하고,  
그에 따른 명확한 투자의견(Buy/Hold/Sell) 을 제시하는 것입니다.  
현재 날짜는 {current_date}이며, 판단은 반드시 이 시점의 시장 상황을 반영해야 합니다.

현재 시장 지표 요약:
{economic_data}

다음은 낙관적·비관적 애널리스트 간의 토론 내용입니다:
\"\"\"{debate_summary}\"\"\"

다음 항목들을 포함한 JSON 형식으로 정확하게 응답하세요:
- 상승확률 (0.0 ~ 1.0)
- 보합확률 (0.0 ~ 1.0)
- 하락확률 (0.0 ~ 1.0)
- 상승시수익률 (%)
- 보합시수익률 (%)
- 하락시수익률 (%)
- 기대수익률 (%)
- 투자의견: 'Strong Buy', 'Buy', 'Hold', 'Sell'
- 의견요약 (2~3문장)

주의사항:
1. 숫자와 판단은 반드시 시장 지표와 토론 내용을 기반으로 작성하세요.
2. '의견요약'에는 회피 표현 없이 명확한 입장을 서술하세요.
3. 과거 수익률, 기술적 지표, 재무 약어, 임의 수치는 포함하지 마세요.
"""