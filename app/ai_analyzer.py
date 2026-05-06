from __future__ import annotations

import json
from typing import Any

from .config import settings


def _fallback_analysis(candidates: list[dict], news: list[dict], market_regime: dict) -> list[dict]:
    enriched = []
    news_titles = [item.get("title", "") for item in news[:5] if item.get("title")]
    for item in candidates:
        score = float(item.get("score", 0))
        if market_regime.get("regime") == "weak":
            score -= 8
        elif market_regime.get("regime") == "strong":
            score += 5
        item = dict(item)
        item["ai_score"] = round(score, 2)
        item["ai_summary"] = "未配置AI Key，使用本地规则评分。综合考虑策略得分、市场状态、趋势结构和风险约束。"
        item["recent_news"] = news_titles
        enriched.append(item)
    return sorted(enriched, key=lambda x: x.get("ai_score", x.get("score", 0)), reverse=True)


def analyze_with_ai(candidates: list[dict], news: list[dict], market_regime: dict, top_n: int = 3) -> list[dict]:
    if not settings.openai_api_key:
        return _fallback_analysis(candidates, news, market_regime)[:top_n]

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        prompt = {
            "task": "你是A股交易辅助分析器。请从候选股票中选出最推荐的3只，并给出交易方案。只输出JSON数组，不要输出其他文字。",
            "market_regime": market_regime,
            "candidates": candidates[:20],
            "recent_news": news[:20],
            "requirements": [
                "必须包含code,name,strategy,ai_score,buy_timing,stop_loss,take_profit,holding_period,position,ai_summary,recent_news,risk_notes",
                "不要编造新闻；只能引用输入recent_news中的标题",
                "优先考虑策略共振、盈利空间、回撤风险、市场情绪和资金活跃度",
                "输出不构成投资建议，必须保留风险提示",
            ],
        }
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "你是严谨的A股量化和交易风控助手，只能基于给定数据做分析。"},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "[]"
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed[:top_n]
    except Exception:
        pass

    return _fallback_analysis(candidates, news, market_regime)[:top_n]
