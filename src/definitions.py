from aiopath import AsyncPath

source_root_dir: AsyncPath = AsyncPath(__file__).parent  # <repo>/src/
project_root_dir: AsyncPath = source_root_dir.parent  # <repo>/
