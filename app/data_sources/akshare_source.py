from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class StockMeta:
    code: str
    name: str
    market: str = "A"


class AkShareSource:
    """AkShare based A-share data source.

    The methods import akshare lazily so the project can still be inspected without
    network access or without the dependency installed.
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def stock_list(self) -> pd.DataFrame:
        import akshare as ak

        df = ak.stock_zh_a_spot_em()
        rename_map = {
            "代码": "code",
            "名称": "name",
            "最新价": "price",
            "涨跌幅": "pct_chg",
            "成交量": "volume",
            "成交额": "amount",
            "市盈率-动态": "pe_ttm",
            "市净率": "pb",
        }
        df = df.rename(columns=rename_map)
        df["code"] = df["code"].astype(str).str.zfill(6)
        return df

    def daily_history(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        import akshare as ak

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return df
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover",
        })
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "close", "high", "low", "volume", "amount", "pct_chg", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)

    def index_history(self, symbol: str = "000001", start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        import akshare as ak

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        df = ak.stock_zh_index_daily_em(symbol=symbol)
        if df.empty:
            return df
        df = df.rename(columns={"date": "date", "open": "open", "close": "close", "high": "high", "low": "low", "volume": "volume", "amount": "amount"})
        df["date"] = pd.to_datetime(df["date"])
        return df[df["date"] >= pd.to_datetime(start_date)].sort_values("date").reset_index(drop=True)

    def news(self, limit: int = 30) -> list[dict]:
        import akshare as ak

        items: list[dict] = []
        try:
            df = ak.stock_info_global_cls()
        except Exception:
            return items
        for _, row in df.head(limit).iterrows():
            items.append({
                "title": str(row.get("标题", row.get("title", ""))),
                "time": str(row.get("发布日期", row.get("时间", ""))),
                "source": str(row.get("来源", "财联社")),
                "url": str(row.get("链接", "")),
            })
        return items
