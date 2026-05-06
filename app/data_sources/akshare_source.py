from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from app.config import settings
from app.utils import normalize_code, safe_float


@dataclass
class StockMeta:
    code: str
    name: str
    market: str = "A"


class AkShareSource:
    """AkShare based A-share data source with lightweight local caching."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.daily_dir = self.cache_dir / "daily"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir.mkdir(parents=True, exist_ok=True)

    def _cache_is_fresh(self, path: Path) -> bool:
        if not settings.cache_enabled or not path.exists():
            return False
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        return age <= timedelta(hours=settings.cache_max_age_hours)

    def _normalize_numeric_columns(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        result = df.copy()
        for col in columns:
            if col in result.columns:
                result[col] = result[col].map(lambda value: safe_float(value, None))
        return result

    def stock_list(self) -> pd.DataFrame:
        import akshare as ak

        df = ak.stock_zh_a_spot_em()
        rename_map = {
            "代码": "code",
            "名称": "name",
            "最新价": "price",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "最高": "high",
            "最低": "low",
            "今开": "open",
            "昨收": "pre_close",
            "量比": "volume_ratio",
            "换手率": "turnover",
            "市盈率-动态": "pe_ttm",
            "市净率": "pb",
            "总市值": "total_mv",
            "流通市值": "float_mv",
        }
        df = df.rename(columns=rename_map)
        df["code"] = df["code"].map(normalize_code)
        df["name"] = df["name"].astype(str)
        df = self._normalize_numeric_columns(
            df,
            [
                "price",
                "pct_chg",
                "change",
                "volume",
                "amount",
                "amplitude",
                "high",
                "low",
                "open",
                "pre_close",
                "volume_ratio",
                "turnover",
                "pe_ttm",
                "pb",
                "total_mv",
                "float_mv",
            ],
        )
        if "amount" in df.columns:
            df = df.sort_values("amount", ascending=False, na_position="last")
        return df.reset_index(drop=True)

    def daily_history(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        import akshare as ak

        code = normalize_code(code)
        if not code:
            return pd.DataFrame()
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=500)).strftime("%Y%m%d")

        cache_path = self.daily_dir / f"{code}.csv"
        if self._cache_is_fresh(cache_path):
            df = pd.read_csv(cache_path)
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").reset_index(drop=True)

        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return df
        df = df.rename(
            columns={
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
            }
        )
        df["date"] = pd.to_datetime(df["date"])
        df = self._normalize_numeric_columns(
            df,
            ["open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"],
        )
        df = df.sort_values("date").reset_index(drop=True)
        if settings.cache_enabled:
            df.to_csv(cache_path, index=False)
        return df

    def index_history(self, symbol: str = "000001", start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        import akshare as ak

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=500)).strftime("%Y%m%d")
        df = ak.stock_zh_index_daily_em(symbol=symbol)
        if df.empty:
            return df
        df = df.rename(columns={"date": "date", "open": "open", "close": "close", "high": "high", "low": "low", "volume": "volume", "amount": "amount"})
        df["date"] = pd.to_datetime(df["date"])
        df = self._normalize_numeric_columns(df, ["open", "close", "high", "low", "volume", "amount"])
        return df[df["date"] >= pd.to_datetime(start_date)].sort_values("date").reset_index(drop=True)

    def market_news(self, limit: int = 30) -> list[dict]:
        import akshare as ak

        items: list[dict] = []
        try:
            df = ak.stock_info_global_cls()
        except Exception:
            return items
        for _, row in df.head(limit).iterrows():
            items.append(
                {
                    "title": str(row.get("标题", row.get("title", ""))),
                    "time": str(row.get("发布日期", row.get("时间", ""))),
                    "source": str(row.get("来源", "财联社")),
                    "url": str(row.get("链接", "")),
                    "type": "market",
                }
            )
        return items

    def stock_news(self, code: str, limit: int = 5) -> list[dict]:
        import akshare as ak

        items: list[dict] = []
        code = normalize_code(code)
        try:
            df = ak.stock_news_em(symbol=code)
        except Exception:
            return items
        for _, row in df.head(limit).iterrows():
            items.append(
                {
                    "title": str(row.get("新闻标题", row.get("标题", row.get("title", "")))),
                    "time": str(row.get("发布时间", row.get("时间", ""))),
                    "source": str(row.get("文章来源", row.get("来源", "东方财富"))),
                    "url": str(row.get("新闻链接", row.get("链接", ""))),
                    "type": "stock",
                    "code": code,
                }
            )
        return items

    def news(self, limit: int = 30) -> list[dict]:
        return self.market_news(limit=limit)
