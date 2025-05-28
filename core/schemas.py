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
'''
class ForecastResult(BaseModel):
    asset_name: str  # ⬅️ 추가
    rise_probability_percent: float
    fall_probability_percent: float
    neutral_probability_percent: float
    expected_value_percent: float

class AdviceEntry(BaseModel):
    asset_name: str
    weight: float
    reason: str
'''
class ForecastResult(BaseModel):
    asset_name: str
    bullish: float
    neutral: float
    bearish: float
    expected_value: float

class AdviceEntry(BaseModel):
    asset_name: str
    allocation_ratio: float
    rationale: str
