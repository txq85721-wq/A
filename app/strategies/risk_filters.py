from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from app.utils import safe_float


def is_suspended_or_invalid(meta: dict[str, Any]) -> bool:
    price = safe_float(meta.get("price"), None)
    pct_chg = safe_float(meta.get("pct_chg"), None)
    amount = safe_float(meta.get("amount"), 0) or 0
    if price is None or price <= 0:
        return True
    # Suspended stocks commonly have zero turnover/amount in spot tables.
    if amount <= 0 and pct_chg in {None, 0}:
        return True
    return False


def is_limit_up_or_down(meta: dict[str, Any], threshold: float = 9.8) -> bool:
    pct_chg = safe_float(meta.get("pct_chg"), None)
    if pct_chg is None:
        return False
    return abs(pct_chg) >= threshold


def is_low_liquidity(meta: dict[str, Any], min_amount: float) -> bool:
    amount = safe_float(meta.get("amount"), 0) or 0
    return amount < min_amount


def has_enough_history(history: pd.DataFrame, min_days: int) -> bool:
    return history is not None and not history.empty and len(history.dropna(subset=["close"])) >= min_days


def is_new_stock(history: pd.DataFrame, min_days: int) -> bool:
    return not has_enough_history(history, min_days)


def should_skip_by_meta(code: str, name: str, meta: dict[str, Any], min_amount: float) -> tuple[bool, str]:
    if not code or len(code) != 6:
        return True, "invalid_code"
    if name.startswith("退") or "ST" in name.upper() or "*ST" in name.upper():
        return True, "st_or_delisting"
    if code.startswith(("8", "4")):
        return True, "beijing_exchange_or_old_market"
    if is_suspended_or_invalid(meta):
        return True, "suspended_or_invalid"
    if is_low_liquidity(meta, min_amount):
        return True, "low_liquidity"
    if is_limit_up_or_down(meta):
        return True, "limit_up_or_down"
    return False, "ok"
