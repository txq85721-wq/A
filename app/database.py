from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .config import settings


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_url)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                market_regime TEXT NOT NULL,
                report_path TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                strategy TEXT NOT NULL,
                score REAL NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        conn.commit()


def save_run(market_regime: dict, report_path: Path, recommendations: Iterable[dict]) -> int:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs(created_at, market_regime, report_path) VALUES (?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), json.dumps(market_regime, ensure_ascii=False), str(report_path)),
        )
        run_id = int(cur.lastrowid)
        for rank, item in enumerate(recommendations, start=1):
            conn.execute(
                """
                INSERT INTO recommendations(run_id, rank, code, name, strategy, score, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    rank,
                    item.get("code", ""),
                    item.get("name", ""),
                    item.get("strategy", ""),
                    float(item.get("score", 0)),
                    json.dumps(item, ensure_ascii=False),
                ),
            )
        conn.commit()
        return run_id


def latest_run() -> dict | None:
    init_db()
    with connect() as conn:
        run = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if not run:
            return None
        rows = conn.execute("SELECT * FROM recommendations WHERE run_id = ? ORDER BY rank", (run["id"],)).fetchall()
        return {
            "id": run["id"],
            "created_at": run["created_at"],
            "market_regime": json.loads(run["market_regime"]),
            "report_path": run["report_path"],
            "recommendations": [json.loads(row["payload"]) for row in rows],
        }
