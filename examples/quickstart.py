"""Walk the programs you have access to, then print the scope of the first one.

Run it with your personal access token in the environment::

    INTIGRITI_TOKEN=xxxxx uv run python examples/quickstart.py

Generate a token from your Intigriti account settings; see
https://intigriti-researcher-api.readme.io/reference/configuration.
"""

from __future__ import annotations

import asyncio
import os
import sys

import intigriti


async def main(token: str) -> None:
    """Query a few endpoints and print what comes back."""
    async with intigriti.Client(token) as client:
        page = await client.programs.list(status=intigriti.ProgramStatus.OPEN, limit=100)
        print(f'{page.max_count} open programs available')

        # Pages are walked for you; the API serves 50 records at a time by default.
        async for program in client.programs.iterate(following=True):
            print(f'  {program.handle}: up to {program.max_bounty.value} {program.max_bounty.currency}')

        detail = await client.programs.get(page.records[0].id)
        print(f'\nScope of {detail.name}:')
        for domain in detail.domains.content or []:
            print(f'  {domain.endpoint} ({domain.type.value}, {domain.tier.value})')


if __name__ == '__main__':
    pat = os.environ.get('INTIGRITI_TOKEN')
    if not pat:
        sys.exit('Set INTIGRITI_TOKEN to a personal access token first.')
    try:
        asyncio.run(main(pat))
    except intigriti.IntigritiAPIError as error:
        sys.exit(f'The API refused the request: {error}')
