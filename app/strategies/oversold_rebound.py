from __future__ import annotations

import pandas as pd

from .base import Candidate
from .indicators import enrich_indicators


def select_oversold_rebound(code: str, name: str, df: pd.DataFrame, market_regime: dict) -> Candidate | None:
    data = enrich_indicators(df).dropna().copy()
    if len(data) < 80:
        return None
    last = data.iloc[-1]
    prev = data.iloc[-2]

    close = float(last["close"])
    ma20 = float(last["ma20"])
    rsi_now = float(last["rsi14"])
    rsi_prev = float(prev["rsi14"])
    volume = float(last.get("volume", 0))
    volume_ma20 = float(last.get("volume_ma20", 0))
    recent_low = float(data.tail(20)["low"].min())
    deviation = close / ma20 - 1

    if market_regime.get("regime") == "weak":
        return None
    if not (rsi_prev < 35 <= rsi_now):
        return None
    if deviation > -0.02:
        return None
    if volume_ma20 > 0 and volume < volume_ma20 * 0.8:
        return None

    score = 55
    score += min(abs(deviation) * 100, 15)
    score += 10 if volume > volume_ma20 else 0
    score += 10 if close > float(last["open"]) else 0
    if market_regime.get("regime") == "strong":
        score += 5

    stop_price = recent_low * 0.98
    target1 = ma20
    target2 = close * 1.12

    return Candidate(
        code=code,
        name=name,
        strategy="超跌反弹策略",
        score=round(score, 2),
        buy_timing="RSI从低位重新上穿后，观察次日是否继续站稳；适合轻仓试错。",
        stop_loss=f"跌破近20日低点，参考止损 {stop_price:.2f}。",
        take_profit=f"第一目标回到20日线 {target1:.2f}，强反弹目标 {target2:.2f}。",
        holding_period="2-8个交易日，短线为主。",
        position="轻仓参与，单票建议不超过10%-15%。",
        reasons=[
            "RSI低位修复，出现超跌反弹信号。",
            f"当前相对20日线偏离约 {deviation*100:.1f}%，存在均值回归空间。",
            "成交量没有明显萎缩，短线修复概率提高。",
        ],
        risk_notes=[
            "超跌反弹不是趋势反转，失败要快速止损。",
            "弱势市场中超跌可能继续超跌，因此已过滤弱市环境。",
        ],
        metrics={"close": close, "ma20": ma20, "rsi14": rsi_now, "deviation": deviation},
    )
