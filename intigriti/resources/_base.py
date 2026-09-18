"""Shared plumbing for the API resources."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intigriti._http import AsyncHTTPClient


class Resource:
    """Base class binding a group of endpoints to the HTTP transport."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http


def to_epoch(value: datetime | int | None) -> int | None:
    """Convert a datetime to the Unix epoch seconds the API expects.

    Integers pass through untouched, and a naive datetime is read as UTC rather than as
    the machine's local time, so the same call behaves identically on every host.
    """
    if value is None or isinstance(value, int):
        return value
    moment = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return int(moment.timestamp())
