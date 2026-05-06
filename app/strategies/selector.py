from __future__ import annotations

import pandas as pd

from .base import Candidate
from .breakout import select_breakout
from .oversold_rebound import select_oversold_rebound
from .quality_trend import select_quality_trend
from .trend_leader import select_trend_leader


def run_all_strategies(
    code: str,
    name: str,
    history: pd.DataFrame,
    market_regime: dict,
    meta: dict | None = None,
) -> list[Candidate]:
    selectors = [
        lambda: select_trend_leader(code, name, history, market_regime),
        lambda: select_breakout(code, name, history, market_regime),
        lambda: select_quality_trend(code, name, history, market_regime, meta),
        lambda: select_oversold_rebound(code, name, history, market_regime),
    ]
    candidates: list[Candidate] = []
    for selector in selectors:
        try:
            candidate = selector()
        except Exception as exc:
            continue
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    by_code: dict[str, Candidate] = {}
    for item in sorted(candidates, key=lambda x: x.score, reverse=True):
        if item.code not in by_code:
            by_code[item.code] = item
        else:
            current = by_code[item.code]
            current.score = round(current.score + min(item.score * 0.08, 8), 2)
            current.reasons.append(f"同时触发：{item.strategy}")
    return sorted(by_code.values(), key=lambda x: x.score, reverse=True)
