import asyncio

from aiopath import AsyncPath
from yarl import URL

from webtoon_download.context import AppContext
from webtoon_download.metadata import Episode, EpisodePage

IMAGE_DOWNLOAD_CHUNK_SIZE = 1024 ** 2  # 1 MiB


def scrape_episode_pages(episode: Episode) -> list[EpisodePage]:
    image_list_tag = episode.viewer_soup.find(id="_imageList")
    image_children = image_list_tag.find_all(name="img")

    return [
        EpisodePage.of(episode, page_index, URL(image_tag.attrs["data-url"]))
        for page_index, image_tag in enumerate(image_children, start=1)
    ]


async def download_page_image(page: EpisodePage, destination_dir: AsyncPath, context: AppContext) -> EpisodePage:
    if page.path is not None and await page.path.exists():
        return page

    assert page.episode.series.slug

    destination_file = destination_dir / f"{page.episode.series.slug}-ep{page.episode.episode_index:03}-page{page.page_index:03}{page.url.suffix}"
    query = dict(page.url.query)
    query.pop("type")
    page_image_url = page.url.with_query(query)
    response = await context.session.get(page_image_url, headers={"Referer": "https://www.webtoons.com"})
    if not response.ok:
        raise Exception("response not ok")

    async with destination_file.open(mode="wb") as destination_handle:
        async for chunk in response.content.iter_chunked(IMAGE_DOWNLOAD_CHUNK_SIZE):
            await destination_handle.write(chunk)

    page.path = destination_file
    return page


async def download_episode(episode: Episode, destination: AsyncPath, context: AppContext) -> list[EpisodePage]:
    extracted_pages = scrape_episode_pages(episode)

    await destination.mkdir(parents=True)  # if the destination directory already exists, this will throw (intended)

    page_download_tasks = [asyncio.create_task(download_page_image(image_url, destination, context)) for image_url in extracted_pages]
    pages = []
    async for page_download_task in asyncio.as_completed(page_download_tasks):
        page = await page_download_task
        print(f"downloaded page {page.page_index}")
        pages.append(page)

    return pages
