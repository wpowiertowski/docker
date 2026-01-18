# VCMI Docker Quick Start Guide

This is a quick reference for getting VCMI up and running in Docker.

## Prerequisites
- Docker installed
- 2-4GB RAM available
- Heroes of Might and Magic III game data files

## Build & Run (3 commands)

```bash
# 1. Navigate to the vcmi directory
cd vcmi

# 2. Build the image (takes 15-30 minutes)
make build

# 3. Run the container
make run
```

## Access the GUI
Open your browser and go to: **http://localhost:6080**

## Add Game Data
```bash
# Copy your Heroes III game files to:
./vcmi-data/Data/    # Place .lod, .vid, .snd files here
./vcmi-data/Maps/    # Place .h3m map files here
```

## Common Commands

```bash
make stop            # Stop the container
make start-game      # Launch VCMI in the GUI
make logs            # View container logs
make shell           # Open shell in container
make clean           # Stop and remove container
```

## Using Docker Compose

```bash
docker compose up -d        # Start services
docker compose down         # Stop services
docker compose logs -f      # View logs
```

## Using Docker Directly

```bash
# Build
docker build -t vcmi:latest .

# Run
docker run -d \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  --name vcmi \
  vcmi:latest

# Access at http://localhost:6080
```

## Troubleshooting

**Container won't start?**
```bash
docker logs vcmi
```

**Need to restart services?**
```bash
docker exec vcmi supervisorctl restart all
```

**Game data not found?**
- Ensure files are in `./vcmi-data/Data/`
- Check permissions: `docker exec vcmi ls -la /home/vcmi/.local/share/vcmi`

## Architecture Notes
- Optimized for ARM64 (Apple Silicon, Raspberry Pi)
- Works on AMD64/x86_64 as well
- Uses multi-stage build for smaller image size

## More Information
See the full [README.md](README.md) for detailed documentation.
