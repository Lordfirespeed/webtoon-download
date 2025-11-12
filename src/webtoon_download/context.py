from dataclasses import dataclass

import aiohttp
from aiopath import AsyncPath


@dataclass(frozen=True, slots=True)
class AppContext:
    session: aiohttp.ClientSession
    ephemeral_dir: AsyncPath


__all__ = ("AppContext",)
