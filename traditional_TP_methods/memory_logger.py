"""Track peak memory usage for algorithm executions."""

from __future__ import annotations

import tracemalloc
from typing import Optional


class MemoryLogger:
    """Singleton-like helper to monitor memory consumption."""

    _instance: Optional["MemoryLogger"] = None

    def __new__(cls) -> "MemoryLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._max_memory = 0.0
            cls._instance._tracing = False
        return cls._instance

    def get_max_memory(self) -> float:
        """Return the maximum resident memory (MB) observed so far."""
        if not self._tracing:
            return self._max_memory
        _, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / (1024 * 1024)
        if peak_mb > self._max_memory:
            self._max_memory = peak_mb
        return self._max_memory

    def reset(self) -> None:
        """Reset recorded metrics and restart tracing."""
        self._max_memory = 0.0
        if self._tracing:
            tracemalloc.stop()
            self._tracing = False
        tracemalloc.start()
        self._tracing = True

    def check_memory(self) -> float:
        """Update the peak memory measurement and return current usage (MB)."""
        if not self._tracing:
            tracemalloc.start()
            self._tracing = True
        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / (1024 * 1024)
        peak_mb = peak / (1024 * 1024)
        if peak_mb > self._max_memory:
            self._max_memory = peak_mb
        return current_mb


def get_instance() -> MemoryLogger:
    """Return the shared MemoryLogger instance."""
    return MemoryLogger()
