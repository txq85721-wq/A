from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    if value.upper() == "ALL":
        return -1
    return int(value)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    report_dir: Path = Path(os.getenv("REPORT_DIR", "data/reports"))
    database_url: Path = Path(os.getenv("DATABASE_URL", "data/stock_platform.db"))
    log_dir: Path = Path(os.getenv("LOG_DIR", "data/logs"))
    max_stocks_to_scan: int = _int_env("MAX_STOCKS_TO_SCAN", 1500)
    min_amount: float = float(os.getenv("MIN_AMOUNT", "100000000"))
    min_history_days: int = int(os.getenv("MIN_HISTORY_DAYS", "120"))
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_max_age_hours: int = int(os.getenv("CACHE_MAX_AGE_HOURS", "18"))
    daily_run_time: str = os.getenv("DAILY_RUN_TIME", "20:00")
    timezone: str = os.getenv("TIMEZONE", "Asia/Shanghai")


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.report_dir.mkdir(parents=True, exist_ok=True)
settings.log_dir.mkdir(parents=True, exist_ok=True)
settings.database_url.parent.mkdir(parents=True, exist_ok=True)
