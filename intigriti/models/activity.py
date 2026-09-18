"""The feed of changes published by programs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from intigriti.models._base import IntigritiModel
from intigriti.models.common import Enumeration


class Activity(IntigritiModel):
    """What changed in a program.

    The API declares this payload as abstract, and its written documentation covers
    only the version-change shape. The fields below are the ones the live feed sends;
    anything else Intigriti adds is kept rather than dropped, and stays readable through
    ``model_extra``.

    Every field is optional because which ones are set depends on the activity type: a
    new domains or rules-of-engagement version carries the two version ids and no
    status, a status change carries the two statuses and no version id. Status ids are
    listed in :class:`intigriti.enums.ProgramStatus`.
    """

    model_config = ConfigDict(extra='allow')

    from_version_id: UUID | None = None
    to_version_id: UUID | None = None
    from_status: Enumeration | None = None
    to_status: Enumeration | None = None


class ProgramActivity(IntigritiModel):
    """One event on the program activity feed.

    Ids of ``type`` are listed in :class:`intigriti.enums.ActivityType`.
    """

    program_id: UUID
    activity: Activity
    type: Enumeration
    created_at: datetime
    following: bool
