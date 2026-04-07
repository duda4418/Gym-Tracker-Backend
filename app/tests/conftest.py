from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


@pytest.fixture
def make_query():
    def _make_query(
        *,
        first: Any = None,
        all_items: Any | None = None,
        scalar: Any = None,
        delete_count: int = 1,
    ) -> MagicMock:
        query = MagicMock()
        query.filter.return_value = query
        query.filter_by.return_value = query
        query.join.return_value = query
        query.order_by.return_value = query
        query.group_by.return_value = query
        query.limit.return_value = query
        query.first.return_value = first
        query.all.return_value = all_items or []
        query.scalar.return_value = scalar
        query.delete.return_value = delete_count
        return query

    return _make_query


@pytest.fixture
def patch_session_scope(monkeypatch):
    def _patch(module, session: MagicMock):
        @contextmanager
        def _scope():
            yield session

        monkeypatch.setattr(module, "session_scope", _scope)

    return _patch
