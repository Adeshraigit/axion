from __future__ import annotations

from collections.abc import AsyncGenerator


async def get_db_session() -> AsyncGenerator[None, None]:
    yield None


async def init_db() -> None:
    return
