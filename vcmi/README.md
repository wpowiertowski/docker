# VCMI Docker Setup

Docker image that runs [VCMI](https://github.com/vcmi/vcmi) (an open-source reimplementation of the Heroes of Might and Magic III game engine) on ARM64 architecture with a web-based GUI interface using noVNC.

## Features

- 🎮 Full VCMI game engine built from the latest develop branch
- 🌐 Web-based GUI access via noVNC (no VNC client needed)
- 🖥️ Virtual framebuffer (Xvfb) for headless operation
- 🪟 Lightweight Openbox window manager
- 📦 Multi-stage Docker build for optimal image size
- 🔒 Non-root user for security
- 📊 Supervisor for process management
- 💾 Persistent volume for game data

## Prerequisites

- Docker installed on your system (ARM64 architecture)
- Heroes of Might and Magic III game data files (required to play)

## Quick Start

### Build the Docker Image

```bash
# For ARM64 architecture
docker build -t vcmi:latest .
```

**Note:** The build process may take 15-30 minutes as it compiles VCMI from source with all dependencies.

### Run the Container

```bash
docker run -d \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  --name vcmi \
  vcmi:latest
```

### Access the Web GUI

1. Open your web browser
2. Navigate to: `http://localhost:6080`
3. You should see the VCMI launcher interface

## Detailed Setup

### 1. Prepare Game Data

VCMI requires the original Heroes of Might and Magic III game data files to run. You need to:

1. Create a local directory for VCMI data:
   ```bash
   mkdir -p vcmi-data
   ```

2. Copy your Heroes III game data into this directory. The expected structure is:
   ```
   vcmi-data/
   ├── Data/          # Game data files (*.lod, *.vid, *.snd)
   ├── Maps/          # Game maps (*.h3m)
   ├── Mp3/           # Music files (optional)
   └── config/        # VCMI configuration
   ```

3. Alternatively, you can use the VCMI launcher to download and configure the game data through the web interface.

### 2. Build Options

The Dockerfile uses a multi-stage build with the following components:

**Build Stage:**
- Base: Ubuntu 24.04
- Installs all development dependencies
- Clones VCMI from the `develop` branch
- Compiles with CMake in Release mode
- Installs to `/opt/vcmi`

**Runtime Stage:**
- Base: Ubuntu 24.04
- Installs only runtime libraries (no development packages)
- Sets up noVNC + Xvfb + x11vnc + openbox
- Configures supervisor for process management
- Creates non-root `vcmi` user

### 3. Run Options

#### Basic Run

```bash
docker run -d \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  --name vcmi \
  vcmi:latest
```

#### With Custom Display Resolution

You can modify the Xvfb resolution by overriding the supervisor configuration:

```bash
docker run -d \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  -e DISPLAY_WIDTH=1920 \
  -e DISPLAY_HEIGHT=1080 \
  --name vcmi \
  vcmi:latest
```

#### Interactive Mode for Debugging

```bash
docker run -it --rm \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  vcmi:latest
```

### 4. Managing the Container

```bash
# View logs
docker logs vcmi

# Stop the container
docker stop vcmi

# Start the container
docker start vcmi

# Remove the container
docker rm vcmi

# Execute commands inside the container
docker exec -it vcmi bash
```

### 5. Starting the VCMI Launcher

The container starts all services automatically (Xvfb, openbox, x11vnc, noVNC). To start the VCMI launcher:

```bash
# Access the container
docker exec -it vcmi bash

# Start the launcher via supervisor
supervisorctl start vcmilauncher
```

Alternatively, access the web GUI and start the launcher from a terminal in the Openbox session.

## Architecture

### Services Managed by Supervisor

1. **Xvfb** (Priority 10)
   - Virtual framebuffer running on display :99
   - Resolution: 1280x720x24
   - Provides the display server for GUI applications

2. **Openbox** (Priority 20)
   - Lightweight window manager
   - Runs as the `vcmi` user
   - Manages application windows

3. **x11vnc** (Priority 30)
   - VNC server exposing the Xvfb display
   - Listens on port 5900 (internal)
   - No password authentication (secured by Docker networking)

4. **noVNC** (Priority 40)
   - Web-based VNC client
   - Listens on port 6080 (exposed)
   - Provides browser-based access to the GUI

5. **vcmilauncher** (Priority 50)
   - VCMI launcher application
   - Disabled by default (start manually)
   - Runs as the `vcmi` user

### Directory Structure

```
/opt/vcmi/              # VCMI installation
├── bin/                # Binaries (vcmiclient, vcmiserver, vcmilauncher)
├── lib/                # Shared libraries
└── share/              # Data files

/home/vcmi/             # VCMI user home directory
└── .local/share/vcmi/  # VCMI data directory (volume mount point)
    ├── config/         # Configuration files
    ├── Games/          # Saved games
    ├── Mods/           # Mods and additional content
    ├── Data/           # Heroes III game data (copy here)
    └── Maps/           # Maps (copy here)
```

## Troubleshooting

### Cannot Access Web GUI

1. Check if the container is running:
   ```bash
   docker ps | grep vcmi
   ```

2. Check container logs:
   ```bash
   docker logs vcmi
   ```

3. Verify port mapping:
   ```bash
   docker port vcmi
   ```

### Game Data Not Found

1. Ensure game data is in the correct location:
   ```bash
   docker exec vcmi ls -la /home/vcmi/.local/share/vcmi
   ```

2. Check file permissions:
   ```bash
   docker exec vcmi ls -la /home/vcmi/.local/share/vcmi/Data
   ```

3. The VCMI launcher can help you set up game data. Access it through the web GUI.

### Performance Issues

1. **Increase Docker resources**: Ensure Docker has sufficient CPU and memory allocated
2. **Use local volumes**: Bind mounts may be slower than named volumes
3. **Check ARM64 optimization**: VCMI is built natively for ARM64 in this container

### Display Issues

1. Check Xvfb logs:
   ```bash
   docker exec vcmi cat /var/log/supervisor/xvfb.log
   ```

2. Check x11vnc logs:
   ```bash
   docker exec vcmi cat /var/log/supervisor/x11vnc.log
   ```

3. Restart display services:
   ```bash
   docker exec vcmi supervisorctl restart xvfb
   docker exec vcmi supervisorctl restart x11vnc
   ```

## Advanced Configuration

### Custom Supervisor Configuration

You can mount a custom supervisor configuration:

```bash
docker run -d \
  -p 6080:6080 \
  -v $(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
  -v $(pwd)/supervisord.conf:/etc/supervisor/conf.d/supervisord.conf \
  --name vcmi \
  vcmi:latest
```

### Environment Variables

The container respects the following environment variables:

- `DISPLAY`: X11 display (default: `:99`)
- `XDG_RUNTIME_DIR`: Runtime directory for user services
- `PATH`: Includes `/opt/vcmi/bin`
- `LD_LIBRARY_PATH`: Includes `/opt/vcmi/lib`

### Building for Different Architectures

While this Dockerfile is optimized for ARM64, it should work on AMD64 as well:

```bash
# For AMD64
docker build --platform linux/amd64 -t vcmi:amd64 .

# For ARM64
docker build --platform linux/arm64 -t vcmi:arm64 .
```

## Technical Details

### VCMI Version

This container builds VCMI from the `develop` branch, which includes the latest features and fixes. The build is performed during Docker image creation.

### Dependencies

**Build Dependencies:**
- CMake, g++, clang
- SDL2 (mixer, image, ttf)
- Boost (filesystem, system, thread, program-options, locale, date-time, atomic)
- libavformat, libswscale (FFmpeg)
- minizip, zlib, tbb, fuzzylite
- Qt5 (base, network)
- LuaJIT, onnxruntime

**Runtime Dependencies:**
- SDL2 runtime libraries
- Boost runtime libraries
- FFmpeg runtime libraries
- Qt5 runtime libraries
- X11 and GUI components (Xvfb, x11vnc, openbox)
- noVNC + websockify

### Image Size Optimization

The multi-stage build ensures:
- Development tools and headers are not included in the final image
- Only runtime libraries are installed in the final stage
- Build artifacts from the builder stage are copied selectively
- Temporary files and caches are cleaned up

## Security Considerations

- Container runs services as the non-root `vcmi` user where possible
- x11vnc has no password (secured by Docker port mapping)
- Game data is stored in a volume for persistence
- No sensitive data should be stored in the container image

## License

VCMI is licensed under GPL v2. See the [VCMI repository](https://github.com/vcmi/vcmi) for details.

This Dockerfile and documentation are provided as-is for educational and hobbyist purposes.

## References

- [VCMI Project](https://github.com/vcmi/vcmi)
- [VCMI Building on Linux](https://github.com/vcmi/vcmi/blob/develop/docs/developers/Building_Linux.md)
- [noVNC](https://github.com/novnc/noVNC)
- [Heroes of Might and Magic III](https://www.gog.com/game/heroes_of_might_and_magic_3_complete_edition)

## Contributing

Feel free to open issues or submit pull requests for improvements to this Docker setup.
