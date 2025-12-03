#!/usr/bin/env bash
#
# Batocera Xbox Extras Uninstaller
# Remove Cxbx-Reloaded and xemu-wine, restore default xemu configuration
#
# Usage:
#   bash uninstall.sh
#

set -e 

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Batocera Xbox Extras Uninstaller${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if xbox-extra directory exists
if [ ! -d "/userdata/system/xbox-extra" ]; then
    echo -e "${YELLOW}Warning:${NC} /userdata/system/xbox-extra not found. May already be uninstalled."
fi

echo -e "${YELLOW}[1/3]${NC} Removing xbox-extra directory..."
if [ -d "/userdata/system/xbox-extra" ]; then
    rm -rf /userdata/system/xbox-extra
    echo "  ✓ Removed /userdata/system/xbox-extra"
else
    echo "  - Directory not found, skipping"
fi

echo -e "${YELLOW}[2/3]${NC} Removing ES Systems configuration..."
if [ -f "/userdata/system/configs/emulationstation/es_systems_xbox.cfg" ]; then
    rm -f /userdata/system/configs/emulationstation/es_systems_xbox.cfg
    echo "  ✓ Removed es_systems_xbox.cfg"
else
    echo "  - Configuration not found, skipping"
fi

echo -e "${YELLOW}[2/3]${NC} Removing ES Features configuration..."
if [ -f "/userdata/system/configs/emulationstation/es_features_xbox.cfg" ]; then
    rm -f /userdata/system/configs/emulationstation/es_features_xbox.cfg
    echo "  ✓ Removed es_features_xbox.cfg"
else
    echo "  - Configuration not found, skipping"
fi

echo -e "${YELLOW}[3/3]${NC} Resetting batocera.conf to use xemu..."
BATOCERA_CONF="/userdata/system/batocera.conf"

if [ -f "$BATOCERA_CONF" ]; then
    if grep -q "^xbox.emulator=" "$BATOCERA_CONF"; then
        sed -i 's/^xbox.emulator=.*/xbox.emulator=xemu/' "$BATOCERA_CONF"
        echo "  ✓ Set xbox.emulator to xemu"
    else
        echo "  - xbox.emulator not found in config"
    fi

    if grep -q "^xbox.core=" "$BATOCERA_CONF"; then
        sed -i 's/^xbox.core=.*/xbox.core=xemu/' "$BATOCERA_CONF"
        echo "  ✓ Set xbox.core to xemu"
    else
        echo "  - xbox.core not found in config"
    fi

    if grep -q "^xbox.cxbxr_" "$BATOCERA_CONF"; then
        sed -i '/^xbox.cxbxr_/d' "$BATOCERA_CONF"
        echo "  ✓ Removed cxbxr-specific options"
    else
        echo "  - No cxbxr-specific options found"
    fi
else
    echo -e "  ${YELLOW}Warning:${NC} batocera.conf not found at $BATOCERA_CONF"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Uninstallation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Removed components:"
echo "  ✓ Xbox launcher scripts"
echo "  ✓ Cxbx-Reloaded emulator"
echo "  ✓ xemu-wine emulator"
echo "  ✓ extract-xiso tool"
echo "  ✓ EmulationStation custom configuration"
echo "  ✓ Configuration reset to xemu defaults"
echo ""
echo "Next steps:"
echo "  1. Restart EmulationStation:"
echo "     systemctl restart emulationstation"
echo ""
echo "  2. Or use the Batocera menu:"
echo "     Main Menu > Quit > Restart EmulationStation"
echo ""
echo -e "${YELLOW}Note:${NC} Xbox games will now use the built-in xemu emulator."
