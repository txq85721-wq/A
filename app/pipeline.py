from __future__ import annotations

from datetime import datetime

from .ai_analyzer import analyze_with_ai
from .config import settings
from .data_sources.akshare_source import AkShareSource
from .database import save_run
from .report import generate_report
from .strategies.market_regime import get_market_regime
from .strategies.selector import deduplicate_candidates, run_all_strategies


def should_skip_stock(code: str, name: str) -> bool:
    if name.startswith("退") or "ST" in name or "*ST" in name:
        return True
    if code.startswith(("8", "4")):
        return True
    return False


def run_daily_pipeline() -> dict:
    source = AkShareSource(settings.data_dir / "cache")
    stock_list = source.stock_list()
    index_df = source.index_history("000001")
    market_regime = get_market_regime(index_df)
    news = source.news(limit=30)

    candidates = []
    scanned = 0
    for _, row in stock_list.iterrows():
        if scanned >= settings.max_stocks_to_scan:
            break
        code = str(row.get("code", "")).zfill(6)
        name = str(row.get("name", ""))
        if should_skip_stock(code, name):
            continue
        scanned += 1
        try:
            history = source.daily_history(code)
            if history.empty:
                continue
            meta = row.to_dict()
            candidates.extend(run_all_strategies(code, name, history, market_regime, meta))
        except Exception:
            continue

    deduped = deduplicate_candidates(candidates)
    candidate_dicts = [item.to_dict() for item in deduped[:30]]
    recommendations = analyze_with_ai(candidate_dicts, news, market_regime, top_n=3)
    report_path = generate_report(market_regime, recommendations, news)
    run_id = save_run(market_regime, report_path, recommendations)

    return {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scanned": scanned,
        "candidates": len(deduped),
        "recommendations": recommendations,
        "market_regime": market_regime,
        "report_path": str(report_path),
    }
