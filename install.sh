#!/usr/bin/env bash
#
# Batocera Xbox Extras Installer
# Install Cxbx-Reloaded and xemu-wine for Xbox emulation on Batocera
#
# Usage:
#   wget -O - https://raw.githubusercontent.com/jimnarey/batocera-xbox-extras/master/install.sh | bash
#   or
#   curl -s https://raw.githubusercontent.com/jimnarey/batocera-xbox-extras/master/install.sh | bash
#

set -e 

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Batocera Xbox Extras Installer${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

echo -e "${YELLOW}[1/6]${NC} Creating directories..."
mkdir -p /userdata/system/xbox-extra
mkdir -p /userdata/system/configs/emulationstation

echo -e "${YELLOW}[2/6]${NC} Downloading source code from GitHub..."
cd "${TEMP_DIR}"
wget -q --show-progress -O batocera-xbox-extras.zip \
    https://github.com/jimnarey/batocera-xbox-extras/archive/refs/heads/master.zip

echo -e "${YELLOW}[3/6]${NC} Extracting source code..."
unzip -q batocera-xbox-extras.zip
SOURCE_DIR="${TEMP_DIR}/batocera-xbox-extras-master"

echo -e "${YELLOW}[4/6]${NC} Downloading emulators..."
echo "  - Downloading Cxbx-Reloaded..."
wget -q --show-progress -O "${TEMP_DIR}/CxbxReloaded-Release.zip" \
    https://github.com/Cxbx-Reloaded/Cxbx-Reloaded/releases/download/CI-cf031f1/CxbxReloaded-Release.zip

echo "  - Downloading xemu (Windows)..."
wget -q --show-progress -O "${TEMP_DIR}/xemu-win-x86_64-release.zip" \
    https://github.com/xemu-project/xemu/releases/latest/download/xemu-win-x86_64-release.zip

echo -e "${YELLOW}[5/6]${NC} Installing files..."
echo "  - Installing launcher scripts..."
cp -rf "${SOURCE_DIR}/configgen" /userdata/system/xbox-extra/
chmod +x /userdata/system/xbox-extra/configgen/xboxlauncher.py

echo "  - Installing ES Systems configuration..."
cp -f "${SOURCE_DIR}/es_systems_xbox.cfg" /userdata/system/configs/emulationstation/

echo "  - Extracting Cxbx-Reloaded..."
mkdir -p /userdata/system/xbox-extra/cxbx-r/app
unzip -q -o "${TEMP_DIR}/CxbxReloaded-Release.zip" -d /userdata/system/xbox-extra/cxbx-r/app

echo "  - Extracting xemu..."
mkdir -p /userdata/system/xbox-extra/xemu-wine/app
unzip -q -o "${TEMP_DIR}/xemu-win-x86_64-release.zip" -d /userdata/system/xbox-extra/xemu-wine/app
echo -e "${YELLOW}[6/6]${NC} Cleaning up..."

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Installed components:"
echo "  ✓ Cxbx-Reloaded (Wine-based Xbox emulator)"
echo "  ✓ xemu-wine (Windows build of xemu)"
echo "  ✓ Xbox launcher scripts"
echo "  ✓ EmulationStation configuration"
echo ""
echo "Next steps:"
echo "  1. Restart EmulationStation:"
echo "     systemctl restart emulationstation"
echo ""
echo "  2. Or use the Batocera menu:"
echo "     Main Menu > Quit > Restart EmulationStation"
echo ""
echo "  3. Place Xbox ROMs in: /userdata/roms/xbox/"
echo "     Supported formats: .iso, .xbe"
echo ""
echo "Configuration:"
echo "  - Edit /userdata/system/batocera.conf for options"
echo "  - Documentation: ${SOURCE_DIR}/configgen/README.md"
echo ""
echo -e "${YELLOW}Note:${NC} The Xbox system will appear after restarting EmulationStation."