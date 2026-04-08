import pytest
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError

import app.db.session as session_module
from app.db.session import get_db_session
from app.utils.errors.database import DatabaseUnavailableError


class _FakeSession:
    def __init__(self) -> None:
        self.rollback_called = False
        self.close_called = False

    def rollback(self) -> None:
        self.rollback_called = True

    def close(self) -> None:
        self.close_called = True


@pytest.mark.parametrize(
    ("db_error"),
    [
        OperationalError("SELECT 1", {}, Exception("db down")),
        SQLAlchemyTimeoutError("pool timeout"),
    ],
)
def test_get_db_session_translates_database_errors(monkeypatch, db_error):
    fake_session = _FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake_session)

    generator = get_db_session()
    yielded_session = next(generator)

    assert yielded_session is fake_session

    with pytest.raises(DatabaseUnavailableError, match="Database is temporarily unavailable"):
        generator.throw(db_error)

    assert fake_session.rollback_called is True
    assert fake_session.close_called is True

