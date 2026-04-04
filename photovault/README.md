# Photo Vault

A CLI tool that catalogs batches of photos into a local JSON database, uploads them with byte-level redundancy files (PAR2) to Backblaze B2, and optionally mirrors to an external disk.

## Quick Start

```bash
make build

# First run bootstraps ~/.photovault/config.toml from the example — fill in your B2 credentials, then:
make run

# Or invoke commands directly (config is picked up automatically)
docker run --rm \
  -v ~/.photovault:/root/.photovault \
  -v /path/to/photos:/photos \
  -v /Volumes/MyDisk:/Volumes/MyDisk \
  photovault add /photos --album "2026-04-03 Beach-Sunset"

docker run --rm -v ~/.photovault:/root/.photovault photovault list

docker run --rm \
  -v ~/.photovault:/root/.photovault \
  -v ./retrieved:/retrieved \
  photovault retrieve --year 2026 --month 04 --day 03 --album Beach-Sunset --dest /retrieved
```

## Configuration

Settings live in `~/.photovault/config.toml`. Running `make run` or `make shell` will create the file from `config.toml.example` automatically if it doesn't exist yet.

```toml
catalog_path   = "~/.photovault/catalog.json"
external_root  = "/Volumes/MyDisk"
redundancy_pct = 10

[b2]
key_id  = "your-key-id"
app_key = "your-app-key"
bucket  = "your-bucket"
```

The config directory can be changed with `CONFIG_DIR`:

```bash
make run CONFIG_DIR=/mnt/nas/photovault
```

Environment variables always take precedence over the config file and can be used to override individual values. The config file location itself can be changed with `PHOTOVAULT_CONFIG`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PHOTOVAULT_CONFIG` | `~/.photovault/config.toml` | Path to the config file |
| `PHOTOVAULT_B2_KEY_ID` | — | Backblaze B2 application key ID |
| `PHOTOVAULT_B2_APP_KEY` | — | Backblaze B2 application key |
| `PHOTOVAULT_B2_BUCKET` | — | B2 bucket name |
| `PHOTOVAULT_CATALOG_PATH` | `~/.photovault/catalog.json` | Catalog file path |
| `PHOTOVAULT_EXTERNAL_ROOT` | — | Default external disk mount point |
| `PHOTOVAULT_REDUNDANCY_PCT` | `10` | PAR2 redundancy percentage |

## Commands

```
photovault add <source_folder> --album "YYYY-MM-DD Name" [--external /mnt/ext]
photovault retrieve --year YYYY [--month MM] [--day DD] [--album Name] --from b2|external --dest <dir>
photovault verify --year YYYY --month MM --day DD --album Name --from b2|external
photovault list [--year YYYY] [--month MM] [--day DD]
photovault repair <image_path> --par2 <par2_path>
```
