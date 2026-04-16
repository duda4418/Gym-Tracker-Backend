"""Compatibility shim for the renamed app logging helpers.

This file remains only to avoid broken imports while exposing stdlib logging
symbols to static analysis tools.
"""

from __future__ import annotations

import importlib.util
import sysconfig
from pathlib import Path

from app.core.log_config import configure_logging, get_app_logger

_stdlib_logging_path = Path(sysconfig.get_path("stdlib")) / "logging" / "__init__.py"
_logging_spec = importlib.util.spec_from_file_location("_stdlib_logging", _stdlib_logging_path)
_stdlib_logging = importlib.util.module_from_spec(_logging_spec)
assert _logging_spec and _logging_spec.loader
_logging_spec.loader.exec_module(_stdlib_logging)

Filter = _stdlib_logging.Filter
Formatter = _stdlib_logging.Formatter
INFO = _stdlib_logging.INFO
Logger = _stdlib_logging.Logger
LogRecord = _stdlib_logging.LogRecord
StreamHandler = _stdlib_logging.StreamHandler
getLogger = _stdlib_logging.getLogger


