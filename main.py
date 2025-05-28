import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime

from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository
from adapters.ai_forecast_repository import AIForecastRepository
from dependencies import ai_recommender
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("config", ".env"))
app = FastAPI(title="Asset Market API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# APScheduler 설정
scheduler = BackgroundScheduler()

def scheduled_fetch():
    print(f"[{datetime.now()}] 🔄 [스케줄러] 데이터 갱신 시작")
    
    # 1. 자산 데이터 업데이트
    try:
        manager = AssetManager(AssetRepository())
        manager.update_all_assets()
        print(f"[{datetime.now()}] ✅ 자산 데이터 업데이트 완료")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 자산 데이터 업데이트 실패: {e}")

    '''
    # 2. AI 예측 정보 업데이트
    try:
        ai_recommender.fetch_probability_forecast()
        print(f"[{datetime.now()}] ✅ probabilityForecast 갱신 완료")

        ai_recommender.fetch_contextual_advice()
        print(f"[{datetime.now()}] ✅ contextualAdvice 갱신 완료")
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ AI 예측 정보 갱신 실패: {e}")

    print(f"[{datetime.now()}] 🔁 [스케줄러] 전체 갱신 프로세스 종료")

    '''
    # 3. AI 예측 정보 업데이트 (BETA)
    try:
        ai_recommender.generate_and_save_forecasts_and_advice()
    except Exception as e:
        print(f"[{datetime.now()}] ❌ AI 예측 정보 (BETA) 갱신 실패: {e}")


# 매일 10:00 (한국시간) 작업 등록
scheduler.add_job(
    scheduled_fetch,
    trigger="cron",
    hour=10,
    minute=00,
    timezone=timezone("Asia/Seoul")
)

#scheduled_fetch()

scheduler.start()
