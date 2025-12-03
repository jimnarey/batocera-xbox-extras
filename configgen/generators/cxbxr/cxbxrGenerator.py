from __future__ import annotations

import logging
import os
import subprocess
import hashlib
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Final

from configgen import Command
from configgen.batoceraPaths import mkdir_if_not_exists
from configgen.controller import generate_sdl_game_controller_config
from configgen.utils import wine
from configgen.utils.wine import WINE_BASE
from configgen.utils.configparser import CaseSensitiveConfigParser
from configgen.generators.Generator import Generator

if TYPE_CHECKING:
    from configgen.types import HotkeysContext

_logger = logging.getLogger(__name__)

XBOX_EXTRA: Final = Path('/userdata/system/xbox-extra')
BATOCERA_LOGDIR : Final = Path('/userdata/system/logs')
ISO_EXTRACT_BASE: Final = XBOX_EXTRA / 'iso-extracts'
EXTRACT_XISO_BIN: Final = XBOX_EXTRA / 'bin' / 'extract-xiso'

class CxbxrGenerator(Generator):
    
    def __init__(self):
        super().__init__()
        self._extracted_iso: Path | None = None
        self._extract_dir: Path | None = None
    
    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "cxbxr",
            "keys": {"exit": ["KEY_LEFTALT", "KEY_F4"]}
        }
    
    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        """Generate the command to run Cxbx-Reloaded"""
        # Verify extract-xiso is installed
        if not EXTRACT_XISO_BIN.exists():
            raise Exception(
                f"extract-xiso not found at {EXTRACT_XISO_BIN}. "
                f"Please run the install script first."
            )

        cxbxr_base = XBOX_EXTRA / 'cxbx-r'
        cxbxr_app = cxbxr_base / 'app'
        cxbxr_exe = cxbxr_app / 'cxbxr-ldr.exe'
        settings_file = cxbxr_app / 'settings.ini'
        
        wine_runner = wine.Runner.default('cxbx-r')
        wine_runner.bottle_dir = cxbxr_base
        
        mkdir_if_not_exists(wine_runner.bottle_dir)
        if not cxbxr_exe.exists():
            raise Exception(
                f"Cxbx-Reloaded not found at {cxbxr_exe}. "
                f"Please run the install script first."
            )
        
        os.environ['WINEARCH'] = 'win64'
        
        self._initialize_wine_prefix(wine_runner)
        
        self._configure_settings(settings_file, system, gameResolution)
        
        rom_path = Path(rom)
        xbe_path: Path
        
        if rom_path.suffix.lower() == '.iso':
            extract_dir = self._get_extract_dir(rom_path)
            
            _logger.info(f"Extracting Xbox ISO {rom_path} to {extract_dir}")
            self._extract_iso(rom_path, extract_dir)
            self._extracted_iso = rom_path
            self._extract_dir = extract_dir
            
            xbe_path = extract_dir / 'default.xbe'
            if not xbe_path.exists():
                for file in extract_dir.rglob('*'):
                    if file.is_file() and file.name.lower() == 'default.xbe':
                        xbe_path = file
                        break
                else:
                    self._cleanup_extraction()
                    raise Exception(f"default.xbe not found in extracted ISO at {extract_dir}")
        
        elif rom_path.suffix.lower() == '.xbe':
            xbe_path = rom_path
        
        else:
            raise Exception(f"Unsupported ROM format: {rom_path.suffix}. Cxbx-Reloaded requires .xbe or .iso files.")
        
        commandArray: list[str | Path] = [
            wine_runner.wine, 
            cxbxr_exe, 
            '/load', 
            f'Z:{xbe_path}'
        ]
        
        environment = wine_runner.get_environment()
        environment.update({
            'SDL_GAMECONTROLLERCONFIG': generate_sdl_game_controller_config(playersControllers),
            'SDL_JOYSTICK_HIDAPI': '0',
        })
        
        if Path('/var/tmp/nvidia.prime').exists():
            variables_to_remove = ['__NV_PRIME_RENDER_OFFLOAD', '__VK_LAYER_NV_optimus', '__GLX_VENDOR_LIBRARY_NAME']
            for variable_name in variables_to_remove:
                if variable_name in os.environ:
                    del os.environ[variable_name]
            
            environment.update({
                'VK_ICD_FILENAMES': '/usr/share/vulkan/icd.d/nvidia_icd.x86_64.json',
                'VK_LAYER_PATH': '/usr/share/vulkan/explicit_layer.d'
            })
        
        _logger.debug(f"Cxbx-Reloaded command: {commandArray}")
        
        return self._wrap_with_cleanup(Command.Command(array=commandArray, env=environment))
    
    def _get_extract_dir(self, iso_path: Path) -> Path:
        """Generate a temporary extraction directory path based on ISO filename"""
        path_hash = hashlib.md5(str(iso_path).encode()).hexdigest()[:8]
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in iso_path.stem)
        extract_name = f"{safe_name}_{path_hash}"
        extract_dir = ISO_EXTRACT_BASE / extract_name
        mkdir_if_not_exists(ISO_EXTRACT_BASE)
        return extract_dir
    
    def _initialize_wine_prefix(self, wine_runner) -> None:
        """Install Wine dependencies. Prefix is created automatically by winetricks."""
        
        # Install dependencies - this will create the prefix if it doesn't exist
        _logger.info("Installing Wine dependencies (vcrun2019, d3dcompiler_47)...")
        wine_runner.install_wine_trick('vcrun2019')
        wine_runner.install_wine_trick('d3dcompiler_47')
    
    def _extract_iso(self, iso_path: Path, extract_dir: Path) -> None:
        """Extract an Xbox ISO file using extract-xiso"""
        mkdir_if_not_exists(extract_dir)
        
        try:
            _logger.info(f"Running extract-xiso on {iso_path}")
            result = subprocess.run(
                [str(EXTRACT_XISO_BIN), '-d', str(extract_dir), str(iso_path)],
                check=True,
                capture_output=True,
                text=True
            )
            _logger.info(f"Successfully extracted {iso_path} to {extract_dir}")
            if result.stdout:
                _logger.debug(f"extract-xiso output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract Xbox ISO: {e.stderr if e.stderr else str(e)}")
    
    def _cleanup_extraction(self) -> None:
        """Clean up extracted ISO directory after emulator exit"""
        if self._extract_dir and self._extract_dir.exists():
            _logger.info(f"Cleaning up extracted ISO at {self._extract_dir}")
            try:
                shutil.rmtree(self._extract_dir)
                self._extracted_iso = None
                self._extract_dir = None
            except Exception as e:
                _logger.error(f"Failed to cleanup extraction directory {self._extract_dir}: {e}")
    
    def _wrap_with_cleanup(self, command: Command.Command) -> Command.Command:
        """Wrap the command to ensure cleanup happens after execution"""
        if self._extract_dir:
            wrapper_script = XBOX_EXTRA / 'cxbx-wrapper.sh'
            wrapper_content = f'''#!/bin/bash
# Auto-generated wrapper for Cxbx-Reloaded with ISO cleanup

# Run the emulator
{' '.join(str(arg) for arg in command.array)}
EXIT_CODE=$?

# Cleanup extracted ISO
if [ -d "{self._extract_dir}" ]; then
    rm -rf "{self._extract_dir}" 2>/dev/null || true
fi

exit $EXIT_CODE
'''
            wrapper_script.write_text(wrapper_content)
            wrapper_script.chmod(0o755)
            
            return Command.Command(
                array=['/bin/bash', str(wrapper_script)],
                env=command.env
            )
        
        return command
    
    def _configure_settings(self, settings_file: Path, system, gameResolution) -> None:
        """Configure Cxbx-Reloaded settings.ini file"""
        
        if not settings_file.exists():
            _logger.info(f"Creating default settings file at {settings_file}")
            self._create_default_settings(settings_file)
        
        config = CaseSensitiveConfigParser(interpolation=None)
        if settings_file.is_file():
            config.read(settings_file)
        
        for section in ['gui', 'core', 'video', 'audio', 'input-general']:
            if not config.has_section(section):
                config.add_section(section)
                        
        if system.isOptSet('cxbxr_debug'):
            debug_mode = '1' if system.getOptBoolean('cxbxr_debug') else '0'
            config.set('gui', 'CxbxDebugMode', debug_mode)
            config.set('gui', 'CxbxDebugLogFile', str(BATOCERA_LOGDIR / 'cxbx-gui-debug.log'))
            config.set('core', 'KrnlDebugMode', debug_mode)
            config.set('core', 'KrnlDebugLogFile', str(BATOCERA_LOGDIR / 'cxbx-kernel-debug.log'))
        
        with settings_file.open('w') as configfile:
            config.write(configfile)
        
        _logger.info(f"Cxbx-Reloaded settings configured at {settings_file}")
    
    def _create_default_settings(self, settings_file: Path) -> None:
        """Create default settings.ini file"""
        default_content = """[gui]
CxbxDebugMode = 0x0
CxbxDebugLogFile = 
DataStorageToggle = 0x1
DataCustomLocation = 
IgnoreInvalidXbeSig = false
IgnoreInvalidXbeSec = false
ConsoleTypeToggle = 0x0

[core]
Revision = 9
FlagsLLE = 0x0
KrnlDebugMode = 0x0
KrnlDebugLogFile = 
AllowAdminPrivilege = false
LogLevel = 1
LogPopupTestCase = false

[video]
VideoResolution = 
adapter = 0x0
Direct3DDevice = 0x0
VSync = false
FullScreen = true
MaintainAspect = true
RenderResolution = 1

[audio]
adapter = 00000000 0000 0000 0000 000000000000
PCM = true
XADPCM = true
UnknownCodec = true
MuteOnUnfocus = true

[input-general]
MouseAxisRange = 10
MouseWheelRange = 80
IgnoreKbMoUnfocus = true

[overlay]
Build Hash = false
FPS = false
HLE/LLE Stats = false
Title Name = false
File Name = false

[hack]
DisablePixelShaders = false
UseAllCores = false
SkipRdtscPatching = false
"""
        mkdir_if_not_exists(settings_file.parent)
        settings_file.write_text(default_content)
    
    def getMouseMode(self, config, rom):
        """Cxbx-Reloaded may need mouse for GUI"""
        return True
    
    def getInGameRatio(self, config, gameResolution, rom):
        """Xbox games are typically 4:3 or 16:9"""
        if config.get("cxbxr_aspect_ratio") == "16:9":
            return 16/9
        return 4/3
