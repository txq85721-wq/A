from __future__ import annotations

import json
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert common market-data values to float safely.

    AkShare/EastMoney sometimes returns '-', '--', empty strings, commas, or
    percentage-like strings. Strategy code should not call float() directly on
    external data.
    """
    if value is None:
        return default
    try:
        if isinstance(value, str):
            text = value.strip().replace(",", "")
            if text in {"", "-", "--", "None", "nan", "NaN"}:
                return default
            if text.endswith("%"):
                text = text[:-1]
            return float(text)
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    number = safe_float(value, None)
    if number is None:
        return default
    return int(number)


def normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    digits = re.sub(r"\D", "", text)
    return digits[-6:].zfill(6) if digits else ""


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("a_share_platform")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    file_handler = RotatingFileHandler(log_dir / "daily.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def extract_json_array(text: str) -> list[Any]:
    """Extract a JSON array from model output.

    Handles plain JSON, fenced Markdown code blocks, and responses that contain
    explanatory text before/after the JSON array.
    """
    if not text:
        return []
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(cleaned[start : end + 1])
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []
