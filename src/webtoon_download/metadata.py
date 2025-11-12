from dataclasses import dataclass, field

from aiopath import AsyncPath
from yarl import URL


@dataclass
class Series:
    title_no: int
    title: str | None = field(default=None)
    slug: str | None = field(default=None)

    @property
    def indirect_url(self):
        return URL(f"https://www.webtoons.com/en/genre/series/list?title_no={self.title_no}")


@dataclass
class Episode:
    series: Series
    index: int

    @property
    def indirect_url(self):
        return URL(f"https://www.webtoons.com/en/genre/series/episode/viewer?title_no={self.series.title_no}&episode_no={self.index}")


@dataclass
class EpisodePage:
    episode: Episode
    index: int
    url: URL
    path: AsyncPath | None = field(default=None)
