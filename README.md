# intigriti.py

[![CI](https://github.com/DonAsako/intigriti.py/actions/workflows/ci.yml/badge.svg)](https://github.com/DonAsako/intigriti.py/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/intigriti)](https://pypi.org/project/intigriti/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

> **Unofficial project**, not affiliated with or endorsed by Intigriti.

An async, fully typed Python wrapper for the
[Intigriti researcher API](https://intigriti-researcher-api.readme.io/) — the API behind a
researcher's personal access token, serving programs, their scope and rules of engagement,
the program activity feed and payouts.

> **Which API?** This wraps the **researcher** API only, at
> `https://api.intigriti.com/external/researcher`. Intigriti also runs a separate
> [company API](https://kb.intigriti.com/en/articles/6117846-intigriti-api) for
> organisations automating their own programs; it has its own host, authentication and
> payloads, and is not covered here.

> **Status:** early development — the public API of this library may still change.

## What's covered

Every endpoint of researcher API v1:

| Endpoint                                                        | Method                                                   |
| --------------------------------------------------------------- | -------------------------------------------------------- |
| `GET /v1/programs`                                              | `client.programs.list()` · `.iterate()`                  |
| `GET /v1/programs/{programId}`                                  | `client.programs.get()`                                  |
| `GET /v1/programs/activities`                                   | `client.programs.activities()` · `.iterate_activities()` |
| `GET /v1/programs/{programId}/domains/{versionId}`              | `client.programs.domains()`                              |
| `GET /v1/programs/{programId}/rules-of-engagements/{versionId}` | `client.programs.rules_of_engagement()`                  |
| `GET /v1/payouts` (BETA)                                        | `client.payouts.list()` · `.iterate()`                   |

## Requirements

- Python **3.13+**

## Installation

```sh
uv add intigriti
# or
pip install intigriti
```

To track unreleased work, install from the repository instead:

```sh
uv add git+https://github.com/DonAsako/intigriti.py
```

## Usage

Generate a [personal access token](https://intigriti-researcher-api.readme.io/reference/configuration)
from your Intigriti account settings, then:

```python
import asyncio
import os

import intigriti


async def main() -> None:
    async with intigriti.Client(os.environ["INTIGRITI_TOKEN"]) as client:
        page = await client.programs.list(status=intigriti.ProgramStatus.OPEN, limit=100)
        print(f"{page.max_count} programs available")

        # Pages are walked for you; the API serves 50 records at a time by default.
        async for program in client.programs.iterate(following=True):
            print(program.handle, program.max_bounty.value, program.max_bounty.currency)

        detail = await client.programs.get(page.records[0].id)
        for domain in detail.domains.content or []:
            print(domain.endpoint, domain.tier.value)


asyncio.run(main())
```

The same example, ready to run, lives in
[`examples/quickstart.py`](examples/quickstart.py):

```sh
INTIGRITI_TOKEN=xxxxx uv run python examples/quickstart.py
```

Everything is typed: responses are [Pydantic](https://docs.pydantic.dev/) models with
snake_case attributes, epoch timestamps decoded to aware `datetime`s and bounties to
`Decimal`.

### Enumerations

The API returns enumerations as `{"id": 3, "value": "Open"}`. Only the id is contractual,
so compare against the members of `intigriti.enums` rather than against the label:

```python
if program.status.id == intigriti.ProgramStatus.OPEN:
    ...
```

An id this library does not know is decoded as a plain integer rather than raising, so a
new program status will not break a running client.

### Errors

Failed requests raise an `IntigritiAPIError` subclass carrying the status, the API error
code and the identifier to quote when reporting a problem:

```python
try:
    await client.programs.get(program_id)
except intigriti.IntigritiRateLimitError as exc:
    print("throttled, retry after", exc.retry_after)
except intigriti.IntigritiAPIError as exc:
    print(exc.status_code, exc.code, exc.identifier)
```

Note that Intigriti signals rate limiting with HTTP 403 rather than 429, so
`IntigritiRateLimitError` inherits from `IntigritiPermissionError`.

## Development

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv sync                    # install deps + dev tools
uv run pre-commit install  # install git hooks (pre-commit + commit-msg)
```

With [`just`](https://github.com/casey/just), `just install` does both.

```sh
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy              # type-check
uv run pytest            # tests
uv run pytest --cov      # tests with coverage
```

```sh
just            # list all recipes
just fix        # auto-fix lint + format
just check      # lint + format-check + typecheck + test (mirrors CI)
```

## Tooling

| Tool                                                                       | Purpose                                                                    |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                                           | Dependency & virtualenv management                                         |
| [Hatchling](https://hatch.pypa.io/)                                        | PEP 517 build backend                                                      |
| [Ruff](https://docs.astral.sh/ruff/)                                       | Linter + formatter                                                         |
| [Mypy](https://mypy.readthedocs.io/)                                       | Static type checking (strict mode)                                         |
| [Pytest](https://docs.pytest.org/)                                         | Test runner (+ coverage, asyncio, benchmark, xdist, mock, timeout, dotenv) |
| [pre-commit](https://pre-commit.com/)                                      | Git hooks orchestration                                                    |
| [gitlint](https://jorisroovers.github.io/gitlint/)                         | Conventional Commits enforcement                                           |
| [GitHub Actions](.github/workflows/ci.yml)                                 | CI: lint, type-check, tests on every push/PR                               |
| [python-semantic-release](https://python-semantic-release.readthedocs.io/) | Version, tag, changelog and PyPI release from the commit history           |
| [just](https://github.com/casey/just)                                      | Task runner for common dev commands (optional)                             |

## Layout

```text
.
├── intigriti/              # source package
│   ├── client.py           # public entry point
│   ├── enums.py            # documented enumeration ids
│   ├── exceptions.py       # error hierarchy
│   ├── models/             # typed response models
│   ├── resources/          # endpoint groups (programs, payouts)
│   ├── pagination.py       # limit/offset iteration
│   ├── _http.py            # async transport
│   └── py.typed            # PEP 561 marker (ships type hints to consumers)
├── examples/
│   └── quickstart.py
├── tests/
│   └── unit/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml          # lint, type-check, tests
│   │   └── publish-to-pypi.yml  # release, PyPI publish
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── dependabot.yml
├── .pre-commit-config.yaml
├── .editorconfig
├── .gitlint
├── .yamllint.yaml
├── justfile
├── pyproject.toml          # single source of truth (ruff, mypy, pytest, coverage)
└── uv.lock
```

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md). Commits follow
[Conventional Commits](https://www.conventionalcommits.org/) and are validated by `gitlint`.

## License

[MIT](LICENSE)
