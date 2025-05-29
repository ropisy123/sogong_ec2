import os
import sys
import json
import pytest
import tempfile
import shutil
import pandas as pd

from datetime import datetime
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.asset_repository import AssetRepository
from managers.asset_manager import AssetManager
from managers.cycle_manager import CycleManager
from managers.correlation_manager import CorrelationManager
from managers.ai_recommender import AIRecommender
from core import config
from core.schemas import ForecastResult, AdviceEntry


@pytest.fixture(scope="module")
def test_environment():
    load_dotenv()
    temp_dir = tempfile.mkdtemp()
    date_folder = datetime.today().strftime("%Y%m%d")
    full_data_path = os.path.join(temp_dir, date_folder)
    os.makedirs(full_data_path, exist_ok=True)

    original_data_dir = config.DATA_DIR
    config.DATA_DIR = temp_dir

    repo = AssetRepository(target_dir=full_data_path)
    manager = AssetManager(repo)

    mock_dates = pd.date_range("2024-01-01", periods=90)
    df1 = pd.DataFrame({"date": mock_dates, "sp500": range(90)})
    df2 = pd.DataFrame({"date": mock_dates, "bitcoin": range(90, 0, -1)})
    df1.to_csv(os.path.join(full_data_path, "sp500.csv"), index=False)
    df2.to_csv(os.path.join(full_data_path, "bitcoin.csv"), index=False)

    yield {
        "temp_dir": temp_dir,
        "full_data_path": full_data_path,
        "manager": manager,
        "mock_dates": mock_dates
    }

    config.DATA_DIR = original_data_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def recommender(save_dir):  # save_dir을 인자로 받음
    mock_llm = MagicMock()

    def call_beta_side_effect(prompt, *args, **kwargs):
        if "기대수익률" in prompt:
            return json.dumps({
                "상승확률": 0.6,
                "보합확률": 0.2,
                "하락확률": 0.2,
                "기대수익률": 5.0
            })
        else:
            return json.dumps({
                "비트코인": {
                    "자산명": "비트코인",
                    "권장비중": 20.0,
                    "선정이유": "성장성"
                }
            })

    mock_llm.call_beta.side_effect = call_beta_side_effect

    mock_repo = MagicMock()

    def save_forecast_side_effect(forecasts: dict):
        date_folder = datetime.today().strftime("%Y%m%d")
        full_path = os.path.join(save_dir, date_folder)
        os.makedirs(full_path, exist_ok=True)
        path = os.path.join(full_path, "forecast.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({k: v.dict() for k, v in forecasts.items()}, f, ensure_ascii=False, indent=2)

    def save_advice_side_effect(advice: dict, duration: str, tolerance: str):
        date_folder = datetime.today().strftime("%Y%m%d")
        full_path = os.path.join(save_dir, date_folder)
        os.makedirs(full_path, exist_ok=True)
        filename = f"advice_{duration}_{tolerance}.csv"
        path = os.path.join(full_path, filename)
        df = pd.DataFrame([
            {"asset": k, "allocation_ratio": v.allocation_ratio, "rationale": v.rationale}
            for k, v in advice.items()
        ])
        df.to_csv(path, index=False)

    def load_forecast_side_effect(asset):
        date_folder = datetime.today().strftime("%Y%m%d")
        path = os.path.join(save_dir, date_folder, "forecast.json")
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        entry = raw[asset]
        return ForecastResult(**entry)

    def load_advice_side_effect(duration, tolerance):
        date_folder = datetime.today().strftime("%Y%m%d")
        path = os.path.join(save_dir, date_folder, f"advice_{duration}_{tolerance}.csv")
        df = pd.read_csv(path)
        return [
            AdviceEntry(asset_name=row["asset"], allocation_ratio=row["allocation_ratio"], rationale=row["rationale"])
            for _, row in df.iterrows()
        ]

    mock_repo.save_forecast.side_effect = save_forecast_side_effect
    mock_repo.save_advice.side_effect = save_advice_side_effect
    mock_repo.load_forecast.side_effect = load_forecast_side_effect
    mock_repo.load_advice.side_effect = load_advice_side_effect

    recommender = AIRecommender(llm_adapter=mock_llm)
    recommender.repository = mock_repo
    recommender.base_data_dir = save_dir  # 주입

    return recommender

@pytest.fixture
def save_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@patch("adapters.asset_repository.AssetRepository.fetch_from_yahoo")
@patch("adapters.asset_repository.AssetRepository.fetch_from_fred")
def test_IT01_update_all_assets_creates_files(mock_fred, mock_yahoo, test_environment):
    full_data_path = test_environment["full_data_path"]
    manager = test_environment["manager"]
    mock_dates = test_environment["mock_dates"]

    def fake_fetch(asset, *_):
        df = pd.DataFrame({
            "date": mock_dates,
            asset: range(len(mock_dates))
        })
        df.to_csv(os.path.join(full_data_path, f"{asset}.csv"), index=False)

    mock_yahoo.side_effect = fake_fetch
    mock_fred.side_effect = fake_fetch

    manager.update_all_assets()

    for asset in manager.get_supported_assets():
        path = os.path.join(full_data_path, f"{asset}.csv")
        assert os.path.exists(path), f"{asset}.csv not created"


def test_IT02_cycle_manager_merges_and_resamples(test_environment):
    cycle = CycleManager()
    result = cycle.get_assets(["sp500", "bitcoin"], resolution="weekly")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "sp500" in result[0]
    assert "bitcoin" in result[0]


def test_IT03_correlation_manager_sliding_result(test_environment):
    corr = CorrelationManager()
    result = corr.get_correlation_sliding_series("sp500", "bitcoin", "1개월")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "date" in result[0]
    assert "correlation" in result[0]
    assert isinstance(result[0]["correlation"], float)


def test_IT04_asset_manager_get_asset_data(test_environment):
    manager = test_environment["manager"]
    result = manager.get_asset_data(["sp500", "bitcoin"], "monthly")
    assert isinstance(result, list)
    assert "sp500" in result[0]
    assert "bitcoin" in result[0]


def test_IT05_asset_manager_correlation_series(test_environment):
    manager = test_environment["manager"]
    result = manager.get_correlation_sliding_series("sp500", "bitcoin", "3개월")
    assert isinstance(result, list)
    assert "correlation" in result[0]
    assert isinstance(result[0]["correlation"], float)


def test_IT06_generate_forecast_creates_file_and_result(recommender, save_dir):
    asset = "비트코인"
    result = recommender.generate_forecast(asset, save_dir)
    assert isinstance(result, ForecastResult)
    file_path = os.path.join(save_dir, f"{asset}_raw_ai_forecast.json")
    assert os.path.exists(file_path)


def test_IT07_generate_and_save_forecasts_and_advice_end_to_end(recommender, save_dir):
    recommender.base_data_dir = save_dir
    recommender.generate_and_save_forecasts_and_advice()

    date_folder = datetime.today().strftime("%Y%m%d")
    forecast_file = os.path.join(save_dir, date_folder, "forecast.json")
    advice_file = os.path.join(save_dir, date_folder, "advice_3년_10%.csv")

    assert os.path.exists(forecast_file)
    assert os.path.exists(advice_file)


def test_IT08_generate_portfolio_advice_creates_entries(recommender):
    dummy_forecast = ForecastResult(
        asset_name="비트코인", bullish=60.0, neutral=25.0, bearish=15.0, expected_value=12.5
    )
    forecasts = {"비트코인": dummy_forecast}
    advice = recommender.generate_portfolio_advice(forecasts, "3년", "10%")
    assert isinstance(advice, dict)
    assert "비트코인".lower() in advice
    assert isinstance(advice["비트코인".lower()], AdviceEntry)


def test_IT09_parse_forecast_and_advice_with_json_block(recommender):
    forecast_json = '''```json
    {
        "상승확률": 50,
        "보합확률": 30,
        "하락확률": 20,
        "기대수익률": 5
    }
    ```'''
    parsed = recommender._parse_forecast("비트코인", forecast_json, True)
    assert isinstance(parsed, ForecastResult)
    assert parsed.expected_value == 5

    advice_json = '''```json
    {
        "비트코인": {
            "권장비중": 20,
            "선정이유": "성장성"
        }
    }
    ```'''
    parsed_advice = recommender._parse_advice(advice_json)
    assert isinstance(parsed_advice, dict)
    assert "비트코인".lower() in parsed_advice
    assert isinstance(parsed_advice["비트코인".lower()], AdviceEntry)


def test_IT10_prompt_contains_economic_and_stat_summary(recommender):
    prompt = recommender.prompt_builder.build_contextual_advice_prompt("3년", "10%")
    assert "요약" in prompt or "통계" in prompt
    assert "경제" in prompt or "금리" in prompt

def test_IT11_load_forecast_from_file(recommender):
    # 먼저 저장 수행
    recommender.generate_and_save_forecasts_and_advice()

    result = recommender.get_loaded_forecast("비트코인")
    assert isinstance(result, ForecastResult)


def test_IT12_load_advice_from_file(recommender):
    # 먼저 저장 수행
    recommender.generate_and_save_forecasts_and_advice()

    result = recommender.get_loaded_advices("3년", "10%")
    assert isinstance(result, list)
    assert all(isinstance(entry, AdviceEntry) for entry in result)
