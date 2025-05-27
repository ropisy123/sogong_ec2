import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.ai_recommender import AIRecommender
from adapters.ai_forecast_repository import AIForecastRepository
from core.config import AI_FORCAST_DIR

def main():
    # 오늘 날짜 폴더 생성
    date_folder = datetime.today().strftime("%Y%m%d")
    save_dir = os.path.join(AI_FORCAST_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)

    # 객체 초기화
    recommender = AIRecommender()
    repository = AIForecastRepository()

    # 자산 목록 및 결과 저장 구조 초기화
    assets =  ["s&p500", "kospi", "bitcoin", "gold", "kr_real_estate", "us_interest", "kr_interest"]
    all_forecasts = {}

    # 예측 생성 및 저장
    for asset in assets:
        result = recommender.generate_forecast(asset, save_dir)
        all_forecasts[asset] = result
    repository.save_forecast(date_folder, all_forecasts)


    # 포트폴리오 조언 생성 및 저장
    for duration in ["1년", "3년", "5년", "10년"]:
        for tolerance in ["5%", "10%", "20%"]:
            advice = recommender.generate_portfolio_advice(all_forecasts, duration, tolerance)
            repository.save_advice(date_folder, advice, duration, tolerance)


if __name__ == "__main__":
    main()
