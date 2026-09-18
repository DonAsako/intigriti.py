"""Exception hierarchy mapping the Intigriti API fault contract to Python errors.

Every failed request raises an :class:`IntigritiAPIError` subclass carrying the HTTP
status, plus the error code and identifier when the response body provides them.

See https://intigriti-researcher-api.readme.io/reference/errors.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any


class IntigritiError(Exception):
    """Base exception for every error raised by this client."""


class IntigritiAPIError(IntigritiError):
    """The Intigriti API returned a non-success HTTP response.

    Attributes:
        status_code: HTTP status code returned by the server.
        message: Human-readable error message extracted from the response body.
        code: Intigriti error code identifying the failure, e.g. ``UNAUTH001``.
        identifier: Identifier the API assigns to the failed request; include it when
            reporting the problem to Intigriti.
        extra_parameters: Additional per-error context, when the API returns some.
        payload: Raw decoded response body, when available.
    """

    def __init__(  # noqa: PLR0913
        self,
        status_code: int,
        message: str = '',
        *,
        code: str = '',
        identifier: str = '',
        extra_parameters: dict[str, Any] | None = None,
        payload: Any = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.code = code
        self.identifier = identifier
        self.extra_parameters = extra_parameters or {}
        self.payload = payload
        prefix = f'Intigriti API error {status_code}' + (f' [{code}]' if code else '')
        super().__init__(f'{prefix}: {message}' if message else prefix)


class IntigritiValidationError(IntigritiAPIError):
    """Raised when the request does not comply with the endpoint spec (HTTP 400)."""


class IntigritiAuthenticationError(IntigritiAPIError):
    """Raised when the personal access token is missing, invalid or expired (HTTP 401)."""


class IntigritiPermissionError(IntigritiAPIError):
    """Raised when the token may not perform the action or reach the resource (HTTP 403)."""


class IntigritiRateLimitError(IntigritiPermissionError):
    """Raised when the client exceeds the API rate limit.

    Intigriti signals rate limiting with HTTP 403 rather than 429, hence the
    inheritance from :class:`IntigritiPermissionError`: handlers that catch
    permission errors keep working. An HTTP 429 always maps here; a 403 only does
    when the response carries a ``Retry-After`` header, since a throttled 403 is
    otherwise indistinguishable from an ordinary one.

    Attributes:
        retry_after: Seconds to wait before retrying, when the server sends a delay.
    """

    def __init__(  # noqa: PLR0913
        self,
        status_code: int,
        message: str = '',
        *,
        code: str = '',
        identifier: str = '',
        extra_parameters: dict[str, Any] | None = None,
        payload: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            message=message,
            code=code,
            identifier=identifier,
            extra_parameters=extra_parameters,
            payload=payload,
        )
        self.retry_after = retry_after


class IntigritiNotFoundError(IntigritiAPIError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class IntigritiConflictError(IntigritiAPIError):
    """Raised when the request conflicts with the current state of the resource (HTTP 409)."""


class IntigritiServerError(IntigritiAPIError):
    """Raised for HTTP 5xx responses."""


class IntigritiServiceUnavailableError(IntigritiServerError):
    """Raised when the API is offline (HTTP 503); see https://status.intigriti.com/."""


def error_for_status(  # noqa: PLR0913
    status_code: int,
    message: str = '',
    *,
    code: str = '',
    identifier: str = '',
    extra_parameters: dict[str, Any] | None = None,
    payload: Any = None,
    retry_after: float | None = None,
) -> IntigritiAPIError:
    """Map an HTTP status code to the most specific exception subclass."""

    throttled = status_code == HTTPStatus.TOO_MANY_REQUESTS or (
        status_code == HTTPStatus.FORBIDDEN and retry_after is not None
    )
    if throttled:
        return IntigritiRateLimitError(
            status_code=status_code,
            message=message,
            code=code,
            identifier=identifier,
            extra_parameters=extra_parameters,
            payload=payload,
            retry_after=retry_after,
        )

    mapping: dict[int, type[IntigritiAPIError]] = {
        HTTPStatus.BAD_REQUEST: IntigritiValidationError,
        HTTPStatus.UNAUTHORIZED: IntigritiAuthenticationError,
        HTTPStatus.FORBIDDEN: IntigritiPermissionError,
        HTTPStatus.NOT_FOUND: IntigritiNotFoundError,
        HTTPStatus.CONFLICT: IntigritiConflictError,
        HTTPStatus.SERVICE_UNAVAILABLE: IntigritiServiceUnavailableError,
    }
    cls = mapping.get(status_code)
    if cls is None:
        cls = IntigritiServerError if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR else IntigritiAPIError
    return cls(
        status_code=status_code,
        message=message,
        code=code,
        identifier=identifier,
        extra_parameters=extra_parameters,
        payload=payload,
    )
