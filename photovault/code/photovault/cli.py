import re
import sys
from pathlib import Path
from typing import Optional

import click
from tqdm import tqdm

from photovault import config
from photovault.b2_client import B2Client
from photovault.catalog import (
    add_album_entry,
    load_catalog,
    query_albums,
    save_catalog,
)
from photovault.external import (
    copy_from_external,
    copy_to_external,
    sync_catalog_to_external,
)
from photovault.hasher import sha256_file
from photovault.models import ImageEntry
from photovault.redundancy import generate_par2, repair_with_par2, verify_with_par2

ALBUM_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2}) (.+)$")


def parse_album(album_str: str) -> tuple[str, str, str, str]:
    m = ALBUM_RE.match(album_str)
    if not m:
        raise click.BadParameter(
            f"Album must match 'YYYY-MM-DD Album-Name', got: {album_str!r}"
        )
    return m.group(1), m.group(2), m.group(3), m.group(4)


def discover_images(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in config.IMAGE_EXTENSIONS
    )


def _b2_client() -> B2Client:
    if not config.B2_KEY_ID or not config.B2_APP_KEY or not config.B2_BUCKET:
        raise click.UsageError(
            "B2 credentials not configured. Set PHOTOVAULT_B2_KEY_ID, "
            "PHOTOVAULT_B2_APP_KEY, and PHOTOVAULT_B2_BUCKET."
        )
    return B2Client(config.B2_KEY_ID, config.B2_APP_KEY, config.B2_BUCKET)


@click.group()
def cli() -> None:
    """Photo Vault — image catalog and backup system."""


@cli.command()
@click.argument("source_folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--album", required=True, help="Album string: 'YYYY-MM-DD Album-Name'")
@click.option("--external", type=click.Path(path_type=Path), default=None,
              help="External disk root path")
def add(source_folder: Path, album: str, external: Optional[Path]) -> None:
    """Catalog and upload a batch of photos."""
    year, month, day, album_name = parse_album(album)
    external_root = external or config.EXTERNAL_ROOT

    catalog = load_catalog(config.CATALOG_PATH)
    images = discover_images(source_folder)
    if not images:
        click.echo(f"No images found in {source_folder}")
        sys.exit(1)

    b2 = _b2_client()
    entries: list[ImageEntry] = []

    for img in tqdm(images, desc="Processing", unit="file"):
        sha = sha256_file(img)
        par2_path = generate_par2(img, config.REDUNDANCY_PCT)

        b2_rel = f"photos/{year}/{month}/{day}/{album_name}/{img.name}"
        b2_file_id = b2.upload_file(img, b2_rel)
        b2_par2_id = b2.upload_file(par2_path, b2_rel + ".par2")

        ext_path = None
        if external_root:
            ext_path = copy_to_external(img, external_root, b2_rel)
            copy_to_external(par2_path, external_root, b2_rel + ".par2")

        entries.append(ImageEntry(
            filename=img.name,
            sha256=sha,
            size_bytes=img.stat().st_size,
            par2_filename=par2_path.name,
            b2_file_id=b2_file_id,
            b2_par2_file_id=b2_par2_id,
            external_path=str(ext_path) if ext_path else None,
        ))

    add_album_entry(catalog, year, month, day, album_name, entries)
    save_catalog(catalog, config.CATALOG_PATH)

    b2.upload_file(config.CATALOG_PATH, "catalog.json")
    if external_root:
        sync_catalog_to_external(config.CATALOG_PATH, external_root)

    click.echo(f"Added {len(entries)} image(s) to album '{album_name}' ({year}-{month}-{day})")


@cli.command()
@click.option("--year", required=True)
@click.option("--month", default=None)
@click.option("--day", default=None)
@click.option("--album", default=None)
@click.option("--from", "source", type=click.Choice(["b2", "external"]), default="b2")
@click.option("--dest", type=click.Path(path_type=Path), default=Path("./retrieved"))
@click.option("--external", type=click.Path(path_type=Path), default=None)
def retrieve(
    year: str,
    month: Optional[str],
    day: Optional[str],
    album: Optional[str],
    source: str,
    dest: Path,
    external: Optional[Path],
) -> None:
    """Download photos from B2 or external disk."""
    external_root = external or config.EXTERNAL_ROOT
    catalog = load_catalog(config.CATALOG_PATH)
    albums = query_albums(catalog, year, month, day, album)

    if not albums:
        click.echo("No albums matched the given filters.")
        sys.exit(1)

    b2 = _b2_client() if source == "b2" else None

    for ar in albums:
        for img_entry in tqdm(ar.images, desc=f"{ar.album_name}", unit="file"):
            rel = (
                f"photos/{ar.year}/{ar.month}/{ar.day}"
                f"/{ar.album_name}/{img_entry.filename}"
            )
            local_dest = dest / rel
            par2_dest = local_dest.with_suffix(local_dest.suffix + ".par2")

            if source == "b2":
                b2.download_file(rel, local_dest)
                b2.download_file(rel + ".par2", par2_dest)
            else:
                if not external_root:
                    raise click.UsageError("--external required when --from external")
                copy_from_external(external_root, rel, local_dest)
                copy_from_external(external_root, rel + ".par2", par2_dest)

            actual_sha = sha256_file(local_dest)
            if actual_sha != img_entry.sha256:
                click.echo(f"CORRUPTION DETECTED: {img_entry.filename}")
                repaired = repair_with_par2(local_dest, par2_dest)
                if repaired:
                    click.echo(f"  Repaired: {img_entry.filename}")
                else:
                    click.echo(f"  REPAIR FAILED: {img_entry.filename} — try other source")

    click.echo(f"Retrieved to {dest}")


@cli.command()
@click.option("--year", required=True)
@click.option("--month", required=True)
@click.option("--day", required=True)
@click.option("--album", required=True)
@click.option("--from", "source", type=click.Choice(["b2", "external"]), default="b2")
@click.option("--external", type=click.Path(path_type=Path), default=None)
def verify(
    year: str,
    month: str,
    day: str,
    album: str,
    source: str,
    external: Optional[Path],
) -> None:
    """Verify integrity of stored photos."""
    external_root = external or config.EXTERNAL_ROOT
    catalog = load_catalog(config.CATALOG_PATH)
    albums = query_albums(catalog, year, month, day, album)

    if not albums:
        click.echo("Album not found in catalog.")
        sys.exit(1)

    b2 = _b2_client() if source == "b2" else None
    tmp_dir = config.CATALOG_PATH.parent / "tmp_verify"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ok = True

    for ar in albums:
        for img_entry in tqdm(ar.images, desc=f"Verifying {ar.album_name}", unit="file"):
            rel = (
                f"photos/{ar.year}/{ar.month}/{ar.day}"
                f"/{ar.album_name}/{img_entry.filename}"
            )
            tmp_img = tmp_dir / img_entry.filename
            tmp_par2 = tmp_dir / img_entry.par2_filename

            if source == "b2":
                b2.download_file(rel, tmp_img)
                b2.download_file(rel + ".par2", tmp_par2)
            else:
                if not external_root:
                    raise click.UsageError("--external required when --from external")
                copy_from_external(external_root, rel, tmp_img)
                copy_from_external(external_root, rel + ".par2", tmp_par2)

            actual_sha = sha256_file(tmp_img)
            if actual_sha != img_entry.sha256:
                click.echo(f"  FAIL (SHA mismatch): {img_entry.filename}")
                ok = False
            elif not verify_with_par2(tmp_img, tmp_par2):
                click.echo(f"  FAIL (PAR2 mismatch): {img_entry.filename}")
                ok = False
            else:
                click.echo(f"  OK: {img_entry.filename}")

            tmp_img.unlink(missing_ok=True)
            tmp_par2.unlink(missing_ok=True)

    tmp_dir.rmdir()
    sys.exit(0 if ok else 1)


@cli.command("list")
@click.option("--year", default=None)
@click.option("--month", default=None)
@click.option("--day", default=None)
def list_albums(
    year: Optional[str],
    month: Optional[str],
    day: Optional[str],
) -> None:
    """List albums in the catalog."""
    catalog = load_catalog(config.CATALOG_PATH)
    albums = query_albums(catalog, year, month, day)

    if not albums:
        click.echo("No albums found.")
        return

    for ar in albums:
        click.echo(
            f"{ar.year}-{ar.month}-{ar.day}  {ar.album_name}"
            f"  ({len(ar.images)} image(s))  added: {ar.added_at}"
        )


@cli.command()
@click.argument("image_path", type=click.Path(exists=True, path_type=Path))
@click.option("--par2", "par2_path", required=True,
              type=click.Path(exists=True, path_type=Path))
def repair(image_path: Path, par2_path: Path) -> None:
    """Repair a corrupted local image using its par2 file."""
    if repair_with_par2(image_path, par2_path):
        click.echo(f"Repaired: {image_path}")
    else:
        click.echo(f"Repair failed: {image_path}")
        sys.exit(1)


def main() -> None:
    cli()
