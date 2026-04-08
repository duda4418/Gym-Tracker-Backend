class DatabaseUnavailableError(Exception):
    """Raised when the application cannot reach the database in time."""

    def __init__(self, detail: str = "Database is temporarily unavailable. Please try again shortly.") -> None:
        super().__init__(detail)
        self.detail = detail

