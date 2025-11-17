import asyncio
from pathlib import Path
import tomllib
from typing import Annotated

from aiopath import AsyncPath
from pydantic import (
    BaseModel, AfterValidator,
)

from .paths import config_root_dir


def path_to_async_path(value: Path) -> AsyncPath:
    return AsyncPath(value)


type PydanticAsyncPath = Annotated[AsyncPath, AfterValidator(path_to_async_path)]


class DownloaderConfig(BaseModel):
    library_path: PydanticAsyncPath


async def load_downloader_config() -> DownloaderConfig:
    async with (config_root_dir/"downloader.conf.toml").open(mode="r") as handle:
        raw_config = await handle.read()
    untrusted_config = tomllib.loads(raw_config)
    config = DownloaderConfig.model_validate(untrusted_config)
    return config


__all__ = (
    "DownloaderConfig",
    "load_downloader_config",
)
