import os
import tomllib
from pathlib import Path

_CONFIG_FILE = Path(
    os.environ.get("PHOTOVAULT_CONFIG", "~/.photovault/config.toml")
).expanduser()

_file_cfg: dict = {}
if _CONFIG_FILE.exists():
    with _CONFIG_FILE.open("rb") as _f:
        _file_cfg = tomllib.load(_f)

_b2_cfg: dict = _file_cfg.get("b2", {})


def _get(env_var: str, file_val, default=""):
    """Env var > config file > default."""
    env = os.environ.get(env_var)
    if env is not None:
        return env
    if file_val is not None:
        return file_val
    return default


CATALOG_PATH = Path(
    _get("PHOTOVAULT_CATALOG_PATH", _file_cfg.get("catalog_path"), "~/.photovault/catalog.json")
).expanduser()

B2_KEY_ID = _get("PHOTOVAULT_B2_KEY_ID", _b2_cfg.get("key_id"))
B2_APP_KEY = _get("PHOTOVAULT_B2_APP_KEY", _b2_cfg.get("app_key"))
B2_BUCKET  = _get("PHOTOVAULT_B2_BUCKET",  _b2_cfg.get("bucket"))

_ext = _get("PHOTOVAULT_EXTERNAL_ROOT", _file_cfg.get("external_root"))
EXTERNAL_ROOT = Path(_ext) if _ext else None

REDUNDANCY_PCT = int(_get("PHOTOVAULT_REDUNDANCY_PCT", _file_cfg.get("redundancy_pct"), "10"))

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw",
                    ".cr2", ".cr3", ".nef", ".arw", ".dng"}
