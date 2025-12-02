# Batocera Xbox Emulator Launcher

This project adds support for running Cxbx-Reloaded (Windows version via Wine) on Batocera Linux.

## Features

- **Cxbx-Reloaded**: Xbox emulator running via Wine
- **xemu**: Native Linux Xbox emulator (uses existing Batocera support)
- **xemu-wine**: Windows version of xemu via Wine (planned)

## Installation

1. Copy this project to your Batocera system:
   ```bash
   scp -r batocera-cxbxr root@batocera:/userdata/
   ```

2. SSH into Batocera and run the installation script:
   ```bash
   ssh root@batocera
   cd /userdata/batocera-cxbxr
   bash install.sh
   ```

3. Restart EmulationStation:
   ```bash
   batocera-es-swissknife --restart
   ```

## Directory Structure

```
/userdata/system/xbox-extra/
├── configgen/                  # Launcher scripts
│   ├── xboxlauncher.py        # Main launcher
│   ├── configgen-defaults.yml # Default configuration
│   └── generators/            # Emulator generators
│       ├── GeneratorImporter.py
│       ├── Generator.py
│       └── cxbxr/
│           └── cxbxrGenerator.py
├── cxbx-r/
│   └── app/                   # Cxbx-Reloaded executable
│       ├── cxbxr.exe
│       └── settings.ini       # Configuration file
└── xemu-wine/
    └── app/                   # xemu Windows build (future)
```

## Configuration

Configuration options can be set in `/userdata/system/batocera.conf`:

### Cxbx-Reloaded Options

```ini
# Video
xbox.cxbxr_fullscreen=true
xbox.cxbxr_vsync=false
xbox.cxbxr_aspect=true
xbox.cxbxr_render_scale=1     # 1-4, higher = better quality but slower
xbox.cxbxr_resolution=1920x1080

# Debug
xbox.cxbxr_debug=false
xbox.cxbxr_lle_gpu=false      # Low-level emulation for GPU (more accurate)
```

### Per-Game Configuration

You can set options per-game by using the ROM filename:

```ini
# For game "Halo.xbe"
xbox["Halo.xbe"].cxbxr_render_scale=2
xbox["Halo.xbe"].cxbxr_vsync=true
```

## Supported ROM Formats

- `.xbe` - Xbox executable files
- `.iso` - Xbox disc images
- `.squashfs` - Compressed disc images (Batocera format)

## Wine Dependencies

The launcher automatically installs these Windows dependencies:
- Visual C++ 2015 Runtime (`vcrun2015`)
- DirectX 9 (`d3dx9`)
- DirectX Shader Compiler 43 (`d3dcompiler_43`)
- DirectX Shader Compiler 47 (`d3dcompiler_47`)

## Troubleshooting

### Check logs
```bash
tail -f /userdata/system/logs/es_launch.log
```

### Manual Wine prefix check
```bash
ls -la /userdata/system/.wine-bottles/cxbx-r/
```

### Test Cxbx-Reloaded manually
```bash
cd /userdata/system/xbox-extra/cxbx-r/app
WINEPREFIX=/userdata/system/.wine-bottles/cxbx-r wine cxbxr.exe
```

## Technical Details

### How It Works

1. EmulationStation calls `xboxlauncher.py` with ROM and controller info
2. Launcher loads configuration from `batocera.conf` and YAML defaults
3. `GeneratorImporter` routes to the appropriate emulator generator
4. `CxbxrGenerator`:
   - Creates Wine prefix if needed
   - Installs Windows dependencies via winetricks
   - Configures `settings.ini` based on user options
   - Builds Wine command with environment variables
5. Command is executed and monitored

### Code References

The implementation follows patterns from:
- `batocera/configgen/generators/xenia/xeniaGenerator.py` - Wine-based Xbox 360 emulator
- `batocera/configgen/generators/model2emu/model2emuGenerator.py` - Wine dependencies
- `batocera/switch/configgen/switchlauncher.py` - Custom launcher structure

## Development

The code uses:
- Python 3 with type hints
- Batocera's `configgen` module for configuration management
- Batocera's `wine.Runner` class for Wine prefix management
- `CaseSensitiveConfigParser` for INI file handling

## Future Plans

- [ ] Add xemu-wine support (Windows xemu via Wine)
- [ ] Add more Cxbx-Reloaded options (controller mapping, etc.)
- [ ] Add per-game patches support
- [ ] Add save state management
- [ ] Add performance overlays

## License

This project integrates with Batocera Linux and Cxbx-Reloaded. Respect their respective licenses.
