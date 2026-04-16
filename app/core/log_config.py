from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

from fastapi import Request
from opentelemetry import trace

from app.core.config import Settings

_logger_lock = Lock()
_logging_configured = False
_APP_LOGGER_NAME = "gym_tracker"
_STANDARD_LOG_RECORD_FIELDS = set(
    logging.LogRecord("", logging.INFO, "", 0, "", (), None).__dict__.keys()
)
_UUID_SEGMENT_RE = re.compile(
    r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_NUMERIC_SEGMENT_RE = re.compile(r"^\d+$")


def _is_sensitive_id_field(field_name: str) -> bool:
    return field_name.endswith("_id") or field_name.endswith("_ids")


def partial_mask_identifier(value: object) -> object:
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return [partial_mask_identifier(item) for item in value]

    if isinstance(value, dict):
        return {key: partial_mask_identifier(item) for key, item in value.items()}

    text = str(value)
    alnum_positions = [index for index, char in enumerate(text) if char.isalnum()]

    if len(alnum_positions) <= 4:
        return "*" * len(text)

    if len(alnum_positions) <= 8:
        keep_start = 2
        keep_end = 2
    else:
        keep_start = 4
        keep_end = 4

    visible_positions = set(alnum_positions[:keep_start] + alnum_positions[-keep_end:])
    masked_chars = []
    for index, char in enumerate(text):
        if not char.isalnum() or index in visible_positions:
            masked_chars.append(char)
        else:
            masked_chars.append("*")

    return "".join(masked_chars)


def sanitize_path(path: str) -> str:
    if not path:
        return path

    sanitized_segments = []
    for segment in path.strip("/").split("/"):
        if not segment:
            continue

        if _UUID_SEGMENT_RE.match(segment) or _NUMERIC_SEGMENT_RE.match(segment):
            sanitized_segments.append("{id}")
        else:
            sanitized_segments.append(segment)

    return "/" + "/".join(sanitized_segments) if sanitized_segments else "/"


def get_safe_request_path(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path or sanitize_path(request.url.path)


def sanitize_request_scope(request: Request) -> str:
    safe_path = get_safe_request_path(request)
    request.scope["path"] = safe_path
    request.scope["query_string"] = b""
    request.scope["raw_path"] = safe_path.encode("utf-8")
    return safe_path


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

        for field_name, value in record.__dict__.items():
            if field_name in payload or field_name in _STANDARD_LOG_RECORD_FIELDS:
                continue
            if field_name in {"trace_id", "span_id"}:
                continue

            payload[field_name] = (
                partial_mask_identifier(value)
                if _is_sensitive_id_field(field_name)
                else value
            )

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


