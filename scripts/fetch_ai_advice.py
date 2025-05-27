import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.asset_repository import AssetRepository
from adapters.ai_forecast_repository import AIForecastRepository
from managers.asset_manager import AssetManager
from managers.ai_recommender import AIRecommender
from core.config import AI_FORCAST_DIR

def main():

    # 1. 자산 데이터 업데이트
    try:
        manager = AssetManager(AssetRepository())
        manager.update_all_assets()
        print(f"[{datetime.now()}] ✅ 자산 데이터 업데이트 완료")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 자산 데이터 업데이트 실패: {e}")


    try:
        recommender = AIRecommender()
        repository = AIForecastRepository()
        recommender.generate_and_save_forecasts_and_advice(repository)
    except Exception as e:
        print(f"[{datetime.now()}] ❌ AI 예측 정보 (BETA) 갱신 실패: {e}")


if __name__ == "__main__":
    main()
