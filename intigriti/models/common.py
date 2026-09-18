"""Building blocks shared across the API's resources."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from intigriti.models._base import IntigritiModel


class Money(IntigritiModel):
    """A monetary amount.

    Attributes:
        value: Amount, decoded as :class:`~decimal.Decimal` to keep it exact.
        currency: Currency of the amount, e.g. ``EUR``.
    """

    value: Decimal
    currency: str


class Enumeration(IntigritiModel):
    """An enumerated value: a stable id paired with its display label.

    Attributes:
        id: Contractual identifier; compare it against the members of
            :mod:`intigriti.enums`.
        value: Human-readable label. Match on ``id`` rather than on this text.
    """

    id: int
    value: str


class Attachment(IntigritiModel):
    """A file attached to a rules-of-engagement version.

    Attributes:
        url: Absolute URL of the file. It may point outside the API host.
        code: Identifier of the attachment.
    """

    url: str
    code: int


class Page[ItemT](IntigritiModel):
    """One page of a paginated collection.

    The paginated endpoints document a default of 50 records and cap ``limit`` at 500;
    walk further with ``offset``.

    Attributes:
        max_count: Total number of records available, not the size of this page.
        records: The records in this page.
    """

    max_count: int
    records: list[ItemT]


class Version[ContentT](IntigritiModel):
    """A versioned snapshot of program information.

    Programs publish their scope and rules as versions: the activity feed announces
    each new one, and the versioned endpoints serve a given version by id.

    Attributes:
        id: Identifier of this version, accepted by the versioned endpoints.
        created_at: When the version was published.
        content: The versioned payload; the API declares it nullable.
    """

    id: UUID
    created_at: datetime
    content: ContentT | None


class VersionWithAttachments[ContentT](Version[ContentT]):
    """A :class:`Version` that also carries downloadable files.

    Attributes:
        attachments: Files published alongside this version.
    """

    attachments: list[Attachment]
