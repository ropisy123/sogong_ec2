import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from managers.ai_recommender import AIRecommender

def main():
    print(f"[{datetime.now()}] 🔄 데이터 업데이트 시작")
    print(settings.model_dump())

    # 2. AI 예측 정보 업데이트
    recommender = AIRecommender()
    try:
        recommender.fetch_probability_forecast()
        print(f"[{datetime.now()}] ✅ probabilityForecast 갱신 완료")
    except Exception as e:
        print(f"[ERROR] probabilityForecast 갱신 실패: {e}")

if __name__ == "__main__":
    main()
