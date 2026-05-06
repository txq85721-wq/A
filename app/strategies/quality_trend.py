from __future__ import annotations

import pandas as pd

from app.utils import safe_float

from .base import Candidate
from .indicators import enrich_indicators


def select_quality_trend(code: str, name: str, df: pd.DataFrame, market_regime: dict, meta: dict | None = None) -> Candidate | None:
    data = enrich_indicators(df).dropna().copy()
    if len(data) < 100:
        return None
    last = data.iloc[-1]

    close = float(last["close"])
    ma20 = float(last["ma20"])
    ma60 = float(last["ma60"])
    vol20 = float(last.get("volatility20", 0))
    drawdown60 = float(last.get("drawdown60", 0))
    return60 = float(last.get("return60", 0))
    pe = safe_float(meta.get("pe_ttm"), None) if meta else None
    pb = safe_float(meta.get("pb"), None) if meta else None

    if not (close > ma60 and ma20 >= ma60 * 0.98):
        return None
    if vol20 > 0.55:
        return None
    if drawdown60 < -0.18:
        return None
    if return60 < 0:
        return None

    score = 55
    score += max(0, min((0.55 - vol20) * 40, 15))
    score += max(0, min(return60 * 100, 20))
    score += 8 if drawdown60 > -0.08 else 0
    if pe is not None and 0 < pe < 50:
        score += 5
    if pb is not None and 0 < pb < 8:
        score += 5
    if market_regime.get("regime") == "weak":
        score += 5  # 弱市更偏好低波动品种

    stop_price = ma60 * 0.97
    target1 = close * 1.12
    target2 = close * 1.22

    return Candidate(
        code=code,
        name=name,
        strategy="低波动质量趋势策略",
        score=round(score, 2),
        buy_timing="回踩20日线或60日线企稳时分批买入，不追短线急拉。",
        stop_loss=f"跌破60日线并无法收回，参考止损 {stop_price:.2f}。",
        take_profit=f"第一目标 {target1:.2f}，第二目标 {target2:.2f}；趋势稳定可继续持有。",
        holding_period="20-60个交易日，偏中线。",
        position=f"参考单票仓位 {int(market_regime.get('single_position', 0.15) * 100)}%，适合作为组合底仓。",
        reasons=[
            "股价站上60日线，趋势结构稳定。",
            f"20日年化波动率约 {vol20*100:.1f}%，相对适合稳健持仓。",
            f"60日最大回撤约 {drawdown60*100:.1f}%，回撤压力可控。",
        ],
        risk_notes=[
            "低波动策略收益弹性通常低于热点题材。",
            "若基本面或行业景气度恶化，需要降低评分。",
        ],
        metrics={"close": close, "ma20": ma20, "ma60": ma60, "volatility20": vol20, "drawdown60": drawdown60, "pe_ttm": pe, "pb": pb},
    )
