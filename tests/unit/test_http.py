"""Unit tests for the async HTTP transport, driven by httpx mock transports."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from intigriti._http import DEFAULT_BASE_URL, AsyncHTTPClient
from intigriti.exceptions import (
    IntigritiAPIError,
    IntigritiAuthenticationError,
    IntigritiConflictError,
    IntigritiNotFoundError,
    IntigritiPermissionError,
    IntigritiRateLimitError,
    IntigritiServerError,
    IntigritiServiceUnavailableError,
    IntigritiValidationError,
)

# Dummy value for the mocked transports, not a real credential.
TOKEN = 'pat-0123456789'  # noqa: S105
API_HOST = 'https://api.intigriti.test'
API_ROOT = f'{API_HOST}/external/researcher/v1'
PREFIX = '/external/researcher/v1'


def _error_body(status: int, title: str, code: str) -> dict[str, Any]:
    """Build an error body in the shape the API returns."""

    return {
        'identifier': '942585ca-e134-4677-8726-67c75359a92f',
        'title': title,
        'status': status,
        'code': code,
        'extraParameters': {},
    }


def _make_transport(responses: dict[str, tuple[int, object]]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        key = f'{request.method} {request.url.path}'
        if key not in responses:
            body = _error_body(404, 'Not found.', 'NOTFOUND001')
            return httpx.Response(404, json=body)
        status, payload = responses[key]
        headers = {}
        if status == 403 and 'throttled' in request.url.path:
            headers['Retry-After'] = '42'
        return httpx.Response(status, content=json.dumps(payload).encode(), headers=headers)

    return httpx.MockTransport(handler)


@pytest.fixture
def http_client() -> AsyncHTTPClient:
    inner = httpx.AsyncClient(
        base_url=API_ROOT,
        headers={'Authorization': f'Bearer {TOKEN}'},
        transport=_make_transport(
            {
                f'GET {PREFIX}/programs': (200, {'maxCount': 1, 'records': [{'id': 'abc'}]}),
                f'GET {PREFIX}/programs/abc': (200, {'id': 'abc', 'name': 'Acme'}),
                f'POST {PREFIX}/programs': (200, {'id': 'new'}),
                f'PATCH {PREFIX}/programs/abc': (200, {'id': 'abc', 'name': 'updated'}),
                f'PUT {PREFIX}/programs/abc': (200, {'id': 'abc'}),
                f'DELETE {PREFIX}/programs/abc': (204, None),
                f'GET {PREFIX}/error_400': (400, _error_body(400, 'Invalid request.', 'VALID001')),
                f'GET {PREFIX}/error_401': (401, _error_body(401, 'Access denied.', 'UNAUTH001')),
                f'GET {PREFIX}/error_403': (403, _error_body(403, 'Forbidden.', 'FORBID001')),
                f'GET {PREFIX}/throttled': (403, _error_body(403, 'Rate limit exceeded.', 'FORBID002')),
                f'GET {PREFIX}/error_409': (409, _error_body(409, 'Conflict.', 'CONFL001')),
                f'GET {PREFIX}/error_500': (500, _error_body(500, 'Server error.', 'SRV001')),
                f'GET {PREFIX}/error_503': (503, _error_body(503, 'Service unavailable.', 'SRV002')),
            }
        ),
    )
    return AsyncHTTPClient(TOKEN, client=inner)


@pytest.mark.unit
class TestAsyncHTTPClientInit:
    def test_version_appended_to_default_base_url(self) -> None:
        c = AsyncHTTPClient(TOKEN)
        assert c.api_root == 'https://api.intigriti.com/external/researcher/v1'
        assert c.base_url == DEFAULT_BASE_URL

    def test_version_not_double_appended(self) -> None:
        c = AsyncHTTPClient(TOKEN, base_url=f'{DEFAULT_BASE_URL}/v1')
        assert c.api_root == f'{DEFAULT_BASE_URL}/v1'

    def test_trailing_slash_stripped(self) -> None:
        c = AsyncHTTPClient(TOKEN, base_url=f'{DEFAULT_BASE_URL}/')
        assert c.api_root == f'{DEFAULT_BASE_URL}/v1'

    def test_custom_api_version(self) -> None:
        c = AsyncHTTPClient(TOKEN, base_url=API_HOST, api_version='v2')
        assert c.api_root == f'{API_HOST}/v2'

    def test_token_sent_as_bearer(self) -> None:
        c = AsyncHTTPClient(TOKEN)
        assert c._client.headers['Authorization'] == f'Bearer {TOKEN}'
        assert c._client.headers['Accept'] == 'application/json'

    def test_empty_token_rejected(self) -> None:
        with pytest.raises(ValueError, match='personal access token'):
            AsyncHTTPClient('')


@pytest.mark.unit
class TestHTTPMethods:
    async def test_get_json_returns_parsed_payload(self, http_client: AsyncHTTPClient) -> None:
        data = await http_client.get_json('/programs')
        assert data == {'maxCount': 1, 'records': [{'id': 'abc'}]}

    async def test_post_json_returns_parsed_payload(self, http_client: AsyncHTTPClient) -> None:
        data = await http_client.post_json('/programs', json={'name': 'test'})
        assert data['id'] == 'new'

    async def test_patch_json_returns_updated_resource(self, http_client: AsyncHTTPClient) -> None:
        data = await http_client.patch_json('/programs/abc', json={'name': 'updated'})
        assert data['name'] == 'updated'

    async def test_put_json_returns_parsed_payload(self, http_client: AsyncHTTPClient) -> None:
        data = await http_client.put_json('/programs/abc', json={'name': 'x'})
        assert data['id'] == 'abc'

    async def test_delete_json_handles_empty_body(self, http_client: AsyncHTTPClient) -> None:
        assert await http_client.delete_json('/programs/abc') is None

    async def test_none_params_are_dropped(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(str(request.url.query, 'utf-8'))
            return httpx.Response(200, json={'records': []})

        inner = httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(handler))
        client = AsyncHTTPClient(TOKEN, client=inner)
        await client.get_json('/programs', params={'limit': 50, 'offset': 0, 'statusId': None, 'following': True})
        assert seen == ['limit=50&offset=0&following=true']


@pytest.mark.unit
class TestHTTPErrors:
    async def test_400_raises_validation_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiValidationError) as exc_info:
            await http_client.get_json('/error_400')
        assert exc_info.value.message == 'Invalid request.'
        assert exc_info.value.code == 'VALID001'
        assert exc_info.value.identifier == '942585ca-e134-4677-8726-67c75359a92f'

    async def test_401_raises_authentication_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiAuthenticationError) as exc_info:
            await http_client.get_json('/error_401')
        assert 'Intigriti API error 401 [UNAUTH001]: Access denied.' in str(exc_info.value)

    async def test_403_raises_permission_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiPermissionError) as exc_info:
            await http_client.get_json('/error_403')
        assert not isinstance(exc_info.value, IntigritiRateLimitError)

    async def test_403_with_retry_after_raises_rate_limit_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiRateLimitError) as exc_info:
            await http_client.get_json('/throttled')
        assert exc_info.value.retry_after == 42.0
        assert isinstance(exc_info.value, IntigritiPermissionError)

    async def test_404_raises_not_found_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiNotFoundError):
            await http_client.get_json('/unmapped')

    async def test_409_raises_conflict_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiConflictError):
            await http_client.get_json('/error_409')

    async def test_500_raises_server_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiServerError):
            await http_client.get_json('/error_500')

    async def test_503_raises_service_unavailable_error(self, http_client: AsyncHTTPClient) -> None:
        with pytest.raises(IntigritiServiceUnavailableError):
            await http_client.get_json('/error_503')

    async def test_non_json_body_falls_back_to_text(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(418, content=b'<html>teapot</html>')

        inner = httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(handler))
        client = AsyncHTTPClient(TOKEN, client=inner)
        with pytest.raises(IntigritiAPIError) as exc_info:
            await client.get_json('/programs')
        assert exc_info.value.message == '<html>teapot</html>'
        assert exc_info.value.code == ''

    async def test_unparseable_retry_after_is_ignored(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json=_error_body(403, 'Forbidden.', 'F1'), headers={'Retry-After': 'tomorrow'})

        inner = httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(handler))
        client = AsyncHTTPClient(TOKEN, client=inner)
        with pytest.raises(IntigritiPermissionError) as exc_info:
            await client.get_json('/programs')
        assert not isinstance(exc_info.value, IntigritiRateLimitError)


@pytest.mark.unit
class TestGetBytes:
    """Off-host attachment downloads must not carry the personal access token."""

    @staticmethod
    def _client(seen: list[str | None]) -> AsyncHTTPClient:
        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get('authorization'))
            return httpx.Response(200, content=b'file-bytes')

        inner = httpx.AsyncClient(
            base_url=API_ROOT,
            headers={'Authorization': f'Bearer {TOKEN}'},
            transport=httpx.MockTransport(handler),
        )
        return AsyncHTTPClient(TOKEN, client=inner)

    async def test_authorization_kept_on_api_host(self) -> None:
        seen: list[str | None] = []
        content = await self._client(seen).get_bytes(f'{API_ROOT}/programs/abc/attachment')
        assert content == b'file-bytes'
        assert seen == [f'Bearer {TOKEN}']

    async def test_authorization_dropped_off_host(self) -> None:
        seen: list[str | None] = []
        content = await self._client(seen).get_bytes('https://cdn.example.test/attachment.pdf')
        assert content == b'file-bytes'
        assert seen == [None]


@pytest.mark.unit
class TestLifecycle:
    @staticmethod
    def _inner() -> httpx.AsyncClient:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        return httpx.AsyncClient(base_url=API_ROOT, transport=httpx.MockTransport(handler))

    async def test_context_manager_closes_owned_client(self) -> None:
        async with AsyncHTTPClient(TOKEN) as client:
            assert client._owns_client
        assert client._client.is_closed

    async def test_injected_client_is_left_open(self) -> None:
        inner = self._inner()
        async with AsyncHTTPClient(TOKEN, client=inner) as client:
            assert not client._owns_client
        assert not inner.is_closed
        await inner.aclose()

    async def test_empty_body_decodes_to_none(self) -> None:
        client = AsyncHTTPClient(TOKEN, client=self._inner())
        assert await client.get_json('/programs') is None
