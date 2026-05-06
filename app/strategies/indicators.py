from __future__ import annotations

import numpy as np
import pandas as pd


def ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def volatility(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window).std() * np.sqrt(252)


def max_drawdown(close: pd.Series, window: int = 60) -> pd.Series:
    rolling_max = close.rolling(window).max()
    return close / rolling_max - 1


def enrich_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ma5"] = ma(result["close"], 5)
    result["ma10"] = ma(result["close"], 10)
    result["ma20"] = ma(result["close"], 20)
    result["ma60"] = ma(result["close"], 60)
    result["ema20"] = ema(result["close"], 20)
    result["ema60"] = ema(result["close"], 60)
    result["rsi14"] = rsi(result["close"], 14)
    result["atr14"] = atr(result, 14)
    result["volatility20"] = volatility(result["close"], 20)
    result["drawdown60"] = max_drawdown(result["close"], 60)
    result["volume_ma20"] = result["volume"].rolling(20).mean()
    result["amount_ma20"] = result["amount"].rolling(20).mean()
    result["return20"] = result["close"].pct_change(20)
    result["return60"] = result["close"].pct_change(60)
    result["high60"] = result["high"].rolling(60).max()
    return result
