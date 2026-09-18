"""Unit tests for the response models, using payloads shaped like the API's own."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from intigriti.enums import ActivityType, ConfidentialityLevel, DomainTier, DomainType, ProgramStatus, ProgramType
from intigriti.models import (
    Activity,
    Domain,
    Page,
    Payout,
    Program,
    ProgramActivity,
    ProgramDetail,
    ProgramDomains,
    ProgramRulesOfEngagement,
)

PROGRAM_ID = '2b7f9a0d-1c22-4a1a-9c3f-3f1b1e361d5e'
VERSION_ID = '7c9e6679-7425-40de-944b-e07fc1f90ae7'
EPOCH = 1758153600
PUBLISHED_AT = datetime(2025, 9, 18, tzinfo=UTC)


def _program() -> dict[str, Any]:
    return {
        'id': PROGRAM_ID,
        'handle': 'acme-bbp',
        'name': 'Acme BBP',
        'following': True,
        'minBounty': {'value': '50', 'currency': 'EUR'},
        'maxBounty': {'value': '7500.50', 'currency': 'EUR'},
        'confidentialityLevel': {'id': 4, 'value': 'Public'},
        'status': {'id': 3, 'value': 'Open'},
        'type': {'id': 1, 'value': 'Bug bounty'},
        'webLinks': {'detail': 'https://app.intigriti.com/researcher/programs/acme/acme-bbp/detail'},
        'industry': 'Technology',
    }


def _domains_version() -> dict[str, Any]:
    return {
        'id': VERSION_ID,
        'createdAt': EPOCH,
        'content': [
            {
                'id': '9c3f2b7f-9a0d-4c22-8a1a-3f1b1e361d5e',
                'type': {'id': 7, 'value': 'Wildcard'},
                'endpoint': '*.acme.com',
                'tier': {'id': 4, 'value': 'Tier 1'},
                'description': 'Main platform.',
                'requiredSkills': [{'id': 'web', 'name': 'Web'}],
            }
        ],
    }


def _rules_version() -> dict[str, Any]:
    return {
        'id': VERSION_ID,
        'createdAt': EPOCH,
        'content': {
            'description': 'Do not test production payments.',
            'testingRequirements': {
                'intigritiMe': True,
                'automatedTooling': 5,
                'userAgent': 'researcher-handle',
                'requestHeader': None,
            },
            'safeHarbour': True,
        },
        'attachments': [{'url': 'https://files.intigriti.test/roe.pdf', 'code': 12}],
    }


@pytest.mark.unit
class TestProgramOverview:
    def test_page_decodes_camel_case_payload(self) -> None:
        page = Page[Program].model_validate({'maxCount': 137, 'records': [_program()]})

        assert page.max_count == 137
        program = page.records[0]
        assert program.id == UUID(PROGRAM_ID)
        assert program.name == 'Acme BBP'
        assert program.web_links.detail.endswith('/detail')

    def test_money_is_exact(self) -> None:
        program = Program.model_validate(_program())

        assert program.max_bounty.value == Decimal('7500.50')
        assert program.max_bounty.currency == 'EUR'

    def test_enumerations_compare_against_the_documented_ids(self) -> None:
        program = Program.model_validate(_program())

        assert program.status.id == ProgramStatus.OPEN
        assert program.type.id == ProgramType.BUG_BOUNTY
        assert program.confidentiality_level.id == ConfidentialityLevel.PUBLIC
        assert program.status.value == 'Open'

    def test_unknown_enumeration_id_is_kept_as_an_integer(self) -> None:
        payload = _program()
        payload['status'] = {'id': 99, 'value': 'Something new'}

        program = Program.model_validate(payload)

        assert program.status.id == 99
        assert program.status.id not in set(ProgramStatus)

    def test_industry_may_be_absent(self) -> None:
        payload = _program()
        payload['industry'] = None

        assert Program.model_validate(payload).industry is None

    def test_snake_case_input_is_accepted(self) -> None:
        payload = _program()
        payload['min_bounty'] = payload.pop('minBounty')
        payload['web_links'] = payload.pop('webLinks')

        assert Program.model_validate(payload).min_bounty.value == Decimal(50)

    def test_unknown_fields_are_ignored(self) -> None:
        payload = _program()
        payload['fieldAddedNextYear'] = 'whatever'

        assert Program.model_validate(payload).handle == 'acme-bbp'

    def test_models_are_frozen(self) -> None:
        program = Program.model_validate(_program())

        with pytest.raises(ValidationError):
            program.name = 'Renamed'  # type: ignore[misc]


@pytest.mark.unit
class TestProgramDetail:
    @staticmethod
    def _payload(*, with_rules: bool = True) -> dict[str, Any]:
        payload = _program()
        del payload['minBounty']
        del payload['maxBounty']
        payload['domains'] = _domains_version()
        payload['rulesOfEngagement'] = _rules_version() if with_rules else None
        return payload

    def test_domains_version_is_decoded(self) -> None:
        detail = ProgramDetail.model_validate(self._payload())

        assert detail.domains.id == UUID(VERSION_ID)
        assert detail.domains.created_at == PUBLISHED_AT
        assert detail.domains.content is not None
        domain = detail.domains.content[0]
        assert domain.endpoint == '*.acme.com'
        assert domain.type.id == DomainType.WILDCARD
        assert domain.tier.id == DomainTier.TIER_1
        assert [skill.name for skill in domain.required_skills] == ['Web']

    def test_rules_of_engagement_version_carries_attachments(self) -> None:
        detail = ProgramDetail.model_validate(self._payload())

        rules = detail.rules_of_engagement
        assert rules is not None
        assert rules.content is not None
        assert rules.content.safe_harbour is True
        assert rules.content.testing_requirements.automated_tooling == 5
        assert rules.content.testing_requirements.request_header is None
        assert rules.attachments[0].url.endswith('roe.pdf')

    def test_rules_of_engagement_may_be_absent(self) -> None:
        detail = ProgramDetail.model_validate(self._payload(with_rules=False))

        assert detail.rules_of_engagement is None

    def test_withheld_version_content_is_none(self) -> None:
        payload = self._payload()
        payload['domains']['content'] = None

        assert ProgramDetail.model_validate(payload).domains.content is None


@pytest.mark.unit
class TestVersionedEndpoints:
    def test_program_domains_envelope(self) -> None:
        envelope = ProgramDomains.model_validate({'domains': _domains_version()})

        assert envelope.domains.content is not None
        assert isinstance(envelope.domains.content[0], Domain)

    def test_program_rules_of_engagement_envelope(self) -> None:
        envelope = ProgramRulesOfEngagement.model_validate({'rulesOfEngagement': _rules_version()})

        assert envelope.rules_of_engagement.content is not None
        assert envelope.rules_of_engagement.content.testing_requirements.intigriti_me is True


@pytest.mark.unit
class TestProgramActivity:
    @staticmethod
    def _payload() -> dict[str, Any]:
        return {
            'programId': PROGRAM_ID,
            'activity': {'fromVersionId': VERSION_ID, 'toVersionId': '1c22b2c3-9a0d-4a1a-9c3f-3f1b1e361d5e'},
            'type': {'id': 1, 'value': 'New domains version added'},
            'createdAt': EPOCH,
            'following': True,
        }

    def test_version_change_activity(self) -> None:
        activity = ProgramActivity.model_validate(self._payload())

        assert activity.program_id == UUID(PROGRAM_ID)
        assert activity.type.id == ActivityType.DOMAINS_VERSION_ADDED
        assert activity.created_at == PUBLISHED_AT
        assert activity.activity.from_version_id == UUID(VERSION_ID)

    def test_undocumented_activity_shape_is_preserved(self) -> None:
        payload = self._payload()
        payload['activity'] = {'newStatus': {'id': 4, 'value': 'Suspended'}}
        payload['type'] = {'id': 3, 'value': 'Program status changed'}

        activity = ProgramActivity.model_validate(payload)

        assert activity.activity.from_version_id is None
        assert activity.activity.model_extra == {'newStatus': {'id': 4, 'value': 'Suspended'}}

    def test_activity_is_frozen_like_the_other_models(self) -> None:
        with pytest.raises(ValidationError):
            Activity().to_version_id = UUID(VERSION_ID)  # type: ignore[misc]


@pytest.mark.unit
class TestPayout:
    @staticmethod
    def _payload() -> dict[str, Any]:
        return {
            'id': 'PO-2025-0001',
            'amount': {'value': '1500', 'currency': 'EUR'},
            'status': {'id': 2, 'value': 'Paid'},
            'createdAt': EPOCH,
            'paidAt': EPOCH + 86400,
        }

    def test_paid_payout(self) -> None:
        payout = Payout.model_validate(self._payload())

        assert payout.amount.value == Decimal(1500)
        assert payout.created_at == PUBLISHED_AT
        assert payout.paid_at == datetime(2025, 9, 19, tzinfo=UTC)

    def test_pending_payout_has_no_paid_at(self) -> None:
        payload = self._payload()
        payload['paidAt'] = None

        assert Payout.model_validate(payload).paid_at is None

    def test_page_of_payouts(self) -> None:
        page = Page[Payout].model_validate({'maxCount': 1, 'records': [self._payload()]})

        assert page.records[0].id == 'PO-2025-0001'
