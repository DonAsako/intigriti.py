# intigriti.py

[![CI](https://github.com/DonAsako/intigriti.py/actions/workflows/ci.yml/badge.svg)](https://github.com/DonAsako/intigriti.py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A Python wrapper for the [Intigriti](https://www.intigriti.com/) API.

> **Status:** early development — the client is not implemented yet, the public API will change.

## Requirements

- Python **3.13+**

## Installation

```sh
uv add intigriti
# or
pip install intigriti
```

Not published yet — for now, install from source:

```sh
uv add git+https://github.com/DonAsako/intigriti.py
```

## Usage

Coming soon.

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

| Tool                                               | Purpose                                                                    |
| -------------------------------------------------- | -------------------------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                   | Dependency & virtualenv management                                         |
| [Hatchling](https://hatch.pypa.io/)                | PEP 517 build backend                                                      |
| [Ruff](https://docs.astral.sh/ruff/)               | Linter + formatter                                                         |
| [Mypy](https://mypy.readthedocs.io/)               | Static type checking (strict mode)                                         |
| [Pytest](https://docs.pytest.org/)                 | Test runner (+ coverage, asyncio, benchmark, xdist, mock, timeout, dotenv) |
| [pre-commit](https://pre-commit.com/)              | Git hooks orchestration                                                    |
| [gitlint](https://jorisroovers.github.io/gitlint/) | Conventional Commits enforcement                                           |
| [GitHub Actions](.github/workflows/ci.yml)         | CI: lint, type-check, tests on every push/PR                               |
| [just](https://github.com/casey/just)              | Task runner for common dev commands (optional)                             |

## Layout

```text
.
├── intigriti/              # source package
│   ├── __init__.py
│   └── py.typed            # PEP 561 marker (ships type hints to consumers)
├── tests/
│   └── unit/
├── .github/
│   ├── workflows/ci.yml    # CI pipeline
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

## Disclaimer

Unofficial project, not affiliated with or endorsed by Intigriti.

## License

[MIT](LICENSE)
