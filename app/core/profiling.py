from __future__ import annotations

import importlib
import logging
from threading import Lock

from app.core.config import Settings

_profiling_lock = Lock()
_profiling_configured = False
_logger = logging.getLogger("gym_tracker")


def configure_profiling(settings: Settings) -> None:
    """Configure Pyroscope continuous profiling when explicitly enabled."""
    global _profiling_configured

    if not settings.PYROSCOPE_ENABLED:
        return

    with _profiling_lock:
        if _profiling_configured:
            return

        try:
            pyroscope = importlib.import_module("pyroscope")
        except ModuleNotFoundError:
            _logger.warning(
                "Pyroscope profiling is enabled but the Python client is not installed; profiling will stay disabled outside the container image."
            )
            return

        pyroscope.configure(
            application_name=settings.PYROSCOPE_APPLICATION_NAME,
            server_address=settings.PYROSCOPE_SERVER_ADDRESS,
            sample_rate=settings.PYROSCOPE_SAMPLE_RATE,
            gil_only=settings.PYROSCOPE_GIL_ONLY,
            enable_logging=settings.PYROSCOPE_ENABLE_LOGGING,
            tags={
                "environment": settings.OTEL_ENVIRONMENT,
                "version": settings.OTEL_SERVICE_VERSION,
            },
        )

        _profiling_configured = True


