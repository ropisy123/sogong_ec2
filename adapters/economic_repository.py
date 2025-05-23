import random
from datetime import datetime
import pandas as pd
from typing import List
from schemas.economic_indicator import EconomicIndicator

class EconomicRepository:
    def __init__(self):
        self.today = datetime.today()

    def _generate_monthly_data(self, name: str, start_year: int, end_year: int, min_val: float, max_val: float) -> List[EconomicIndicator]:
        dates = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq='M')
        return [
            EconomicIndicator(
                name=name,
                date=date.strftime("%Y-%m-%d"),
                value=round(random.uniform(min_val, max_val), 2)
            )
            for date in dates
        ]

    def get_interest_rate(self) -> List[EconomicIndicator]:
        return self._generate_monthly_data("interest_rate", self.today.year - 5, self.today.year, 0.5, 4.0)

    def get_gdp_growth(self) -> List[EconomicIndicator]:
        return self._generate_monthly_data("gdp_growth", self.today.year - 5, self.today.year, -2.0, 6.0)

    def get_unemployment_rate(self) -> List[EconomicIndicator]:
        return self._generate_monthly_data("unemployment_rate", self.today.year - 5, self.today.year, 2.0, 6.0)

    def get_all(self) -> List[EconomicIndicator]:
        return (
            self.get_interest_rate() +
            self.get_gdp_growth() +
            self.get_unemployment_rate()
        )

    def get_by_name(self, name: str) -> List[EconomicIndicator]:
        if name == "interest_rate":
            return self.get_interest_rate()
        elif name == "gdp_growth":
            return self.get_gdp_growth()
        elif name == "unemployment_rate":
            return self.get_unemployment_rate()
        else:
            raise ValueError(f"Unknown economic indicator: {name}")
