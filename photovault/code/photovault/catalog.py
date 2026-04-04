import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from photovault.models import AlbumResult, ImageEntry


def load_catalog(path: Path) -> dict:
    """Load or initialise empty catalog."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {
        "version": 1,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "years": {},
    }


def save_catalog(catalog: dict, path: Path) -> None:
    """Atomic write (write tmp + rename)."""
    catalog["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(catalog, f, indent=2)
    os.replace(tmp, path)


def add_album_entry(
    catalog: dict,
    year: str,
    month: str,
    day: str,
    album_name: str,
    images: list[ImageEntry],
) -> None:
    """Insert album into hierarchy, creating intermediate keys if absent."""
    years = catalog.setdefault("years", {})
    months = years.setdefault(year, {}).setdefault("months", {})
    days = months.setdefault(month, {}).setdefault("days", {})
    albums = days.setdefault(day, {}).setdefault("albums", {})

    albums[album_name] = {
        "added_at": datetime.now(timezone.utc).isoformat(),
        "images": [img.to_dict() for img in images],
    }


def query_albums(
    catalog: dict,
    year: Optional[str] = None,
    month: Optional[str] = None,
    day: Optional[str] = None,
    album: Optional[str] = None,
) -> list[AlbumResult]:
    """Filter catalog by date components; return matching albums."""
    results = []
    years_data = catalog.get("years", {})
    year_keys = [year] if year else list(years_data.keys())

    for y in year_keys:
        if y not in years_data:
            continue
        months_data = years_data[y].get("months", {})
        month_keys = [month] if month else list(months_data.keys())

        for m in month_keys:
            if m not in months_data:
                continue
            days_data = months_data[m].get("days", {})
            day_keys = [day] if day else list(days_data.keys())

            for d in day_keys:
                if d not in days_data:
                    continue
                albums_data = days_data[d].get("albums", {})
                album_keys = [album] if album else list(albums_data.keys())

                for name in album_keys:
                    if name not in albums_data:
                        continue
                    album_data = albums_data[name]
                    images = [
                        ImageEntry.from_dict(img)
                        for img in album_data.get("images", [])
                    ]
                    results.append(
                        AlbumResult(
                            year=y,
                            month=m,
                            day=d,
                            album_name=name,
                            added_at=album_data.get("added_at", ""),
                            images=images,
                        )
                    )
    return results
