"""The rules a program sets for security testing."""

from __future__ import annotations

from intigriti.models._base import IntigritiModel


class TestingRequirements(IntigritiModel):
    """Constraints a researcher must respect while testing.

    Attributes:
        intigriti_me: Whether the program asks researchers to use their ``@intigriti.me``
            address.
        automated_tooling: Maximum requests per second allowed for automated tooling,
            or ``None`` when the program sets no limit.
        user_agent: User agent to identify your traffic with, when the program wants one.
        request_header: Request header to identify your traffic with, when the program
            wants one.
    """

    intigriti_me: bool
    automated_tooling: int | None
    user_agent: str | None
    request_header: str | None


class RulesOfEngagement(IntigritiModel):
    """The content of a rules-of-engagement version.

    Attributes:
        description: The program's rules, as written by the company.
        safe_harbour: Whether the company commits to a safe harbour policy.
    """

    description: str
    testing_requirements: TestingRequirements
    safe_harbour: bool
