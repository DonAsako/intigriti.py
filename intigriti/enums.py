"""Enumerated values used by the Intigriti researcher API.

The API models enumerations as ``{"id": 3, "value": "Open"}`` objects, where only the
id is contractual — the label is display text and may be reworded. Compare against the
members below rather than against ``value``::

    if program.status.id == ProgramStatus.OPEN:
        ...

These are a convenience, not a whitelist: an id Intigriti adds later is decoded as a
plain integer instead of raising, so a new program status never breaks a running
client.

The labels are the other reason to match on ids: they already drift from the written
documentation, which prints ``Invite only`` where the API sends ``InviteOnly``, and
``Program status changed`` where the activity feed sends ``New program status
available``.

Ids are documented at https://intigriti-researcher-api.readme.io/reference/program-1.
"""

from __future__ import annotations

from enum import IntEnum


class ConfidentialityLevel(IntEnum):
    """How a researcher gains access to a program."""

    INVITE_ONLY = 1
    APPLICATION = 2
    REGISTERED = 3
    PUBLIC = 4


class ProgramStatus(IntEnum):
    """Lifecycle state of a program, among the ids the API documents for researchers."""

    OPEN = 3
    SUSPENDED = 4
    CLOSING = 5


class ProgramType(IntEnum):
    """Reward model of a program."""

    BUG_BOUNTY = 1
    HYBRID = 2


class DomainType(IntEnum):
    """Nature of an in-scope asset."""

    URL = 1
    ANDROID = 2
    IOS = 3
    IP_RANGE = 4
    DEVICE = 5
    OTHER = 6
    WILDCARD = 7


class DomainTier(IntEnum):
    """Bounty tier of an in-scope asset.

    Beware the ordering: the ids climb as the tier gets *more* rewarding, so
    ``TIER_1`` (the highest payout) is id 4 and ``TIER_3`` is id 2.
    """

    NO_BOUNTY = 1
    TIER_3 = 2
    TIER_2 = 3
    TIER_1 = 4
    OUT_OF_SCOPE = 5


class ActivityType(IntEnum):
    """Kind of event reported on the program activity feed."""

    DOMAINS_VERSION_ADDED = 1
    RULES_OF_ENGAGEMENT_VERSION_ADDED = 2
    PROGRAM_STATUS_CHANGED = 3
