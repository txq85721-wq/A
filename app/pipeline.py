from __future__ import annotations

from collections import Counter
from datetime import datetime

from .ai_analyzer import analyze_with_ai
from .config import settings
from .data_sources.akshare_source import AkShareSource
from .database import save_run
from .report import generate_report
from .strategies.market_regime import get_market_regime
from .strategies.risk_filters import has_enough_history, should_skip_by_meta
from .strategies.selector import deduplicate_candidates, run_all_strategies
from .utils import normalize_code, setup_logging


logger = setup_logging(settings.log_dir)


def run_daily_pipeline() -> dict:
    logger.info("daily pipeline started")
    source = AkShareSource(settings.data_dir / "cache")
    failure_reasons: Counter[str] = Counter()
    strategy_errors: Counter[str] = Counter()

    stock_list = source.stock_list()
    index_df = source.index_history("000001")
    market_regime = get_market_regime(index_df)
    market_news = source.market_news(limit=30)

    candidates = []
    scanned = 0
    skipped = 0
    universe = stock_list.to_dict("records")

    for row in universe:
        if settings.max_stocks_to_scan > 0 and scanned >= settings.max_stocks_to_scan:
            break
        code = normalize_code(row.get("code"))
        name = str(row.get("name", ""))
        skip, reason = should_skip_by_meta(code, name, row, settings.min_amount)
        if skip:
            skipped += 1
            failure_reasons[reason] += 1
            continue

        scanned += 1
        try:
            history = source.daily_history(code)
            if not has_enough_history(history, settings.min_history_days):
                skipped += 1
                failure_reasons["not_enough_history_or_new_stock"] += 1
                continue
            stock_candidates = run_all_strategies(code, name, history, market_regime, row)
            if stock_candidates:
                related_news = source.stock_news(code, limit=5)
                related_titles = [item.get("title", "") for item in related_news if item.get("title")]
                for candidate in stock_candidates:
                    candidate.metrics["recent_news"] = related_titles
                    candidates.append(candidate)
        except Exception as exc:  # noqa: BLE001
            strategy_errors[type(exc).__name__] += 1
            logger.exception("failed scanning stock %s %s: %s", code, name, exc)
            continue

    deduped = deduplicate_candidates(candidates)
    candidate_dicts = []
    for item in deduped[:30]:
        payload = item.to_dict()
        payload["recent_news"] = payload.get("metrics", {}).get("recent_news", [])
        candidate_dicts.append(payload)

    recommendations = analyze_with_ai(candidate_dicts, market_news, market_regime, top_n=3)
    stats = {
        "scanned": scanned,
        "skipped": skipped,
        "candidates": len(deduped),
        "skip_reasons": dict(failure_reasons.most_common(10)),
        "errors": dict(strategy_errors.most_common(10)),
    }
    report_path = generate_report(market_regime, recommendations, market_news, stats=stats)
    run_id = save_run(market_regime, report_path, recommendations)

    result = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scanned": scanned,
        "skipped": skipped,
        "candidates": len(deduped),
        "recommendations": recommendations,
        "market_regime": market_regime,
        "report_path": str(report_path),
        "skip_reasons": dict(failure_reasons.most_common(10)),
        "errors": dict(strategy_errors.most_common(10)),
    }
    logger.info("daily pipeline finished: %s", result)
    return result
