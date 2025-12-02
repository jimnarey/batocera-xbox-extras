#!/usr/bin/env bash

mkdir -p /userdata/system/xbox-extra
mkdir -p /userdata/system/xbox-extra/configgen

echo "Downloading Cxbx-Reloaded..."
wget -O /userdata/system/xbox-extra/CxbxReloaded-Release.zip https://github.com/Cxbx-Reloaded/Cxbx-Reloaded/releases/download/CI-cf031f1/CxbxReloaded-Release.zip

echo "Downloading xemu (Windows)..."
wget -O /userdata/system/xbox-extra/xemu-win-x86_64-release.zip https://github.com/xemu-project/xemu/releases/latest/download/xemu-win-x86_64-release.zip

echo "Extracting Cxbx-Reloaded..."
unzip -q /userdata/system/xbox-extra/CxbxReloaded-Release.zip -d /userdata/system/xbox-extra/cxbx-r/app

echo "Extracting xemu..."
unzip -q /userdata/system/xbox-extra/xemu-win-x86_64-release.zip -d /userdata/system/xbox-extra/xemu-wine/app

echo "Installing launcher scripts..."
cp -r configgen/* /userdata/system/xbox-extra/configgen/

chmod +x /userdata/system/xbox-extra/configgen/xboxlauncher.py

echo "Installing ES Systems configuration..."
cp es_systems_xbox.cfg /userdata/system/configs/emulationstation/es_systems_xbox.cfg

echo "Cleaning up..."
rm /userdata/system/xbox-extra/CxbxReloaded-Release.zip
rm /userdata/system/xbox-extra/xemu-win-x86_64-release.zip

echo "Installation complete!"
echo "The Xbox system should now be available in EmulationStation."
echo "You may need to restart EmulationStation for changes to take effect."