from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .config import settings


def generate_report(market_regime: dict, recommendations: list[dict], news: list[dict]) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = settings.report_dir / "latest_report.md"
    dated_path = settings.report_dir / f"report_{today}.md"

    lines: list[str] = []
    lines.append(f"# A股每日交易方案推荐报告 - {today}")
    lines.append("")
    lines.append("> 仅供学习研究，不构成投资建议。请结合自身风险承受能力独立判断。")
    lines.append("")
    lines.append("## 市场状态")
    lines.append("")
    lines.append(f"- 状态：{market_regime.get('regime', 'unknown')}")
    lines.append(f"- 最大建议总仓位：{int(float(market_regime.get('max_position', 0)) * 100)}%")
    lines.append(f"- 原因：{market_regime.get('reason', '')}")
    lines.append("")
    lines.append("## 今日/近期最推荐的3只股票")
    lines.append("")

    if not recommendations:
        lines.append("当前没有满足策略和风控条件的股票。建议等待更明确的市场机会。")
    else:
        for idx, item in enumerate(recommendations, start=1):
            lines.append(f"### {idx}. {item.get('name', '')}（{item.get('code', '')}）")
            lines.append("")
            lines.append(f"- 策略来源：{item.get('strategy', '')}")
            lines.append(f"- 综合评分：{item.get('ai_score', item.get('score', ''))}")
            lines.append(f"- 买入时机：{item.get('buy_timing', '')}")
            lines.append(f"- 止损策略：{item.get('stop_loss', '')}")
            lines.append(f"- 止盈策略：{item.get('take_profit', '')}")
            lines.append(f"- 持仓周期：{item.get('holding_period', '')}")
            lines.append(f"- 仓位建议：{item.get('position', '')}")
            lines.append(f"- 推荐理由：{item.get('ai_summary', '')}")
            risk_notes = item.get("risk_notes") or []
            if risk_notes:
                lines.append("- 风险提示：")
                for risk in risk_notes:
                    lines.append(f"  - {risk}")
            recent_news = item.get("recent_news") or []
            if recent_news:
                lines.append("- 关联市场消息：")
                for title in recent_news[:5]:
                    lines.append(f"  - {title}")
            lines.append("")

    lines.append("## 最近市场消息")
    lines.append("")
    for item in news[:10]:
        title = item.get("title", "")
        source = item.get("source", "")
        time = item.get("time", "")
        if title:
            lines.append(f"- {title}（{source} {time}）")
    lines.append("")
    lines.append("## 风控纪律")
    lines.append("")
    lines.append("- 不在市场弱势时重仓。")
    lines.append("- 不追连续加速后的高位后排股。")
    lines.append("- 单票亏损达到预设止损必须处理。")
    lines.append("- 推荐结果需要结合第二天开盘表现确认，不能机械挂单。")

    content = "\n".join(lines)
    report_path.write_text(content, encoding="utf-8")
    dated_path.write_text(content, encoding="utf-8")
    return report_path
