from collections.abc import Generator

from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.utils.errors.database import DatabaseUnavailableError


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except (OperationalError, SQLAlchemyTimeoutError) as exc:
        session.rollback()
        raise DatabaseUnavailableError() from exc
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
