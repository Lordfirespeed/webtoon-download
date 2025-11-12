import asyncio
from contextlib import AsyncExitStack
from tempfile import TemporaryDirectory

import aiohttp
from aiopath import AsyncPath

from webtoon_download.context import AppContext
from webtoon_download.get_episode_images import get_episode_page_images
from webtoon_download.metadata import Episode, Series


async def main():
    async with AsyncExitStack() as stack:
        async with asyncio.TaskGroup() as tg:
            session_task = tg.create_task(stack.enter_async_context(aiohttp.ClientSession()))

        session = await session_task
        ephemeral_dir = AsyncPath(stack.enter_context(TemporaryDirectory()))
        context = AppContext(session=session, ephemeral_dir=ephemeral_dir)

        series = Series(title_no=7857)
        episode = Episode(series=series, index=40)
        episode_images = await get_episode_page_images(episode, context)
        print(episode_images)

        await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(main())
