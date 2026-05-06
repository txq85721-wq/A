from __future__ import annotations

import html
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from .database import latest_run
from .pipeline import run_daily_pipeline
from .task_manager import task_manager

app = FastAPI(title="A股本地股票买卖方案推荐平台")


def esc(value: object) -> str:
    return html.escape(str(value or ""))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    run = latest_run()
    status = task_manager.status()
    status_text = "运行中" if status["running"] else "空闲"
    if not run:
        return f"""
        <html><head><title>A股推荐平台</title></head>
        <body style='font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto;'>
        <h1>A股本地股票买卖方案推荐平台</h1>
        <p><b>任务状态：</b>{esc(status_text)}</p>
        <p>当前还没有生成报告。请先运行：</p>
        <pre>python run.py --once</pre>
        <p>或用 POST 请求触发：<code>curl -X POST http://127.0.0.1:8000/run</code></p>
        <p><a href='/status'>查看任务状态</a></p>
        </body></html>
        """

    cards = []
    for idx, item in enumerate(run["recommendations"], start=1):
        news_items = "".join(f"<li>{esc(n)}</li>" for n in item.get("recent_news", [])[:5])
        risks = "".join(f"<li>{esc(r)}</li>" for r in item.get("risk_notes", [])[:5])
        cards.append(f"""
        <section style='border:1px solid #ddd; border-radius:12px; padding:18px; margin:16px 0;'>
          <h2>{idx}. {esc(item.get('name', ''))}（{esc(item.get('code', ''))}）</h2>
          <p><b>策略：</b>{esc(item.get('strategy', ''))}</p>
          <p><b>评分：</b>{esc(item.get('ai_score', item.get('score', '')))}</p>
          <p><b>买入时机：</b>{esc(item.get('buy_timing', ''))}</p>
          <p><b>止损：</b>{esc(item.get('stop_loss', ''))}</p>
          <p><b>止盈：</b>{esc(item.get('take_profit', ''))}</p>
          <p><b>持仓：</b>{esc(item.get('holding_period', ''))}</p>
          <p><b>仓位：</b>{esc(item.get('position', ''))}</p>
          <p><b>理由：</b>{esc(item.get('ai_summary', ''))}</p>
          <h3>风险提示</h3><ul>{risks}</ul>
          <h3>相关消息</h3><ul>{news_items}</ul>
        </section>
        """)

    return f"""
    <html>
    <head><title>A股推荐平台</title></head>
    <body style='font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; line-height:1.6;'>
      <h1>A股本地股票买卖方案推荐平台</h1>
      <p><b>任务状态：</b>{esc(status_text)}</p>
      <p><b>更新时间：</b>{esc(run['created_at'])}</p>
      <p><b>市场状态：</b>{esc(run['market_regime'].get('regime'))}；{esc(run['market_regime'].get('reason'))}</p>
      <p><a href='/report'>查看 Markdown 报告</a> ｜ <a href='/status'>查看任务状态</a></p>
      <p>手动运行请使用：<code>curl -X POST http://127.0.0.1:8000/run</code></p>
      {''.join(cards)}
      <p style='color:#777'>仅供学习研究，不构成投资建议。</p>
    </body>
    </html>
    """


@app.post("/run")
def run_now() -> dict:
    return task_manager.start(run_daily_pipeline)


@app.get("/status")
def run_status() -> dict:
    return task_manager.status()


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
