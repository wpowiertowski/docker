import os
from pathlib import Path

CATALOG_PATH = Path(
    os.environ.get("PHOTOVAULT_CATALOG_PATH", "~/.photovault/catalog.json")
).expanduser()

B2_KEY_ID = os.environ.get("PHOTOVAULT_B2_KEY_ID", "")
B2_APP_KEY = os.environ.get("PHOTOVAULT_B2_APP_KEY", "")
B2_BUCKET = os.environ.get("PHOTOVAULT_B2_BUCKET", "")

EXTERNAL_ROOT_STR = os.environ.get("PHOTOVAULT_EXTERNAL_ROOT", "")
EXTERNAL_ROOT = Path(EXTERNAL_ROOT_STR) if EXTERNAL_ROOT_STR else None

REDUNDANCY_PCT = int(os.environ.get("PHOTOVAULT_REDUNDANCY_PCT", "10"))

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw",
                    ".cr2", ".cr3", ".nef", ".arw", ".dng"}
