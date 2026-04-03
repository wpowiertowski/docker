# Photo Vault

A CLI tool that catalogs batches of photos into a local JSON database, uploads them with byte-level redundancy files (PAR2) to Backblaze B2, and optionally mirrors to an external disk.

## Quick Start

```bash
make build

# Add a batch of photos
docker run --rm \
  -v ~/.photovault:/root/.photovault \
  -v /path/to/photos:/photos:ro \
  -e PHOTOVAULT_B2_KEY_ID=... \
  -e PHOTOVAULT_B2_APP_KEY=... \
  -e PHOTOVAULT_B2_BUCKET=my-vault \
  photovault add /photos --album "2026-04-03 Beach-Sunset"

# List catalog
docker run --rm -v ~/.photovault:/root/.photovault photovault list

# Retrieve photos
docker run --rm \
  -v ~/.photovault:/root/.photovault \
  -v ./retrieved:/retrieved \
  -e PHOTOVAULT_B2_KEY_ID=... \
  -e PHOTOVAULT_B2_APP_KEY=... \
  -e PHOTOVAULT_B2_BUCKET=my-vault \
  photovault retrieve --year 2026 --month 04 --day 03 --album Beach-Sunset --dest /retrieved
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PHOTOVAULT_B2_KEY_ID` | Yes | Backblaze B2 application key ID |
| `PHOTOVAULT_B2_APP_KEY` | Yes | Backblaze B2 application key |
| `PHOTOVAULT_B2_BUCKET` | Yes | B2 bucket name |
| `PHOTOVAULT_CATALOG_PATH` | No | Catalog path (default: `~/.photovault/catalog.json`) |
| `PHOTOVAULT_EXTERNAL_ROOT` | No | Default external disk mount point |
| `PHOTOVAULT_REDUNDANCY_PCT` | No | PAR2 redundancy percentage (default: `10`) |

## Commands

```
photovault add <source_folder> --album "YYYY-MM-DD Name" [--external /mnt/ext]
photovault retrieve --year YYYY [--month MM] [--day DD] [--album Name] --from b2|external --dest <dir>
photovault verify --year YYYY --month MM --day DD --album Name --from b2|external
photovault list [--year YYYY] [--month MM] [--day DD]
photovault repair <image_path> --par2 <par2_path>
```
