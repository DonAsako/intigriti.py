"""Assets a program puts in scope."""

from __future__ import annotations

from uuid import UUID

from intigriti.models._base import IntigritiModel
from intigriti.models.common import Enumeration


class Skill(IntigritiModel):
    """A skill a researcher needs to test a given asset.

    Attributes:
        id: Identifier of the skill.
        name: Name of the skill.
    """

    id: str
    name: str


class Domain(IntigritiModel):
    """An asset in a program's scope.

    Attributes:
        id: Identifier of the asset.
        type: Nature of the asset; ids listed in :class:`intigriti.enums.DomainType`.
        endpoint: The asset itself — a URL, an IP range, a package name, etc.
        tier: Bounty tier; ids listed in :class:`intigriti.enums.DomainTier`. An asset
            can be listed and still be out of scope, so check this before testing.
        description: Free-form notes from the program about this asset.
        required_skills: Skills the program expects for this asset.
    """

    id: UUID
    type: Enumeration
    endpoint: str
    tier: Enumeration
    description: str
    required_skills: list[Skill]
