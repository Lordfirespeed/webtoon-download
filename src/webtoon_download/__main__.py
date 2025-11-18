import asyncio
from contextlib import AsyncExitStack
from tempfile import TemporaryDirectory

import aiohttp
from aiopath import AsyncPath

from webtoon_download.config.downloader import load_downloader_config
from webtoon_download.config.series import load_all_series_config
from webtoon_download.context import AppContext
from webtoon_download.download_queue import get_download_queue
from webtoon_download.metadata import Episode, Series, SeriesIdentifier, EpisodeIdentifier
from webtoon_download.util.async_interrupt import create_interrupt_future


async def main():
    async with AsyncExitStack() as stack:
        async with asyncio.TaskGroup() as tg:
            session_task = tg.create_task(stack.enter_async_context(aiohttp.ClientSession()))
            downloader_config_task = tg.create_task(load_downloader_config())
            all_series_config_task = tg.create_task(load_all_series_config())

        session = await session_task
        downloader_config = await downloader_config_task
        all_series_config = await all_series_config_task
        ephemeral_dir = AsyncPath(stack.enter_context(TemporaryDirectory()))
        context = AppContext(
            session=session,
            ephemeral_dir=ephemeral_dir,
            downloader_config=downloader_config,
            all_series_config=all_series_config,
        )

        download_queue = await stack.enter_async_context(get_download_queue(context))

        for series_config in context.all_series_config:
            series_id = SeriesIdentifier(series_config.title_no)
            series = await Series.fetch_populated_series(series_id, context)
            for episode_index in range(1, series.free_episode_count + 1):
                episode_id = EpisodeIdentifier.of(series, episode_index)
                episode = await Episode.fetch_populated_episode(episode_id, context)
                await download_queue.put(episode)

        await create_interrupt_future()

if __name__ == "__main__":
    asyncio.run(main())
