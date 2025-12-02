# Lightgun Support for Xbox Emulation on Batocera

## Overview

Your Gun4IR lightguns should work with Xbox emulation on Batocera! This guide explains how to set them up.

## How Gun4IR Works with Batocera

Gun4IR devices use Arduino MCUs and appear to the system as USB HID mice. Batocera's gun detection system:
1. Scans for devices marked with `ID_INPUT_MOUSE=1`
2. Checks for the `ID_INPUT_GUN=1` property to identify them as lightguns
3. Reads available mouse buttons for trigger/action mappings

## Setting Up Gun4IR

### 1. Create udev Rules

Create `/userdata/system/udev.rules` (or add to existing):

```bash
# Gun4IR Lightguns
SUBSYSTEM=="input", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8036", ENV{ID_INPUT_GUN}="1"
SUBSYSTEM=="input", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8036", ENV{ID_INPUT_GUN_NEED_CROSS}="1"
```

**Note**: Replace vendor/product IDs with your Gun4IR's actual IDs. To find them:
```bash
lsusb
# Look for your Arduino device, e.g.:
# Bus 001 Device 005: ID 2341:8036 Arduino SA Leonardo
```

### 2. Configure Gun4IR Properties

You can set additional properties:
- `ENV{ID_INPUT_GUN}="1"` - Required to mark as lightgun
- `ENV{ID_INPUT_GUN_NEED_CROSS}="1"` - Shows crosshairs on screen
- `ENV{ID_INPUT_GUN_NEED_BORDERS}="1"` - For Sinden-style border detection (not needed for Gun4IR)

### 3. Enable Guns in Batocera Config

Edit `/userdata/system/batocera.conf`:

```ini
# Enable guns for Xbox system
xbox.use_guns=1

# Gun calibration and display options
xbox.controllers.guns.bordersmode=hidden   # hidden, auto, normal, gameonly, force
xbox.controllers.guns.borderssize=thin     # thin, medium, large (if using borders)

# Per-game configuration example (for House of the Dead III)
xbox["hotd3.iso"].use_guns=1
```

## Xbox Lightgun Games

Games that support lightgun input:
- **The House of the Dead III** - Classic zombie shooter
- **Silent Scope Complete** - Sniper game compilation
- **Area 51** - Sci-fi shooter
- **Starsky & Hutch** - Arcade-style driving/shooting

## Cxbx-Reloaded and Wine Considerations

### Current Status
The launcher now detects and passes gun information to Cxbx-Reloaded, but there are limitations:

1. **Wine Mouse Pass-through**: Wine needs to map the mouse input from Gun4IR to Windows
2. **Cxbx-R Input System**: Cxbx-Reloaded must recognize the mouse as Xbox Light Gun input
3. **Game Compatibility**: Not all Xbox lightgun games may work perfectly in Cxbx-R

### Testing Your Setup

1. **Verify Gun Detection**:
```bash
# SSH into Batocera
ssh root@batocera

# Check if guns are detected
ls -la /dev/input/by-id/ | grep -i gun
```

2. **Test in a Known Working Emulator** (e.g., RetroArch):
   - Try a different system with lightgun support first (like Sega Naomi's House of the Dead 2)
   - This confirms your Gun4IR hardware and udev rules work

3. **Check Logs**:
```bash
tail -f /userdata/system/logs/es_launch.log
# Look for: "Found X gun(s) for Xbox"
```

## Configuration in settings.ini

The `cxbxrGenerator.py` automatically configures Cxbx-Reloaded's `settings.ini`. For guns, relevant sections:

```ini
[input-general]
MouseAxisRange = 10          # Mouse sensitivity
MouseWheelRange = 80
IgnoreKbMoUnfocus = true     # Keep mouse active when unfocused

[input-port-0]
Type = -1                    # -1 = auto-detect, specific values for controller types
DeviceName = 
```

## Troubleshooting

### Gun Not Detected
```bash
# Check udev properties
udevadm info -a -p $(udevadm info -q path -n /dev/input/eventX)
# Replace X with your gun's event number

# Reload udev rules
udevadm control --reload-rules
udevadm trigger
```

### Gun Detected but Not Working in Cxbx-R

**Wine Mouse Capture**:
- Wine may need the window to capture mouse input
- Try setting: `WINE_MOUSE_CAPTURE=1` in the environment

**Input Port Configuration**:
- Xbox supported the Light Gun Controller on specific ports
- May need to configure Cxbx-R to recognize port device types

### Calibration Issues

Gun4IR typically requires:
1. Physical calibration via Gun4IR's calibration software
2. Per-game calibration in some titles

## Future Improvements

Possible enhancements to `cxbxrGenerator.py`:
- Automatic mouse-to-Xbox-lightgun port mapping
- Per-gun sensitivity configuration
- Crosshair overlay support
- Button remapping for triggers/reload

## Additional Resources

- Gun4IR: https://github.com/gunnfactory/Gun4IR
- Batocera Gun Config: https://wiki.batocera.org/lightguns
- Cxbx-Reloaded: https://github.com/Cxbx-Reloaded/Cxbx-Reloaded

## Quick Start Commands

```bash
# 1. Create udev rule (adjust vendor/product IDs)
echo 'SUBSYSTEM=="input", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8036", ENV{ID_INPUT_GUN}="1"' >> /userdata/system/udev.rules

# 2. Reload udev
udevadm control --reload-rules && udevadm trigger

# 3. Enable guns in batocera.conf
echo 'xbox.use_guns=1' >> /userdata/system/batocera.conf

# 4. Test with a lightgun game
# Launch House of the Dead III from EmulationStation
```

Your Gun4IR guns should now be recognized and available for Xbox lightgun games!
