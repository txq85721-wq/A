import pandas as pd

from app.strategies.breakout import select_breakout
from app.strategies.market_regime import get_market_regime
from app.strategies.trend_leader import select_trend_leader


def make_history(rows=130):
    close = [10 + i * 0.08 for i in range(rows)]
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=rows),
            "open": [x * 0.99 for x in close],
            "close": close,
            "high": [x * 1.02 for x in close],
            "low": [x * 0.98 for x in close],
            "volume": [1000000] * rows,
            "amount": [100000000] * rows,
            "turnover": [3] * rows,
        }
    )
    return df


def test_market_regime_strong():
    df = make_history()
    regime = get_market_regime(df)
    assert regime["regime"] in {"strong", "neutral"}


def test_trend_leader_can_trigger():
    df = make_history()
    regime = {"regime": "strong", "single_position": 0.2}
    candidate = select_trend_leader("600000", "测试股票", df, regime)
    assert candidate is not None
    assert candidate.code == "600000"


def test_breakout_can_trigger():
    df = make_history()
    df.loc[df.index[-1], "close"] = df["high"].iloc[:-1].max() * 1.03
    df.loc[df.index[-1], "high"] = df.loc[df.index[-1], "close"] * 1.01
    df.loc[df.index[-1], "low"] = df.loc[df.index[-1], "close"] * 0.98
    df.loc[df.index[-1], "volume"] = 3000000
    regime = {"regime": "strong", "single_position": 0.2}
    candidate = select_breakout("600000", "测试股票", df, regime)
    assert candidate is not None
    assert candidate.strategy == "放量突破策略"
