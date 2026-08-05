class BaseAPIError(Exception):
    """
    Base class for all API exceptions
    """

    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        status_code: int = 400,
        extra: dict | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(message)
