from __future__ import annotations

import pandas as pd

from .base import Candidate
from .indicators import enrich_indicators


def select_trend_leader(code: str, name: str, df: pd.DataFrame, market_regime: dict) -> Candidate | None:
    data = enrich_indicators(df).dropna().copy()
    if len(data) < 80:
        return None
    last = data.iloc[-1]
    prev20 = data.tail(20)

    close = float(last["close"])
    ma20 = float(last["ma20"])
    ma60 = float(last["ma60"])
    amount = float(last.get("amount", 0))
    amount_ma20 = float(last.get("amount_ma20", 0))
    return20 = float(last.get("return20", 0))
    turnover = float(last.get("turnover", 0)) if pd.notna(last.get("turnover", 0)) else 0.0

    if not (close > ma20 > ma60):
        return None
    if return20 < 0.08:
        return None
    if amount_ma20 > 0 and amount < amount_ma20 * 0.8:
        return None

    score = 60
    score += min(return20 * 100, 25)
    score += 10 if amount > amount_ma20 else 0
    score += 5 if turnover >= 3 else 0
    if market_regime.get("regime") == "strong":
        score += 10
    elif market_regime.get("regime") == "weak":
        score -= 15

    recent_low = float(prev20["low"].min())
    stop_price = max(ma20 * 0.97, close * 0.92)
    target1 = close * 1.15
    target2 = close * 1.25

    return Candidate(
        code=code,
        name=name,
        strategy="趋势龙头策略",
        score=round(score, 2),
        buy_timing="回踩20日线不破，或放量突破近10日平台时分批买入；避免连续大涨后追高。",
        stop_loss=f"跌破20日线附近 {stop_price:.2f} 或跌破近20日低点 {recent_low:.2f} 减仓/止损。",
        take_profit=f"第一目标 {target1:.2f}，第二目标 {target2:.2f}；跌破10日线可移动止盈。",
        holding_period="5-20个交易日，趋势未破可延长。",
        position=f"参考单票仓位 {int(market_regime.get('single_position', 0.15) * 100)}% 左右。",
        reasons=[
            "股价位于20日和60日均线上方，趋势结构较强。",
            f"近20日涨幅约 {return20*100:.1f}%，具备相对强势特征。",
            "成交额未明显萎缩，资金活跃度尚可。",
        ],
        risk_notes=[
            "趋势股最大风险是高位放量冲高回落。",
            "若大盘转弱，应降低仓位或放弃追涨。",
        ],
        metrics={"close": close, "ma20": ma20, "ma60": ma60, "return20": return20, "amount": amount},
    )
