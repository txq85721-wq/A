from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    report_dir: Path = Path(os.getenv("REPORT_DIR", "data/reports"))
    database_url: Path = Path(os.getenv("DATABASE_URL", "data/stock_platform.db"))
    max_stocks_to_scan: int = int(os.getenv("MAX_STOCKS_TO_SCAN", "500"))


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.report_dir.mkdir(parents=True, exist_ok=True)
settings.database_url.parent.mkdir(parents=True, exist_ok=True)
