import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository
from managers.ai_recommender import AIRecommender
from core.config import settings

def main():
    print(f"[{datetime.now()}] 🔄 데이터 업데이트 시작")

    # 1. 자산 데이터 업데이트
    try:
        manager = AssetManager(AssetRepository())
        manager.update_all_assets()
        print(f"[{datetime.now()}] ✅ 자산 데이터 업데이트 완료")
    except Exception as e:
        print(f"[ERROR] 자산 데이터 업데이트 실패: {e}")

    # 2. AI 예측 정보 업데이트
    recommender = AIRecommender()
    
    try:
        recommender.fetch_probability_forecast()
        print(f"[{datetime.now()}] ✅ probabilityForecast 갱신 완료")
    except Exception as e:
        print(f"[ERROR] probabilityForecast 갱신 실패: {e}")

    try:
        recommender.fetch_contextual_advice()
        print(f"[{datetime.now()}] ✅ contextualAdvice 갱신 완료")
    except Exception as e:
        print(f"[ERROR] contextualAdvice 갱신 실패: {e}")

    print(f"[{datetime.now()}] 🔁 전체 갱신 프로세스 종료")

if __name__ == "__main__":
    main()
