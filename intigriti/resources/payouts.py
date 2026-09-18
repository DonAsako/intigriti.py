"""Endpoints under ``/v1/payouts``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from intigriti.models import Page, Payout
from intigriti.pagination import DEFAULT_PAGE_SIZE, iterate_records
from intigriti.resources._base import Resource, to_epoch

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime


class Payouts(Resource):
    """Bounty payouts owed to the researcher.

    Intigriti flags this endpoint as BETA, so its payloads and filters may change
    before the next API version.
    """

    async def list(
        self,
        *,
        status_id: int | None = None,
        created_since: datetime | int | None = None,
        paid_since: datetime | int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Payout]:
        """List the payouts the researcher has access to.

        Args:
            status_id: Keep only payouts in this state. The API does not document its
                payout status ids, hence a plain integer.
            created_since: Keep only payouts created after this moment. A naive datetime
                is read as UTC.
            paid_since: Keep only payouts settled after this moment.
            limit: Records per page; the API caps this at 500.
            offset: Records to skip.

        Returns:
            One page of payouts, alongside the total number available.
        """
        payload = await self._http.get_json(
            '/payouts',
            params={
                'statusId': status_id,
                'createdSince': to_epoch(created_since),
                'paidSince': to_epoch(paid_since),
                'limit': limit,
                'offset': offset,
            },
        )
        return Page[Payout].model_validate(payload)

    def iterate(
        self,
        *,
        status_id: int | None = None,
        created_since: datetime | int | None = None,
        paid_since: datetime | int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[Payout]:
        """Iterate over every payout, requesting further pages as needed."""

        async def fetch(limit: int, offset: int) -> Page[Payout]:
            return await self.list(
                status_id=status_id,
                created_since=created_since,
                paid_since=paid_since,
                limit=limit,
                offset=offset,
            )

        return iterate_records(fetch, page_size=page_size)
