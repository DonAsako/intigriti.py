"""Programs: the bug bounty engagements a researcher can take part in."""

from __future__ import annotations

from uuid import UUID

from intigriti.models._base import IntigritiModel
from intigriti.models.common import Enumeration, Money, Version, VersionWithAttachments
from intigriti.models.domain import Domain
from intigriti.models.rules_of_engagement import RulesOfEngagement


class ProgramWebLinks(IntigritiModel):
    """Links to the program on the Intigriti web application.

    Attributes:
        detail: URL of the program's detail page.
    """

    detail: str


class Program(IntigritiModel):
    """A program as listed in the overview.

    Scope and rules are not included here; fetch the program's details for those.

    Attributes:
        id: Identifier of the program.
        handle: Slug used in web URLs, alongside the company handle.
        name: Display name of the program.
        following: Whether the researcher follows this program.
        min_bounty: Bounty for the lowest tier and severity.
        max_bounty: Bounty for the highest tier and severity.
        confidentiality_level: How the program is joined; ids listed in
            :class:`intigriti.enums.ConfidentialityLevel`.
        status: Lifecycle state; ids listed in :class:`intigriti.enums.ProgramStatus`.
        type: Reward model; ids listed in :class:`intigriti.enums.ProgramType`.
        web_links: Links to the program on the web application.
        industry: Industry of the company, when it discloses one.
    """

    id: UUID
    handle: str
    name: str
    following: bool
    min_bounty: Money
    max_bounty: Money
    confidentiality_level: Enumeration
    status: Enumeration
    type: Enumeration
    web_links: ProgramWebLinks
    industry: str | None


class ProgramDetail(IntigritiModel):
    """A program with the current version of its scope and rules.

    Bounty ranges are not repeated here; read them from the overview.

    Attributes:
        id: Identifier of the program.
        handle: Slug used in web URLs, alongside the company handle.
        name: Display name of the program.
        following: Whether the researcher follows this program.
        confidentiality_level: How the program is joined; ids listed in
            :class:`intigriti.enums.ConfidentialityLevel`.
        status: Lifecycle state; ids listed in :class:`intigriti.enums.ProgramStatus`.
        type: Reward model; ids listed in :class:`intigriti.enums.ProgramType`.
        domains: Current version of the in-scope assets.
        rules_of_engagement: Current version of the rules, or ``None`` when the program
            publishes none.
        web_links: Links to the program on the web application.
        industry: Industry of the company, when it discloses one.
    """

    id: UUID
    handle: str
    name: str
    following: bool
    confidentiality_level: Enumeration
    status: Enumeration
    type: Enumeration
    domains: Version[list[Domain]]
    rules_of_engagement: VersionWithAttachments[RulesOfEngagement] | None
    web_links: ProgramWebLinks
    industry: str | None


class ProgramDomains(IntigritiModel):
    """Response of the versioned domains endpoint.

    Attributes:
        domains: The requested version of the in-scope assets.
    """

    domains: Version[list[Domain]]


class ProgramRulesOfEngagement(IntigritiModel):
    """Response of the versioned rules-of-engagement endpoint.

    Attributes:
        rules_of_engagement: The requested version of the rules, with its attachments.
    """

    rules_of_engagement: VersionWithAttachments[RulesOfEngagement]
