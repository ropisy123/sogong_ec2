from typing import Dict, List
from core.schemas import EconomicIndicator
from adapters.economic_repository import EconomicRepository

class EconomicIndicatorManager:
    def __init__(self, repository: EconomicRepository):
        self.repository = repository
        self.indicators: Dict[str, List[EconomicIndicator]] = {}

    def fetch_all(self):
        all_data = self.repository.fetch_all()
        self.indicators.clear()

        for name, time_series in all_data.items():  # name: 'cpi', time_series: Dict[date_str, float]
            self.indicators[name] = []
            for date_str, value in time_series.items():
                self.indicators[name].append(
                    EconomicIndicator(name=name, date=date_str, value=value)
                )

    def get_indicator(self, name: str) -> List[EconomicIndicator]:
        if name not in self.indicators:
            self.indicators[name] = self.repository.get_by_name(name)
        return self.indicators[name]


    def get_all_indicators(self) -> List[EconomicIndicator]:
        all_list = []
        for series in self.indicators.values():
            all_list.extend(series)
        return all_list
