from aiopath import AsyncPath

from definitions import project_root_dir

config_root_dir: AsyncPath = project_root_dir/"config"
series_config_dir: AsyncPath = config_root_dir/"series"
