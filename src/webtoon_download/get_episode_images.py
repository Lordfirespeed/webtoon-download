import tempfile

from aiopath import AsyncPath
from yarl import URL
from bs4 import BeautifulSoup

from webtoon_download.context import AppContext


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
