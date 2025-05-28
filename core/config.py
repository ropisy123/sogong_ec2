import os

from pathlib import Path
from pydantic_settings import BaseSettings

# 프로젝트 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BASE_DATA_DIR = DATA_DIR
AI_FORCAST_DIR = os.path.join(DATA_DIR, "ai_forcast")

# 환경 설정 클래스 정의
class AppSettings(BaseSettings):
    fred_api_key: str
    llm_api_key: str
    llm_model_name: str
    llm_base_url: str

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent / "config" / ".env")
        case_sensitive = False

# 설정 인스턴스 초기화
settings = AppSettings()

# 필요한 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)
