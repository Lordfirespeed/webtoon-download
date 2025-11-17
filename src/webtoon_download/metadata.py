from dataclasses import dataclass, field

from aiopath import AsyncPath
from bs4 import BeautifulSoup
from yarl import URL

from webtoon_download.context import AppContext


@dataclass
class Series:
    title_no: int
    title: str
    slug: str
    base_url: URL
    free_episode_count: int

    @property
    def list_url(self) -> URL:
        return (self.base_url / f"list").with_query({"title_no": self.title_no})

    @classmethod
    async def get_populated_series(cls, title_no: int, context: AppContext):
        indirect_url = URL(f"https://www.webtoons.com/en/genre/series/list?title_no={title_no}")
        response = await context.session.get(indirect_url)
        if not response.ok:
            raise Exception("response not ok")
        base_url = response.url.parent
        body = await response.text()
        soup = BeautifulSoup(body, features="html.parser")
        title_raw = soup.find("title").text
        title = title_raw[:title_raw.rindex("|")].strip()

        episode_list_tag = soup.find(name="ul", id="_listUl")
        most_recent_free_episode_tag = episode_list_tag.find()
        free_episode_count = int(most_recent_free_episode_tag.attrs["data-episode-no"])

        return cls(title_no=title_no, title=title, slug=base_url.name, base_url=base_url, free_episode_count=free_episode_count)


@dataclass
class Episode:
    series: Series
    index: int

    @property
    def indirect_url(self):
        # WEBTOON doesn't care about the path, as long as it contains the right number of fragments.
        # It uses the (series) title_no and episode_no query parameters to identify the episode, then redirects you to
        # the canonical URL for the viewer for that episode
        # (e.g. ``/en/romance/fae-trapped/ep-1-the-banished-fae/viewer?title_no=8904&episode_no=1``)
        return URL(f"https://www.webtoons.com/en/genre/series/episode/viewer?title_no={self.series.title_no}&episode_no={self.index}")


@dataclass
class EpisodePage:
    episode: Episode
    index: int
    url: URL
    path: AsyncPath | None = field(default=None)
