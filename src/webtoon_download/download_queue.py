import asyncio
from asyncio import CancelledError, QueueShutDown
from contextlib import asynccontextmanager

from typing_extensions import AsyncContextManager

from webtoon_download.context import AppContext
from webtoon_download.download_episode import download_episode
from webtoon_download.metadata import Episode


async def work_on_download_queue(queue: asyncio.Queue[Episode], context: AppContext) -> None:
    while True:
        try:
            episode = await queue.get()
        except QueueShutDown:
            return

        destination = context.downloader_config.library_path / episode.series.slug / "Volume 01" / f"Chapter {episode.episode_index}:03"
        try:
            await download_episode(episode, destination, context)
        except FileExistsError:
            queue.task_done()
            print(f"Skipping download for {episode.subpath}, its directory already exists, assuming already downloaded")
            continue

        print(f"Download for {episode.subpath} is complete, see it at {destination}")
        queue.task_done()


def get_worker_tasks(count: int, queue: asyncio.Queue[Episode], context) -> list[asyncio.Task]:
    worker_tasks: list[asyncio.Task] = []
    for _ in range(count):
        worker_task = asyncio.create_task(work_on_download_queue(queue, context))
        worker_tasks.append(worker_task)
    return worker_tasks


def cancel_tasks(tasks: list[asyncio.Task]) -> None:
    for task in tasks: task.cancel()

async def wait_for_cancelled_tasks(tasks: list[asyncio.Task]) -> None:
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if result is None: continue
        if not isinstance(result, Exception): continue
        if isinstance(result, CancelledError): continue
        raise result


@asynccontextmanager
async def get_download_queue(context: AppContext) -> AsyncContextManager[asyncio.Queue[Episode]]:
    queue: asyncio.Queue[Episode] = asyncio.Queue()

    # only one worker - HTTP traffic is less suspicious if we download only 1 episode at a time
    worker_tasks = get_worker_tasks(1, queue, context)
    try:
        yield queue
    finally:
        queue.shutdown()
        await queue.join()
        cancel_tasks(worker_tasks)
        await wait_for_cancelled_tasks(worker_tasks)


__all__ = ("get_download_queue",)
