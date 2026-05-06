from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Callable


class TaskManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._last_result: dict[str, Any] | None = None
        self._last_error: str | None = None
        self._started_at: str | None = None
        self._finished_at: str | None = None

    def start(self, func: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            if self._running:
                return {"status": "running", "message": "任务正在运行，请勿重复启动。"}
            self._running = True
            self._last_error = None
            self._started_at = datetime.now().isoformat(timespec="seconds")
            self._finished_at = None

        def runner() -> None:
            try:
                result = func()
                with self._lock:
                    self._last_result = result
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    self._last_error = repr(exc)
            finally:
                with self._lock:
                    self._running = False
                    self._finished_at = datetime.now().isoformat(timespec="seconds")

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        return {"status": "started", "started_at": self._started_at}

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "started_at": self._started_at,
                "finished_at": self._finished_at,
                "last_error": self._last_error,
                "last_result": self._last_result,
            }


task_manager = TaskManager()
