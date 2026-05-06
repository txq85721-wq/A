from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings
from .pipeline import run_daily_pipeline
from .utils import setup_logging


logger = setup_logging(settings.log_dir)


def run_scheduler() -> None:
    """Run the daily job at settings.daily_run_time in settings.timezone.

    This avoids relying on the host machine's local timezone. The loop checks the
    configured timezone every 20 seconds and guarantees at most one run per date.
    """
    tz = ZoneInfo(settings.timezone)
    last_run_date: str | None = None
    logger.info("scheduler started, daily_run_time=%s, timezone=%s", settings.daily_run_time, settings.timezone)
    print(f"Scheduler started. Daily job time: {settings.daily_run_time}, timezone: {settings.timezone}")

    while True:
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        if current_time == settings.daily_run_time and last_run_date != current_date:
            logger.info("scheduled run triggered at %s", now.isoformat(timespec="seconds"))
            try:
                run_daily_pipeline()
                last_run_date = current_date
            except Exception as exc:  # noqa: BLE001
                logger.exception("scheduled run failed: %s", exc)
                last_run_date = current_date
        time.sleep(20)
