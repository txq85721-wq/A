from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import schedule

from .config import settings
from .pipeline import run_daily_pipeline
from .utils import setup_logging


logger = setup_logging(settings.log_dir)


def _run_with_logging() -> None:
    logger.info("scheduled run triggered")
    run_daily_pipeline()


def run_scheduler() -> None:
    """Run the daily scheduler.

    The schedule library uses local process time. This function logs the target
    timezone and current time so users can verify the host clock. For strict
    Beijing-time execution, set the host timezone to Asia/Shanghai or run the
    process in a container configured with TZ=Asia/Shanghai.
    """
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz).isoformat(timespec="seconds")
    schedule.every().day.at(settings.daily_run_time).do(_run_with_logging)
    logger.info("scheduler started, daily_run_time=%s, timezone=%s, now=%s", settings.daily_run_time, settings.timezone, now)
    print(f"Scheduler started. Daily job time: {settings.daily_run_time}, timezone setting: {settings.timezone}")
    while True:
        schedule.run_pending()
        time.sleep(30)
