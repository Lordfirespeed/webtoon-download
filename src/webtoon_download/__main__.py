import asyncio
from contextlib import AsyncExitStack
from tempfile import TemporaryDirectory

import aiohttp
from aiopath import AsyncPath

from webtoon_download.config.series import load_all_series_config
from webtoon_download.context import AppContext
from webtoon_download.get_episode_images import download_episode
from webtoon_download.metadata import Episode, Series, SeriesIdentifier, EpisodeIdentifier
from webtoon_download.util.async_interrupt import create_interrupt_future


async def main():
    async with AsyncExitStack() as stack:
        async with asyncio.TaskGroup() as tg:
            session_task = tg.create_task(stack.enter_async_context(aiohttp.ClientSession()))
            all_series_config_task = tg.create_task(load_all_series_config())

        session = await session_task
        all_series_config = await all_series_config_task
        ephemeral_dir = AsyncPath(stack.enter_context(TemporaryDirectory()))
        context = AppContext(session=session, ephemeral_dir=ephemeral_dir, all_series_config=all_series_config)

        series_id = SeriesIdentifier(7857)
        series = await Series.fetch_populated_series(series_id, context)
        episode_id = EpisodeIdentifier.of(series, 40)
        episode = await Episode.fetch_populated_episode(episode_id, context)
        pages = await download_episode(episode, ephemeral_dir/series.slug/episode.slug, context)

        print(f"got all the pages! look in: {context.ephemeral_dir}")
        await create_interrupt_future()

if __name__ == "__main__":
    asyncio.run(main())
