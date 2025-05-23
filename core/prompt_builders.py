from managers.economic_indicator_manager import EconomicIndicatorManager
from typing import Dict

class PromptBuilder:
    def __init__(self, indicator_manager: EconomicIndicatorManager):
        self.indicator_manager = indicator_manager

    def build_contextual_advice_prompt(self, investment_period: str, max_loss_tolerance: str) -> str:
        # 거시 지표를 텍스트 형태로 요약
        indicators = self.indicator_manager.get_all_indicators()
        indicator_summary = self._summarize_indicators(indicators)

        prompt = (
            f"당신은 경제 분석가입니다. 사용자가 {investment_period} 동안 "
            f"{max_loss_tolerance}의 손실을 감수할 수 있다고 가정할 때,\n"
            f"{indicator_summary}"
            "다음 자산들의 100% 기준 투자 비중 % 및 투자 관점에서의 요약을 1~2줄씩 해주세요:\n\n"
            "- 채권\n"
            "- 금\n"
            "- 나스닥\n"
            "- 미국 대형 가치주\n"
            "- 비트코인\n"
            "- 서울 부동산\n\n"
            "친절하지만 간결하게 요약해 주세요. 이모지도 허용됩니다."
        )
        return prompt

    def build_probability_forecast_prompt(self, asset_name: str) -> str:
        return (
            f"당신은 경제 분석가입니다. {asset_name}의 향후 예상치의 상승, 하락, 보합 각각의 예상 %를 알려주고, "
            "확률 가중 기대치가 하락 -100%, 보합 0%, 상승 100% 기준으로 표시할 때 "
            "몇 % (-100% ~ 100% 사이의 값) 가 될지 알려줘"
        )

    def _summarize_indicators(self, indicators: Dict[str, list]) -> str:
        """
        거시 지표들을 요약 텍스트 형태로 구성 (데모용 간단한 요약)
        """
        summary_lines = []
        for name, series in indicators.items():
            if not series:
                continue
            latest = series[-1]
            summary_lines.append(f"- 최신 {name.replace('_', ' ')}: {latest.value} ({latest.date})")
        return "현재 거시 경제 지표는 다음과 같습니다:\n" + "\n".join(summary_lines) + "\n\n"
