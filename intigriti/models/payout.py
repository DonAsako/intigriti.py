"""Bounty payouts owed to the researcher."""

from __future__ import annotations

from datetime import datetime

from intigriti.models._base import IntigritiModel
from intigriti.models.common import Enumeration, Money


class Payout(IntigritiModel):
    """A bounty payout.

    Intigriti flags the payouts endpoint as BETA, so these fields may change before the
    next API version.

    Attributes:
        status: State of the payout. Its ids are not documented by the API.
        paid_at: When the payout was settled, or ``None`` while it is pending.
    """

    id: str
    amount: Money
    status: Enumeration
    created_at: datetime
    paid_at: datetime | None
