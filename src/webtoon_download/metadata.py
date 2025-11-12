from dataclasses import dataclass, field

from aiopath import AsyncPath
from yarl import URL


@dataclass(frozen=True)
class Series:
    title_no: int

    @property
    def indirect_url(self):
        return URL(f"https://www.webtoons.com/en/genre/series/list?title_no={self.title_no}")


@dataclass(frozen=True)
class Episode:
    series: Series
    index: int

    @property
    def indirect_url(self):
        return URL(f"https://www.webtoons.com/en/genre/series/episode/viewer?title_no={self.series.title_no}&episode_no={self.index}")


@dataclass(frozen=True)
class EpisodePage:
    episode: Episode
    index: int
    url: URL
    path: AsyncPath | None = field(default=None)
