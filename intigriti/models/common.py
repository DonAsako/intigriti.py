"""Building blocks shared across the API's resources."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from intigriti.models._base import IntigritiModel


class Money(IntigritiModel):
    """A monetary amount, decoded as :class:`~decimal.Decimal` rather than as a float."""

    value: Decimal
    currency: str


class Enumeration(IntigritiModel):
    """An enumerated value: a stable id paired with its display label.

    Match on ``id``, against the members of :mod:`intigriti.enums` — never on ``value``,
    which is display text and drifts from the documentation.
    """

    id: int
    value: str


class Attachment(IntigritiModel):
    """A file attached to a rules-of-engagement version; its URL may point off-host."""

    url: str
    code: int


class Page[ItemT](IntigritiModel):
    """One page of a paginated collection.

    The paginated endpoints document a default of 50 records and cap ``limit`` at 500;
    walk further with ``offset``. ``max_count`` is the total available, not the size of
    this page.
    """

    max_count: int
    records: list[ItemT]


class Version[ContentT](IntigritiModel):
    """A versioned snapshot of program information.

    Programs publish their scope and rules as versions: the activity feed announces
    each new one, and the versioned endpoints serve a given version by id. ``content``
    is nullable by the API's own declaration.
    """

    id: UUID
    created_at: datetime
    content: ContentT | None


class VersionWithAttachments[ContentT](Version[ContentT]):
    """A :class:`Version` that also carries downloadable files."""

    attachments: list[Attachment]
