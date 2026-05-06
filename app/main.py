from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from .database import latest_run
from .pipeline import run_daily_pipeline

app = FastAPI(title="A股本地股票买卖方案推荐平台")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    run = latest_run()
    if not run:
        return """
        <html><head><title>A股推荐平台</title></head>
        <body style='font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto;'>
        <h1>A股本地股票买卖方案推荐平台</h1>
        <p>当前还没有生成报告。请先运行：</p>
        <pre>python run.py --once</pre>
        <p>或访问 <a href='/run'>/run</a> 手动触发一次。</p>
        </body></html>
        """

    cards = []
    for idx, item in enumerate(run["recommendations"], start=1):
        news_items = "".join(f"<li>{n}</li>" for n in item.get("recent_news", [])[:5])
        risks = "".join(f"<li>{r}</li>" for r in item.get("risk_notes", [])[:5])
        cards.append(f"""
        <section style='border:1px solid #ddd; border-radius:12px; padding:18px; margin:16px 0;'>
          <h2>{idx}. {item.get('name', '')}（{item.get('code', '')}）</h2>
          <p><b>策略：</b>{item.get('strategy', '')}</p>
          <p><b>评分：</b>{item.get('ai_score', item.get('score', ''))}</p>
          <p><b>买入时机：</b>{item.get('buy_timing', '')}</p>
          <p><b>止损：</b>{item.get('stop_loss', '')}</p>
          <p><b>止盈：</b>{item.get('take_profit', '')}</p>
          <p><b>持仓：</b>{item.get('holding_period', '')}</p>
          <p><b>仓位：</b>{item.get('position', '')}</p>
          <p><b>理由：</b>{item.get('ai_summary', '')}</p>
          <h3>风险提示</h3><ul>{risks}</ul>
          <h3>相关消息</h3><ul>{news_items}</ul>
        </section>
        """)

    return f"""
    <html>
    <head><title>A股推荐平台</title></head>
    <body style='font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; line-height:1.6;'>
      <h1>A股本地股票买卖方案推荐平台</h1>
      <p><b>更新时间：</b>{run['created_at']}</p>
      <p><b>市场状态：</b>{run['market_regime'].get('regime')}；{run['market_regime'].get('reason')}</p>
      <p><a href='/report'>查看 Markdown 报告</a> ｜ <a href='/run'>立即重新运行</a></p>
      {''.join(cards)}
      <p style='color:#777'>仅供学习研究，不构成投资建议。</p>
    </body>
    </html>
    """


@app.get("/run")
def run_now() -> dict:
    return run_daily_pipeline()


@app.get("/api/latest")
def api_latest() -> dict:
    return latest_run() or {"message": "no report yet"}


@app.get("/report", response_class=PlainTextResponse)
def report() -> str:
    run = latest_run()
    if not run:
        return "暂无报告"
    path = Path(run["report_path"])
    if not path.exists():
        return "报告文件不存在，请重新运行。"
    return path.read_text(encoding="utf-8")
