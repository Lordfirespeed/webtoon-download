import asyncio
import tomllib

from aiopath import AsyncPath
from pydantic import (
    BaseModel,
)

from .paths import series_config_dir


class SeriesConfig(BaseModel):
    title_no: int


async def load_series_config(path: AsyncPath) -> tuple[AsyncPath, SeriesConfig]:
    async with path.open(mode="r") as handle:
        raw_config = await handle.read()
    untrusted_config = tomllib.loads(raw_config)
    config = SeriesConfig.model_validate(untrusted_config)
    return path, config


async def load_all_series_config() -> list[SeriesConfig]:
    path: AsyncPath
    # todo: I would like to use rglob(), but this is blocked by https://github.com/alexdelorenzo/aiopath/issues/42
    tasks = [asyncio.create_task(load_series_config(path)) async for path in series_config_dir.glob("*.conf.toml")]
    configs = []
    async for task in asyncio.as_completed(tasks):
        path, config = await task
        configs.append(config)
    return configs


__all__ = (
    "SeriesConfig",
    "load_series_config",
    "load_all_series_config",
)
