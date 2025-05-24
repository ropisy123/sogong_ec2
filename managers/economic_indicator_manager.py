from typing import Dict, List
from core.schemas import EconomicIndicator
from adapters.economic_repository import EconomicRepository

class EconomicIndicatorManager:
    def __init__(self, repository: EconomicRepository):
        self.repository = repository
        self.indicators: Dict[str, List[EconomicIndicator]] = {}

    def fetch_all(self):
        all_data = self.repository.get_all()
        self.indicators.clear()
        for item in all_data:
            if item.name not in self.indicators:
                self.indicators[item.name] = []
            self.indicators[item.name].append(item)

    def get_indicator(self, name: str) -> List[EconomicIndicator]:
        if name not in self.indicators:
            self.indicators[name] = self.repository.get_by_name(name)
        return self.indicators[name]

    def get_all_indicators(self) -> Dict[str, List[EconomicIndicator]]:
        if not self.indicators:
            self.fetch_all()
        return self.indicators
