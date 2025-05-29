from datetime import datetime
from typing import Dict, List

from builders.summary_text_builder import SummaryTextBuilder
from managers.economic_indicator_manager import EconomicIndicatorManager
from core.schemas import ForecastResult

class PromptBuilder:
    def __init__(self, summary_builder: SummaryTextBuilder):
        self.summary_builder = summary_builder

    def build_contextual_advice_prompt(self, investment_period: str, max_loss_tolerance: str) -> str:
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_text = self.summary_builder.get_asset_summary_all_text()

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

    def build_bullish_prompt(self, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name}에 대해 낙관적인 관점을 가진 투자 애널리스트입니다.",
            f"현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.",
            "",
            "현재 시장 지표 요약:",
            indicator_summary,
            "",
            asset_summary,
            "",
            "다음 구조에 따라 5문장 이내로 정리된 투자 의견을 작성하고, 3개월 후 예상 수익률(%)을 정량적으로 제시하세요.",
            "- 거시경제 흐름 기반의 긍정적 요인",
            "- 밸류에이션 매력 또는 수급상 이점",
            "- 향후 상승 가능성을 지지하는 촉매 또는 이벤트",
            "",
            "작성 스타일 지침:",
            "- 굵은 글씨는 사용하지 마세요.",
            "- 과거 수익률/가격, 기술적 지표, 재무 약어는 사용하지 마세요."
        ]
        return "\n".join(lines)

    def build_bearish_prompt(self, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name}에 대해 비관적인 관점을 가진 투자 애널리스트입니다.",
            f"현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.",
            "",
            "현재 시장 지표 요약:",
            indicator_summary,
            "",
            asset_summary,
            "",
            "다음 구조에 따라 5문장 이내로 정리된 투자 의견을 작성하고, 3개월 후 예상 수익률(%)을 정량적으로 제시하세요.",
            "- 거시경제 리스크 또는 침체 가능성",
            "- 과대평가 우려 또는 펀더멘털 저하",
            "- 향후 하락 요인 또는 투자심리 악화 가능성",
            "",
            "작성 스타일 지침:",
            "- 굵은 글씨는 사용하지 마세요.",
            "- 과거 수익률/가격, 기술적 지표, 재무 약어는 사용하지 마세요."
        ]
        return "\n".join(lines)

    def build_bearish_rebuttal_prompt(self, previous_response: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name}에 대한 낙관적 분석을 반박하는 비관적 애널리스트입니다.",
            f"현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.",
            "",
            "현재 시장 지표 요약:",
            indicator_summary,
            "",
            asset_summary,
            "다음은 낙관적 관점의 분석입니다:",
            previous_response,
            "",
            "이 분석의 약점을 지적하는 반론을 3문장 이내로 작성하세요.",
            "- 과도한 낙관성, 증거 부족, 리스크 무시에 초점을 맞추되, 논리적이고 비공격적으로 작성하세요.",
            "",
            "작성 스타일 지침:",
            "- 굵은 글씨는 사용하지 마세요.",
            "- 과거 수치, 기술적 지표, 재무 약어는 사용하지 마세요."
        ]
        return "\n".join(lines)

    def build_bullish_rebuttal_prompt(self, previous_response: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name}에 대한 비관적 분석을 반박하는 낙관적 애널리스트입니다.",
            f"현재 날짜는 {current_date}이며, 분석은 반드시 이 시점의 경제 상황을 반영해야 합니다.",
            "",
            "현재 시장 지표 요약:",
            indicator_summary,
            "",
            asset_summary,
            "다음은 비관적 관점의 분석입니다:",
            previous_response,
            "",
            "이 분석의 약점을 지적하는 반론을 3문장 이내로 작성하세요.",
            "- 과도한 우려, 생략된 긍정 요인, 시각적 편향 등에 초점을 맞추되, 논리적인 낙관적 관점을 제시하세요.",
            "",
            "작성 스타일 지침:",
            "- 굵은 글씨는 사용하지 마세요.",
            "- 과거 수치, 기술적 지표, 재무 약어는 사용하지 마세요."
        ]
        return "\n".join(lines)

    def build_trader_prompt(self, debate_summary: str, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name} 투자 판단을 최종적으로 내리는 전문 트레이더입니다.",
            "당신의 임무는 아래의 애널리스트 토론 내용을 종합적으로 분석하여,",
            f"향후 3개월 내 {asset_name}의 방향(상승/보합/하락)과 예상 수익률을 정량적으로 추정해야 합니다.",
            f"현재 날짜는 {current_date}이며, 판단은 반드시 이 시점의 시장 상황과 최근 추세를 반영해야 합니다.",
            "",
            "다음은 낙관적·비관적 애널리스트 간의 토론 내용입니다.",
            "이 토론은 서로 상반된 논거를 제시하고 있으며,",
            "당신은 각 주장에 대한 설득력과 시장 지표와의 정합성을 바탕으로,",
            "어떤 입장이 더 타당한지를 비교·분석하여 최종 판단을 내려야 합니다.",
            f'"""{debate_summary}"""',
            "",
            "아래 항목들을 포함한 JSON 형식으로 정확하게 응답하세요:",
            "- 상승확률 (0.0 ~ 1.0)",
            "- 보합확률 (0.0 ~ 1.0)",
            "- 하락확률 (0.0 ~ 1.0)",
            "- 상승시수익률 (%)",
            "- 보합시수익률 (%)",
            "- 하락시수익률 (%)",
            "- 기대수익률 (%)",
            "- 의견요약 (2~3문장)",
            "",
            "판단 기준 안내:",
            "- 기대수익률은 다음 공식에 따라 계산하세요:",
            "  기대수익률 = (상승확률 × 상승시수익률) + (보합확률 × 보합시수익률) + (하락확률 × 하락시수익률)",
            "- 예측 수익률 범위는 자산과 시장 환경에 따라 -50%에서 +50% 이상도 가능하므로, 실제 시장 변동성을 반영해 유연하게 판단하십시오.",
            "- 애널리스트가 제시한 수익률이 강하고, 그 논거가 시장 지표와 정합성이 있을 경우, 보수적 축소 없이 적극적으로 반영하십시오.",
            "- 보합 확률은 실제 중립적 근거가 명확할 때만 설정하십시오. 애매한 경우 회피 판단으로 간주됩니다.",
            "- 확률과 수익률 간의 논리적 일관성을 반드시 유지하십시오. 예: 상승확률이 가장 높다면 기대수익률은 양(+)이어야 합니다.",
            "",
            "주의사항:",
            "1. 판단은 반드시 위 토론 내용과 아래 시장 지표 요약을 기반으로 작성해야 합니다.",
            "2. 애널리스트들이 언급한 수익률 수치를 그대로 복사하지 말고, 논리를 바탕으로 직접 수치를 판단하세요.",
            "3. '의견요약'에는 회피 표현 없이 명확한 입장을 서술하세요.",
            "4. 과거 수익률, 기술적 지표, 재무 약어, 임의 수치는 포함하지 마세요.",
            "",
            "--- 참고용: 현재 시장 지표 요약 ---",
            indicator_summary,
            "",
            "--- 참고용: 자산 정보 요약 ---",
            asset_summary,
        ]
        return "\n".join(lines)


    def build_trader_prompt_wo_debate(self, asset_name: str) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_single_text(asset_name)

        lines = [
            f"당신은 {asset_name} 투자 판단을 최종적으로 내리는 전문 트레이더입니다.",
            f"향후 3개월 내 {asset_name}의 방향(상승/보합/하락)과 예상 수익률을 정량적으로 추정해야 합니다.",
            f"현재 날짜는 {current_date}이며, 판단은 반드시 이 시점의 시장 상황과 최근 추세를 반영해야 합니다.",
            "",
            "--- 참고용: 현재 시장 지표 요약 ---",
            indicator_summary,
            "",
            "--- 참고용: 자산 정보 요약 ---",
            asset_summary,
            "",
            "아래 항목들을 포함한 JSON 형식으로 정확하게 응답하세요:",
            "- 상승확률 (0.0 ~ 1.0)",
            "- 보합확률 (0.0 ~ 1.0)",
            "- 하락확률 (0.0 ~ 1.0)",
            "- 상승시수익률 (%)",
            "- 보합시수익률 (%)",
            "- 하락시수익률 (%)",
            "- 기대수익률 (%)",
            "- 의견요약 (2~3문장)",
            "",
            "판단 기준 안내:",
            "- 기대수익률은 다음 공식에 따라 계산하세요:",
            "  기대수익률 = (상승확률 × 상승시수익률) + (보합확률 × 보합시수익률) + (하락확률 × 하락시수익률)",
            "- 예측 수익률 범위는 자산과 시장 환경에 따라 -50%에서 +50% 이상도 가능하므로, 실제 시장 변동성을 반영해 유연하게 판단하십시오.",
            "- 애널리스트가 제시한 수익률이 강하고, 그 논거가 시장 지표와 정합성이 있을 경우, 보수적 축소 없이 적극적으로 반영하십시오.",
            "- 보합 확률은 실제 중립적 근거가 명확할 때만 설정하십시오. 애매한 경우 회피 판단으로 간주됩니다.",
            "- 확률과 수익률 간의 논리적 일관성을 반드시 유지하십시오. 예: 상승확률이 가장 높다면 기대수익률은 양(+)이어야 합니다.",
            "",
            "주의사항:",
            "1. 판단은 반드시 위에 제공된 시장 지표와 자산 정보를 기반으로 작성해야 합니다.",
            "2. 어떤 수익률 수치를 그대로 복사하지 말고, 논리를 바탕으로 직접 수치를 판단하세요.",
            "3. '의견요약'에는 회피 표현 없이 명확한 입장을 서술하세요.",
            "4. 과거 수익률, 기술적 지표, 재무 약어, 임의 수치는 포함하지 마세요."
        ]
        return "\n".join(lines)

    def build_portfolio_advice_prompt(
        self,
        forecasts: Dict[str, ForecastResult],
        investment_period: str,
        max_loss_tolerance: str
    ) -> str:
        current_date = self._current_date_string()
        indicator_summary = self.summary_builder.get_macro_summary()
        asset_summary = self.summary_builder.get_asset_summary_all_text()

        asset_lines = []
        for asset, forecast in forecasts.items():
            asset_lines.extend([
                f"- {asset}",
                f"  • 상승 확률: {forecast.bullish * 100:.1f}%",
                f"  • 보합 확률: {forecast.neutral * 100:.1f}%",
                f"  • 하락 확률: {forecast.bearish * 100:.1f}%",
                f"  • 기대 수익률: {forecast.expected_value:.2f}%",
            ])

        forecast_summary = "\n".join(asset_lines)

        lines = [
            f"[{current_date} 기준 경제 지표]",
            indicator_summary,
            "",
            asset_summary,
            "",
            "[예측 정보 기반 포트폴리오 추천 요청]",
            f"사용자가 {investment_period} 동안 {max_loss_tolerance}의 손실을 감수할 수 있다고 가정할 때,",
            "다음 자산들의 예측 정보를 참고하여 포트폴리오를 구성해 주세요:",
            "",
            forecast_summary,
            "",
            "총합 100%가 되도록 투자 비중을 아래 형식으로 추천하고, 각 자산에 대한 선정 이유도 1~2문장으로 작성해 주세요.",
            "",
            "형식 (Python dict):",
            '{',
            '  "채권": {"자산명": "채권", "권장비중": 20.0, "선정이유": "시장 불확실성에 대비한 안정적 수익 기대"},',
            '  "금": {"자산명": "금", "권장비중": 15.0, "선정이유": "인플레이션 헷지 및 안전자산"},',
            '  ...',
            '}',
            "",
            "- 반드시 큰따옴표(\") 사용, 코드 블록 없이 출력해 주세요.",
            "- true / false / null 대신 한국어 표현 사용",
            "- 이모지 허용",
            "",
            "자산 목록:",
            "- 채권",
            "- 금",
            "- 나스닥",
            "- 미국 대형 가치주",
            "- 비트코인",
            "- 서울 부동산"
        ]
        return "\n".join(lines)

    def _current_date_string(self):
        return datetime.today().strftime("%Y년 %m월 %d일")
