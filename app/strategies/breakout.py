from __future__ import annotations

import pandas as pd

from .base import Candidate
from .indicators import enrich_indicators


def select_breakout(code: str, name: str, df: pd.DataFrame, market_regime: dict) -> Candidate | None:
    data = enrich_indicators(df).dropna().copy()
    if len(data) < 80:
        return None
    last = data.iloc[-1]
    previous = data.iloc[:-1]
    if previous.empty:
        return None

    close = float(last["close"])
    high60_before = float(previous["high"].tail(60).max())
    volume = float(last.get("volume", 0))
    volume_ma20 = float(last.get("volume_ma20", 0))
    day_range = float(last["high"] - last["low"])
    close_position = (close - float(last["low"])) / day_range if day_range > 0 else 0

    if close <= high60_before:
        return None
    if volume_ma20 <= 0 or volume < volume_ma20 * 1.5:
        return None
    if close_position < 0.65:
        return None

    score = 65
    score += min((volume / volume_ma20 - 1.5) * 10, 15)
    score += 10 if close_position > 0.8 else 0
    score += 10 if market_regime.get("regime") == "strong" else 0
    score -= 15 if market_regime.get("regime") == "weak" else 0

    stop_price = high60_before * 0.97
    target1 = close * 1.10
    target2 = close * 1.18

    return Candidate(
        code=code,
        name=name,
        strategy="放量突破策略",
        score=round(score, 2),
        buy_timing=f"突破位约 {high60_before:.2f}；次日不跌回突破位，或盘中回踩突破位企稳时考虑。",
        stop_loss=f"跌回突破位下方，参考止损 {stop_price:.2f}。",
        take_profit=f"第一目标 {target1:.2f}，强势延伸目标 {target2:.2f}；放量长上影需减仓。",
        holding_period="3-10个交易日，偏短线。",
        position=f"参考单票仓位 {int(market_regime.get('single_position', 0.15) * 100)}%，弱市减半。",
        reasons=[
            "收盘价突破近60日高点，出现平台突破信号。",
            f"成交量约为20日均量的 {volume / volume_ma20:.2f} 倍，量能确认较强。",
            "收盘位置靠近当日高位，说明突破质量较好。",
        ],
        risk_notes=[
            "假突破风险较高，跌回突破位应果断处理。",
            "若次日低开低走，不建议追入。",
        ],
        metrics={"close": close, "breakout_level": high60_before, "volume_ratio": volume / volume_ma20},
    )
