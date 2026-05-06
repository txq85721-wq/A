from __future__ import annotations

import pandas as pd

from .indicators import enrich_indicators


def get_market_regime(index_df: pd.DataFrame) -> dict:
    data = enrich_indicators(index_df).dropna().copy()
    if data.empty:
        return {"regime": "unknown", "max_position": 0.3, "reason": "指数数据不足"}
    last = data.iloc[-1]
    close = float(last["close"])
    ma20 = float(last["ma20"])
    ma60 = float(last["ma60"])
    amount = float(last.get("amount", 0))
    amount_ma20 = float(last.get("amount_ma20", 0))

    if close > ma20 > ma60 and amount >= amount_ma20:
        return {"regime": "strong", "max_position": 0.8, "single_position": 0.25, "reason": "指数位于20日和60日均线上方且成交额不弱"}
    if close > ma60:
        return {"regime": "neutral", "max_position": 0.5, "single_position": 0.15, "reason": "指数仍在60日线上方，但趋势或量能不够强"}
    return {"regime": "weak", "max_position": 0.25, "single_position": 0.1, "reason": "指数低于60日均线，控制仓位优先"}
