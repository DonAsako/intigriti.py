"""Endpoints under ``/v1/programs``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from intigriti.models import (
    Domain,
    Page,
    Program,
    ProgramActivity,
    ProgramDetail,
    ProgramDomains,
    ProgramRulesOfEngagement,
    RulesOfEngagement,
    Version,
    VersionWithAttachments,
)
from intigriti.pagination import DEFAULT_PAGE_SIZE, iterate_records
from intigriti.resources._base import Resource, to_epoch

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime
    from uuid import UUID

    from intigriti.enums import ProgramStatus, ProgramType

# Defined here rather than inline: inside the class body, ``list`` resolves to the
# ``list`` method rather than to the builtin.
type DomainsVersion = Version[list[Domain]]
type RulesVersion = VersionWithAttachments[RulesOfEngagement]


class Programs(Resource):
    """Programs, their scope and their activity feed.

    The API filters programs on status, type and whether you follow them. Its written
    documentation also advertises a ``confidentialityLevel`` filter, which neither the
    OpenAPI specification declares nor the live API honours — sending it returns the
    unfiltered set — so it is deliberately not exposed here.
    """

    async def list(
        self,
        *,
        status: ProgramStatus | int | None = None,
        program_type: ProgramType | int | None = None,
        following: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Program]:
        """List the programs the researcher has access to.

        Args:
            status: Keep only programs in this state, sent as ``statusId``.
            program_type: Keep only programs of this reward model, sent as ``typeId``.
            following: Keep only the programs you follow, or only those you do not.
            limit: Records per page; the API defaults to 50 and caps this at 500.
            offset: Records to skip.

        Returns:
            One page of programs, alongside the total number available.
        """
        payload = await self._http.get_json(
            '/programs',
            params={
                'statusId': status,
                'typeId': program_type,
                'following': following,
                'limit': limit,
                'offset': offset,
            },
        )
        return Page[Program].model_validate(payload)

    def iterate(
        self,
        *,
        status: ProgramStatus | int | None = None,
        program_type: ProgramType | int | None = None,
        following: bool | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[Program]:
        """Iterate over every program, requesting further pages as needed.

        Args:
            status: Keep only programs in this state.
            program_type: Keep only programs of this reward model.
            following: Keep only the programs you follow, or only those you do not.
            page_size: Records per request, between 1 and 500.
        """

        async def fetch(limit: int, offset: int) -> Page[Program]:
            return await self.list(
                status=status,
                program_type=program_type,
                following=following,
                limit=limit,
                offset=offset,
            )

        return iterate_records(fetch, page_size=page_size)

    async def get(self, program_id: UUID | str) -> ProgramDetail:
        """Retrieve a program with the current version of its scope and rules.

        Raises:
            IntigritiPermissionError: The program does not exist, or its details are not
                open to you. The API does not distinguish the two — it answers 403 in
                both cases rather than 404.
        """
        payload = await self._http.get_json(f'/programs/{program_id}')
        return ProgramDetail.model_validate(payload)

    async def domains(self, program_id: UUID | str, version_id: UUID | str) -> DomainsVersion:
        """Retrieve one version of a program's in-scope assets.

        Version ids come from a program's details or from its activity feed.
        """
        payload = await self._http.get_json(f'/programs/{program_id}/domains/{version_id}')
        return ProgramDomains.model_validate(payload).domains

    async def rules_of_engagement(
        self,
        program_id: UUID | str,
        version_id: UUID | str,
    ) -> RulesVersion:
        """Retrieve one version of a program's rules of engagement, with its attachments."""
        payload = await self._http.get_json(f'/programs/{program_id}/rules-of-engagements/{version_id}')
        return ProgramRulesOfEngagement.model_validate(payload).rules_of_engagement

    async def activities(
        self,
        *,
        created_since: datetime | int | None = None,
        following: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[ProgramActivity]:
        """List the events published by programs.

        Args:
            created_since: Keep only events published after this moment. A naive
                datetime is read as UTC.
            following: Keep only events from the programs you follow, or only the others.
            limit: Records per page; the API defaults to the 50 most recent activities
                and caps this at 500.
            offset: Records to skip.

        Returns:
            One page of events, alongside the total number available.
        """
        payload = await self._http.get_json(
            '/programs/activities',
            params={
                'createdSince': to_epoch(created_since),
                'following': following,
                'limit': limit,
                'offset': offset,
            },
        )
        return Page[ProgramActivity].model_validate(payload)

    def iterate_activities(
        self,
        *,
        created_since: datetime | int | None = None,
        following: bool | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[ProgramActivity]:
        """Iterate over every program event, requesting further pages as needed."""

        async def fetch(limit: int, offset: int) -> Page[ProgramActivity]:
            return await self.activities(
                created_since=created_since,
                following=following,
                limit=limit,
                offset=offset,
            )

        return iterate_records(fetch, page_size=page_size)
