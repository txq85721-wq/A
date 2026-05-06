from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Candidate:
    code: str
    name: str
    strategy: str
    score: float
    buy_timing: str
    stop_loss: str
    take_profit: str
    holding_period: str
    position: str
    reasons: list[str]
    risk_notes: list[str]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
