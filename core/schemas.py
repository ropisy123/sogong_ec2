from pydantic import BaseModel
from dataclasses import dataclass
from typing import Union, List

class ProbabilityForecast(BaseModel):
    asset: str
    rise: float
    hold: float
    fall: float

    @classmethod
    def from_response(cls, asset: str, raw: str):
        # 모의 파싱
        return cls(asset=asset, rise=60, hold=20, fall=20)

class ContextualAdvice(BaseModel):
    period: int
    risk_tolerance: int
    content: str

    @classmethod
    def from_response(cls, period: int, risk_tolerance: int, raw: str):
        return cls(period=period, risk_tolerance=risk_tolerance, content=raw)

class EconomicIndicator(BaseModel):
    name: str                    # 예: "interest_rate"
    date: str                    # 예: "2023-04-01"
    value: Union[float, List[float]]  # 단일값 또는 수치 배열

class ForecastResult(BaseModel):
    asset_name: str  # ⬅️ 추가
    rise_probability_percent: int
    fall_probability_percent: int
    neutral_probability_percent: int
    expected_value_percent: int

class AdviceEntry(BaseModel):
    asset_name: str
    weight: float
    reason: str

@dataclass
class ForecastResult:
    bullish: float
    neutral: float
    bearish: float
    expected_value: float
