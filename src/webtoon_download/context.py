from dataclasses import dataclass

import aiohttp
from aiopath import AsyncPath

from webtoon_download.config.series import SeriesConfig


@dataclass(frozen=True, slots=True)
class AppContext:
    session: aiohttp.ClientSession
    ephemeral_dir: AsyncPath
    all_series_config: list[SeriesConfig]


__all__ = ("AppContext",)
