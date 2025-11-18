import tomllib

from pydantic import BaseModel

from webtoon_download.util.pydantic_aiopath import PydanticAsyncPath
from .paths import config_root_dir


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
