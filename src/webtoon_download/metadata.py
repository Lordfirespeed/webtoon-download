from dataclasses import dataclass, field
from functools import cached_property
from typing import ClassVar, Self

from aiopath import AsyncPath
from bs4 import BeautifulSoup
from yarl import URL

from webtoon_download.context import AppContext


@dataclass(frozen=True)
class SeriesIdentifier:
    title_no: int

    @property
    def indirect_url(self):
        return URL(f"https://www.webtoons.com/en/genre/series/list?title_no={self.title_no}")


@dataclass
class Series:
    _instance_cache: ClassVar[dict[SeriesIdentifier, Self]] = {}

    title_no: int
    base_url: URL
    list_soup: BeautifulSoup

    @property
    def list_url(self) -> URL:
        return (self.base_url / f"list").with_query({"title_no": self.title_no})

    @cached_property
    def title(self) -> str:
        title_raw = self.list_soup.find("title").text
        title = title_raw[:title_raw.rindex("|")].strip()
        return title

    @cached_property
    def slug(self) -> str:
        return self.base_url.name

    @cached_property
    def free_episode_count(self) -> int:
        episode_list_tag = self.list_soup.find(name="ul", id="_listUl")
        most_recent_free_episode_tag = episode_list_tag.find()
        return int(most_recent_free_episode_tag.attrs["data-episode-no"])

    @classmethod
    async def fetch_populated_series(cls, series_id: SeriesIdentifier, context: AppContext) -> Self:
        response = await context.session.get(series_id.indirect_url)
        if not response.ok:
            raise Exception("response not ok")
        body = await response.text()
        soup = BeautifulSoup(body, features="html.parser")
        return cls.make_cached(series_id, response.url, soup)

    @classmethod
    def make_cached(cls, series_id: SeriesIdentifier, list_url: URL, list_soup: BeautifulSoup) -> Self:
        base_url = list_url.parent

        series = cls(
            title_no=series_id.title_no,
            base_url=base_url,
            list_soup=list_soup,
        )
        cls._instance_cache[series_id] = series
        return series

    @classmethod
    def get_cached(cls, series_id: SeriesIdentifier) -> Self:
        return cls._instance_cache[series_id]


@dataclass(frozen=True, slots=True)
class EpisodeIdentifier:
    series_title_no: int
    episode_index: int

    @property
    def indirect_url(self):
        # WEBTOON doesn't care about the path, as long as it contains the right number of fragments.
        # It uses the (series) title_no and episode_no query parameters to identify the episode, then redirects you to
        # the canonical URL for the viewer for that episode
        # (e.g. ``/en/romance/fae-trapped/ep-1-the-banished-fae/viewer?title_no=8904&episode_no=1``)
        return URL(f"https://www.webtoons.com/en/genre/series/episode/viewer?title_no={self.series_title_no}&episode_no={self.episode_index}")

    @classmethod
    def of(cls, series: Series | SeriesIdentifier, with_episode_index: int) -> Self:
        return cls(series.title_no, with_episode_index)


@dataclass
class Episode:
    _instance_cache: ClassVar[dict[EpisodeIdentifier, Self]] = {}

    series_title_no: int
    episode_index: int
    base_url: URL
    viewer_soup: BeautifulSoup

    @property
    def viewer_url(self) -> URL:
        return (self.base_url / f"viewer").with_query({"title_no": self.series_title_no, "episode_no": self.episode_index})

    @property
    def series(self):
        return Series.get_cached(SeriesIdentifier(self.series_title_no))

    @cached_property
    def title(self) -> str:
        title_raw = self.viewer_soup.find("title").text
        title = title_raw[:title_raw.rindex("|")].strip()
        return title

    @cached_property
    def webtoon_slug(self) -> str:
        return self.base_url.name

    @property
    def slug(self) -> str:
        return f"ep{self.episode_index:03}"

    @classmethod
    async def fetch_populated_episode(cls, episode_id: EpisodeIdentifier, context: AppContext) -> Self:
        response = await context.session.get(episode_id.indirect_url)
        if not response.ok:
            raise Exception("response not ok")
        body = await response.text()
        soup = BeautifulSoup(body, features="html.parser")
        return cls.make_cached(episode_id, response.url, soup)

    @classmethod
    def make_cached(cls, episode_id: EpisodeIdentifier, viewer_url: URL, viewer_soup: BeautifulSoup) -> Self:
        base_url = viewer_url.parent

        episode = cls(
            series_title_no=episode_id.series_title_no,
            episode_index=episode_id.episode_index,
            base_url=base_url,
            viewer_soup=viewer_soup,
        )
        cls._instance_cache[episode_id] = episode
        return episode

    @classmethod
    def get_cached(cls, episode_id: EpisodeIdentifier) -> Self:
        return cls._instance_cache[episode_id]


@dataclass
class EpisodePage:
    series_title_no: int
    episode_index: int
    page_index: int
    url: URL
    path: AsyncPath | None = field(default=None)

    @classmethod
    def of(cls, episode: Episode | EpisodeIdentifier, with_page_index: int, with_url: URL) -> Self:
        return cls(episode.series_title_no, episode.episode_index, with_page_index, with_url)

    @property
    def episode(self):
        return Episode.get_cached(EpisodeIdentifier(self.series_title_no, self.episode_index))
