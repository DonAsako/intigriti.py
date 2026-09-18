"""The feed of changes published by programs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from intigriti.models._base import IntigritiModel
from intigriti.models.common import Enumeration


class Activity(IntigritiModel):
    """What changed in a program.

    The API declares this payload as abstract and documents only its version-change
    shape, so this model keeps the fields it does not know instead of dropping them:
    read those through ``model_extra``.

    Attributes:
        from_version_id: Version the program moved away from, on a version change.
        to_version_id: Version the program moved to, on a version change.
    """

    model_config = ConfigDict(extra='allow')

    from_version_id: UUID | None = None
    to_version_id: UUID | None = None


class ProgramActivity(IntigritiModel):
    """One event on the program activity feed.

    Attributes:
        program_id: Program the event belongs to.
        activity: What changed.
        type: Kind of event; ids listed in :class:`intigriti.enums.ActivityType`.
        created_at: When the event was published.
        following: Whether the researcher follows the program the event belongs to.
    """

    program_id: UUID
    activity: Activity
    type: Enumeration
    created_at: datetime
    following: bool
