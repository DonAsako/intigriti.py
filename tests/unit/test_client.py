"""Unit tests for the public client, its resources and the pagination helper."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
import pytest

import intigriti
from intigriti.enums import ProgramStatus, ProgramType
from intigriti.models import Page, Program, ProgramActivity, ProgramDetail
from intigriti.pagination import MAX_PAGE_SIZE, iterate_records
from intigriti.resources._base import to_epoch

# Dummy value for the mocked transports, not a real credential.
TOKEN = 'pat-0123456789'  # noqa: S105
API_ROOT = 'https://api.intigriti.test/external/researcher/v1'
PROGRAM_ID = UUID('2b7f9a0d-1c22-4a1a-9c3f-3f1b1e361d5e')
VERSION_ID = UUID('7c9e6679-7425-40de-944b-e07fc1f90ae7')
EPOCH = 1758153600


def _program(index: int) -> dict[str, Any]:
    return {
        'id': str(PROGRAM_ID),
        'handle': f'program-{index}',
        'name': f'Program {index}',
        'following': True,
        'minBounty': {'value': '50', 'currency': 'EUR'},
        'maxBounty': {'value': '5000', 'currency': 'EUR'},
        'confidentialityLevel': {'id': 4, 'value': 'Public'},
        'status': {'id': 3, 'value': 'Open'},
        'type': {'id': 1, 'value': 'Bug bounty'},
        'webLinks': {'detail': 'https://app.intigriti.test/p'},
        'industry': None,
    }


def _domains_version() -> dict[str, Any]:
    return {
        'id': str(VERSION_ID),
        'createdAt': EPOCH,
        'content': [
            {
                'id': str(PROGRAM_ID),
                'type': {'id': 1, 'value': 'URL'},
                'endpoint': 'acme.test',
                'tier': {'id': 4, 'value': 'Tier 1'},
                'description': '',
                'requiredSkills': [],
            }
        ],
    }


def _rules_version() -> dict[str, Any]:
    return {
        'id': str(VERSION_ID),
        'createdAt': EPOCH,
        'content': {
            'description': 'Be nice.',
            'testingRequirements': {
                'intigritiMe': False,
                'automatedTooling': None,
                'userAgent': None,
                'requestHeader': None,
            },
            'safeHarbour': True,
        },
        'attachments': [{'url': 'https://files.intigriti.test/roe.pdf', 'code': 1}],
    }


def _activity(index: int) -> dict[str, Any]:
    return {
        'programId': str(PROGRAM_ID),
        'activity': {'fromVersionId': None, 'toVersionId': str(VERSION_ID)},
        'type': {'id': 1, 'value': 'New domains version added'},
        'createdAt': EPOCH + index,
        'following': True,
    }


def _payout(index: int) -> dict[str, Any]:
    return {
        'id': f'PO-{index}',
        'amount': {'value': '100', 'currency': 'EUR'},
        'status': {'id': 2, 'value': 'Paid'},
        'createdAt': EPOCH,
        'paidAt': None,
    }


def _make_client(
    dataset: list[dict[str, Any]],
    *,
    seen: list[httpx.URL] | None = None,
    detail: dict[str, Any] | None = None,
    max_count: int | None = None,
) -> intigriti.Client:
    """Build a client whose transport slices ``dataset`` the way the API paginates."""

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request.url)
        path = request.url.path
        if path.endswith('/domains/' + str(VERSION_ID)):
            return httpx.Response(200, json={'domains': _domains_version()})
        if path.endswith('/rules-of-engagements/' + str(VERSION_ID)):
            return httpx.Response(200, json={'rulesOfEngagement': _rules_version()})
        if detail is not None and path.endswith(f'/programs/{PROGRAM_ID}'):
            return httpx.Response(200, json=detail)
        limit = int(request.url.params.get('limit', 50))
        offset = int(request.url.params.get('offset', 0))
        window = dataset[offset : offset + limit]
        total = len(dataset) if max_count is None else max_count
        return httpx.Response(200, json={'maxCount': total, 'records': window})

    inner = httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(handler))
    return intigriti.Client(TOKEN, base_url=API_ROOT, client=inner)


@pytest.mark.unit
class TestClient:
    def test_exposes_its_resources(self) -> None:
        client = intigriti.Client(TOKEN)

        assert client.api_root == 'https://api.intigriti.com/external/researcher/v1'
        assert client.programs is not None
        assert client.payouts is not None

    def test_rejects_an_empty_token(self) -> None:
        with pytest.raises(ValueError, match='personal access token'):
            intigriti.Client('')

    async def test_context_manager_leaves_an_injected_client_open(self) -> None:
        inner = httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(lambda _r: httpx.Response(204)))
        async with intigriti.Client(TOKEN, base_url=API_ROOT, client=inner) as client:
            assert client.api_root == API_ROOT
        assert not inner.is_closed
        await inner.aclose()

    async def test_context_manager_closes_an_owned_client(self) -> None:
        async with intigriti.Client(TOKEN) as client:
            http = client._http
        assert http._client.is_closed


@pytest.mark.unit
class TestProgramsList:
    async def test_returns_a_typed_page(self) -> None:
        client = _make_client([_program(1), _program(2)])

        page = await client.programs.list()

        assert isinstance(page, Page)
        assert page.max_count == 2
        assert [program.handle for program in page.records] == ['program-1', 'program-2']
        assert isinstance(page.records[0], Program)

    async def test_filters_are_sent_with_the_api_spelling(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(1)], seen=seen)

        await client.programs.list(status=ProgramStatus.OPEN, program_type=ProgramType.HYBRID, following=True, limit=10)

        params = seen[0].params
        assert params['statusId'] == '3'
        assert params['typeId'] == '2'
        assert params['following'] == 'true'
        assert params['limit'] == '10'

    async def test_unset_filters_are_not_sent(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(1)], seen=seen)

        await client.programs.list(following=False)

        assert str(seen[0].params) == 'following=false'


@pytest.mark.unit
class TestProgramsIterate:
    async def test_walks_every_page(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(i) for i in range(5)], seen=seen)

        handles = [program.handle async for program in client.programs.iterate(page_size=2)]

        assert handles == [f'program-{i}' for i in range(5)]
        assert [(url.params['limit'], url.params['offset']) for url in seen] == [('2', '0'), ('2', '2'), ('2', '4')]

    async def test_stops_on_a_short_page_without_an_extra_request(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(i) for i in range(3)], seen=seen)

        records = [program async for program in client.programs.iterate(page_size=5)]

        assert len(records) == 3
        assert len(seen) == 1

    async def test_stops_when_the_api_overstates_max_count(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(i) for i in range(2)], seen=seen, max_count=10_000)

        records = [program async for program in client.programs.iterate(page_size=2)]

        # Page two comes back empty; without that guard, max_count would loop forever.
        assert len(records) == 2
        assert len(seen) == 2

    async def test_carries_the_filters_into_every_request(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_program(i) for i in range(3)], seen=seen)

        _ = [program async for program in client.programs.iterate(status=ProgramStatus.OPEN, page_size=1)]

        assert all(url.params['statusId'] == '3' for url in seen)

    @pytest.mark.parametrize('page_size', [0, -1, MAX_PAGE_SIZE + 1])
    async def test_rejects_an_out_of_range_page_size(self, page_size: int) -> None:
        client = _make_client([_program(1)])

        with pytest.raises(ValueError, match='page_size must be between'):
            _ = [program async for program in client.programs.iterate(page_size=page_size)]


@pytest.mark.unit
class TestProgramDetailEndpoints:
    async def test_get_returns_the_detail_model(self) -> None:
        detail = _program(1)
        del detail['minBounty']
        del detail['maxBounty']
        detail['domains'] = _domains_version()
        detail['rulesOfEngagement'] = _rules_version()
        client = _make_client([], detail=detail)

        program = await client.programs.get(PROGRAM_ID)

        assert isinstance(program, ProgramDetail)
        assert program.domains.content is not None
        assert program.domains.content[0].endpoint == 'acme.test'

    async def test_domains_unwraps_the_envelope(self) -> None:
        client = _make_client([])

        version = await client.programs.domains(PROGRAM_ID, VERSION_ID)

        assert version.id == VERSION_ID
        assert version.content is not None
        assert version.content[0].endpoint == 'acme.test'

    async def test_rules_of_engagement_unwraps_the_envelope(self) -> None:
        client = _make_client([])

        version = await client.programs.rules_of_engagement(PROGRAM_ID, VERSION_ID)

        assert version.content is not None
        assert version.content.safe_harbour is True
        assert version.attachments[0].code == 1


@pytest.mark.unit
class TestProgramActivities:
    async def test_returns_a_typed_page(self) -> None:
        client = _make_client([_activity(0), _activity(1)])

        page = await client.programs.activities()

        assert isinstance(page.records[0], ProgramActivity)
        assert page.records[0].activity.to_version_id == VERSION_ID

    async def test_created_since_is_sent_as_epoch_seconds(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_activity(0)], seen=seen)

        await client.programs.activities(created_since=datetime(2025, 9, 18, tzinfo=UTC))

        assert seen[0].params['createdSince'] == str(EPOCH)

    async def test_iterates_over_every_activity(self) -> None:
        client = _make_client([_activity(i) for i in range(4)])

        records = [activity async for activity in client.programs.iterate_activities(page_size=2)]

        assert len(records) == 4


@pytest.mark.unit
class TestPayouts:
    async def test_returns_a_typed_page(self) -> None:
        client = _make_client([_payout(1)])

        page = await client.payouts.list()

        assert page.records[0].id == 'PO-1'
        assert page.records[0].paid_at is None

    async def test_filters_are_sent_with_the_api_spelling(self) -> None:
        seen: list[httpx.URL] = []
        client = _make_client([_payout(1)], seen=seen)

        await client.payouts.list(status_id=2, created_since=EPOCH, paid_since=datetime(2025, 9, 18, tzinfo=UTC))

        params = seen[0].params
        assert params['statusId'] == '2'
        assert params['createdSince'] == str(EPOCH)
        assert params['paidSince'] == str(EPOCH)

    async def test_iterates_over_every_payout(self) -> None:
        client = _make_client([_payout(i) for i in range(3)])

        records = [payout async for payout in client.payouts.iterate(page_size=2)]

        assert [payout.id for payout in records] == ['PO-0', 'PO-1', 'PO-2']


@pytest.mark.unit
class TestEpochConversion:
    def test_naive_datetimes_are_read_as_utc(self) -> None:
        naive = datetime(2025, 9, 18, 0, 0)  # noqa: DTZ001 -- the point of the test
        aware = datetime(2025, 9, 18, tzinfo=UTC)

        assert to_epoch(naive) == to_epoch(aware) == EPOCH

    def test_integers_and_none_pass_through(self) -> None:
        assert to_epoch(EPOCH) == EPOCH
        assert to_epoch(None) is None


@pytest.mark.unit
class TestIterateRecordsDirectly:
    async def test_an_empty_first_page_yields_nothing(self) -> None:
        async def fetch(_limit: int, _offset: int) -> Page[Program]:
            return Page[Program].model_validate({'maxCount': 0, 'records': []})

        assert [record async for record in iterate_records(fetch)] == []
