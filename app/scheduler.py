from __future__ import annotations

import time

import schedule

from .pipeline import run_daily_pipeline


def run_scheduler() -> None:
    schedule.every().day.at("20:00").do(run_daily_pipeline)
    print("Scheduler started. Daily job time: 20:00")
    while True:
        schedule.run_pending()
        time.sleep(30)
