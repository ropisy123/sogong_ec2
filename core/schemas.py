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

@dataclass
class EconomicIndicator:
    name: str                    # 예: "interest_rate"
    date: str                    # 예: "2023-04-01"
    value: Union[float, List[float]]  # 단일값 또는 수치 배열

@dataclass
class ForecastResult:
    bullish: float      # 상승
    neutral: float      # 보합
    bearish: float      # 하락
    expected_value: float  # 가중기대치

@dataclass
class AdviceEntry:
    asset_name: str
    allocation_ratio: float
    rationale: str

@dataclass
class ForecastResult(BaseModel):
    rise: float
    hold: float
    fall: float
    expected_value: float = 0.0  # 확률 가중 기대치

@dataclass
class AdviceEntry(BaseModel):
    asset_name: str
    weight: float
    reason: str
