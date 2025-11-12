import asyncio
import tempfile

from aiopath import AsyncPath
from yarl import URL
from bs4 import BeautifulSoup

from webtoon_download.context import AppContext


IMAGE_DOWNLOAD_CHUNK_SIZE = 1024 ** 2  # 1 MiB


async def get_episode_html(episode_url: URL, context: AppContext) -> str:
    response = await context.session.get(episode_url)
    if not response.ok:
        raise Exception("response not ok")
    body = await response.text()
    return body


async def get_episode_soup(episode_url: URL, context: AppContext) -> BeautifulSoup:
    html = await get_episode_html(episode_url, context)
    soup = BeautifulSoup(html)
    return soup


def extract_episode_page_image_urls(episode_soup: BeautifulSoup) -> list[URL]:
    image_list_tag = episode_soup.find(id="_imageList")
    image_children = image_list_tag.find_all(name="img")
    return [URL(image_tag.attrs["data-url"]) for image_tag in image_children]


async def get_page_image(page_image_url: URL, context: AppContext) -> AsyncPath:
    destination = context.ephemeral_dir / page_image_url.name
    query = dict(page_image_url.query)
    query.pop("type")
    page_image_url = page_image_url.with_query(query)
    response = await context.session.get(page_image_url, headers={"Referer": "https://www.webtoons.com"})
    if not response.ok:
        raise Exception("response not ok")

    async with destination.open(mode="wb") as destination_handle:
        async for chunk in response.content.iter_chunked(IMAGE_DOWNLOAD_CHUNK_SIZE):
            await destination_handle.write(chunk)

    return destination


async def get_episode_page_images(episode_url: URL, context: AppContext) -> list[AsyncPath]:
    soup = await get_episode_soup(episode_url, context)
    image_urls = extract_episode_page_image_urls(soup)
    async with asyncio.TaskGroup() as tg:
        image_tasks = [tg.create_task(get_page_image(image_url, context)) for image_url in image_urls]
    return [await image_task for image_task in image_tasks]
