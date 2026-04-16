from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

from opentelemetry import trace

from app.core.config import Settings

_logger_lock = Lock()
_logging_configured = False
_APP_LOGGER_NAME = "gym_tracker"


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            record.trace_id = format(span_context.trace_id, "032x")
            record.span_id = format(span_context.span_id, "016x")
        else:
            record.trace_id = ""
            record.span_id = ""

        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
        }

        for field in ("method", "path", "status_code", "duration_ms", "client_host"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_app_logger() -> logging.Logger:
    return logging.getLogger(_APP_LOGGER_NAME)


def configure_logging(settings: Settings) -> None:
    global _logging_configured

    with _logger_lock:
        if _logging_configured:
            return

        logs_dir = Path(settings.LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / settings.LOG_FILE_NAME

        formatter = JsonFormatter()
        trace_filter = TraceContextFilter()

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(trace_filter)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)

        logger = get_app_logger()
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        logger.handlers.clear()
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        logger.propagate = False

        _logging_configured = True


