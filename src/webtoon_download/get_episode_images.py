import asyncio
import tempfile
from copy import replace

from aiopath import AsyncPath
from yarl import URL
from bs4 import BeautifulSoup

from webtoon_download.context import AppContext
from webtoon_download.metadata import Episode, EpisodePage

IMAGE_DOWNLOAD_CHUNK_SIZE = 1024 ** 2  # 1 MiB


async def get_episode_html(episode: Episode, context: AppContext) -> str:
    response = await context.session.get(episode.indirect_url)
    if not response.ok:
        raise Exception("response not ok")
    body = await response.text()
    return body


async def get_episode_soup(episode: Episode, context: AppContext) -> BeautifulSoup:
    html = await get_episode_html(episode, context)
    soup = BeautifulSoup(html)
    return soup


def extract_episode_pages(episode: Episode, episode_soup: BeautifulSoup) -> list[EpisodePage]:
    image_list_tag = episode_soup.find(id="_imageList")
    image_children = image_list_tag.find_all(name="img")

    return [
        EpisodePage(episode, page_index, URL(image_tag.attrs["data-url"]))
        for page_index, image_tag in enumerate(image_children, start=1)
    ]


async def download_page_image(page: EpisodePage, context: AppContext) -> EpisodePage:
    if page.path is not None and await page.path.exists():
        return page

    destination = context.ephemeral_dir / page.url.name
    query = dict(page.url.query)
    query.pop("type")
    page_image_url = page.url.with_query(query)
    response = await context.session.get(page_image_url, headers={"Referer": "https://www.webtoons.com"})
    if not response.ok:
        raise Exception("response not ok")

    async with destination.open(mode="wb") as destination_handle:
        async for chunk in response.content.iter_chunked(IMAGE_DOWNLOAD_CHUNK_SIZE):
            await destination_handle.write(chunk)

    return replace(page, path=destination)


async def download_episode(episode: Episode, context: AppContext) -> list[EpisodePage]:
    soup = await get_episode_soup(episode, context)
    pages = extract_episode_pages(episode, soup)
    async with asyncio.TaskGroup() as tg:
        page_download_tasks = [tg.create_task(download_page_image(image_url, context)) for image_url in pages]
    return [await image_task for image_task in page_download_tasks]
