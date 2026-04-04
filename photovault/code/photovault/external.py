import os
import shutil
from pathlib import Path


def _ensure_mounted(external_root: Path) -> None:
    if not external_root.exists():
        raise FileNotFoundError(
            f"External disk root not found: {external_root}. "
            "Ensure the drive is mounted before using --external."
        )


def copy_to_external(src: Path, external_root: Path, relative_path: str) -> Path:
    """Copy file to external disk preserving hierarchy. Returns dest path."""
    _ensure_mounted(external_root)
    dest = external_root / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def copy_from_external(external_root: Path, relative_path: str, dest: Path) -> Path:
    """Retrieve file from external disk to local dest."""
    _ensure_mounted(external_root)
    src = external_root / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def sync_catalog_to_external(catalog_path: Path, external_root: Path) -> None:
    """Copy catalog.json to external root."""
    _ensure_mounted(external_root)
    dest = external_root / "catalog.json"
    shutil.copy2(catalog_path, dest)
