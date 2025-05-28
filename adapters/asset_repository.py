import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from fredapi import Fred
from core.config import BASE_DATA_DIR


class AssetRepository:
    def __init__(self, target_dir: str = None):
        self.START = "2005-01-01"
        self.END = datetime.today().strftime('%Y-%m-%d')
        self.full_dates = pd.date_range(start=self.START, end=self.END, freq="D")
        self.base_df = pd.DataFrame({"date": self.full_dates})
        self.fred = Fred(api_key=os.getenv("FRED_API_KEY", "YOUR_API_KEY"))

        self.asset_symbol_map = {
            "sp500": "^GSPC",
            "kospi": "^KS11",
            "bitcoin": "BTC-USD",
            "gold": "GC=F",
            "real_estate": "VNQ",
            "us_interest": "FEDFUNDS",
            "kr_interest": "INTGSBKRM193N",
        }
        self.fred_assets = {"us_interest", "kr_interest"}

        # ➕ 자동으로 오늘 날짜 기반 폴더 생성
        if not target_dir:
            today_str = datetime.today().strftime('%Y%m%d')
            target_dir = os.path.join(BASE_DATA_DIR, today_str)
        self.output_dir = target_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _save_asset_df(self, df: pd.DataFrame, asset: str):
        df = df.copy()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col if isinstance(col, str) else col[0] for col in df.columns]

        df = df.reset_index(drop=True)
        if "date" not in df.columns:
            if "Date" in df.columns:
                df.rename(columns={"Date": "date"}, inplace=True)
            else:
                print(f"[WARNING] No 'date' column found for asset {asset}")
                return

        df["date"] = pd.to_datetime(df["date"])
        if asset not in df.columns:
            print(f"[WARNING] No valid data for {asset} from Yahoo.")
            return

        df = df[["date", asset]]
        df = pd.merge(self.base_df, df, on="date", how="left")
        df[asset] = df[asset].ffill().fillna(0)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        save_path = os.path.join(self.output_dir, f"{asset}.csv")
        df.to_csv(save_path, index=False)
        print(f"[OK] Saved {save_path}")

    def fetch_from_yahoo(self, asset: str, ticker: str):
        print(f"[YF] Fetching {asset} from {ticker}")
        try:
            df = yf.download(ticker, start=self.START, end=self.END)
            if df.empty or "Close" not in df.columns:
                print(f"[WARNING] No valid data for {asset} from Yahoo.")
                return
            df = df[["Close"]].copy()
            df.rename(columns={"Close": asset}, inplace=True)
            df["date"] = df.index
            self._save_asset_df(df, asset)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {asset} from Yahoo: {e}")

    def fetch_from_fred(self, asset: str, series_id: str):
        print(f"[FRED] Fetching {asset} from {series_id}")
        try:
            series = self.fred.get_series(series_id)
            df = series.reset_index()
            df.columns = ["date", asset]
            self._save_asset_df(df, asset)
        except Exception as e:
            print(f"[ERROR] {asset} fetch failed: {e}")

    def fetch_all(self):
        for asset, symbol in self.asset_symbol_map.items():
            if asset in self.fred_assets:
                self.fetch_from_fred(asset, symbol)
            else:
                self.fetch_from_yahoo(asset, symbol)

    def fetch_and_save(self, asset: str):
        symbol = self.asset_symbol_map.get(asset)
        if not symbol:
            raise ValueError(f"Unknown asset: {asset}")

        if asset in self.fred_assets:
            self.fetch_from_fred(asset, symbol)
        else:
            self.fetch_from_yahoo(asset, symbol)

    def get_all_assets(self):
        return list(self.asset_symbol_map.keys())
