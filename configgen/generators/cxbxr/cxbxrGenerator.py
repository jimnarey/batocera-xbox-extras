from __future__ import annotations

import logging
import os
import subprocess
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Final

from configgen import Command
from configgen.batoceraPaths import mkdir_if_not_exists
from configgen.controller import generate_sdl_game_controller_config
from configgen.utils import wine
from configgen.utils.configparser import CaseSensitiveConfigParser
from configgen.generators.Generator import Generator

if TYPE_CHECKING:
    from configgen.types import HotkeysContext

_logger = logging.getLogger(__name__)

XBOX_EXTRA: Final = Path('/userdata/system/xbox-extra')
ISO_MOUNT_BASE: Final = XBOX_EXTRA / 'iso-mounts'

class CxbxrGenerator(Generator):
    
    def __init__(self):
        super().__init__()
        self._mounted_iso: Path | None = None
        self._mount_point: Path | None = None
    
    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "cxbxr",
            "keys": {"exit": ["KEY_LEFTALT", "KEY_F4"]}
        }
    
    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        """Generate the command to run Cxbx-Reloaded"""
        wine_runner = wine.Runner.default('cxbx-r')
        cxbxr_app = XBOX_EXTRA / 'cxbx-r' / 'app'
        cxbxr_exe = cxbxr_app / 'cxbx.exe'
        settings_file = cxbxr_app / 'settings.ini'
        
        mkdir_if_not_exists(wine_runner.bottle_dir)
        if not cxbxr_exe.exists():
            raise Exception(
                f"Cxbx-Reloaded not found at {cxbxr_exe}. "
                f"Please run the install script first."
            )
        os.environ['WINEARCH'] = 'win64'
        _logger.info("Installing Wine dependencies for Cxbx-Reloaded...")
        wine_runner.install_wine_trick('vcrun2015')
        wine_runner.install_wine_trick('d3dx9')
        wine_runner.install_wine_trick('d3dcompiler_43')
        wine_runner.install_wine_trick('d3dcompiler_47')
        
        self._configure_settings(settings_file, system, gameResolution)
        
        rom_path = Path(rom)
        xbe_path: Path
        
        # Handle ISO files - mount and find default.xbe
        if rom_path.suffix.lower() == '.iso':
            mount_point = self._get_mount_point(rom_path)
            
            # Check if already mounted
            if self._is_mounted(mount_point):
                _logger.info(f"ISO already mounted at {mount_point}")
            else:
                _logger.info(f"Mounting ISO {rom_path} to {mount_point}")
                self._mount_iso(rom_path, mount_point)
                self._mounted_iso = rom_path
                self._mount_point = mount_point
            
            # Find default.xbe in mount point
            xbe_path = mount_point / 'default.xbe'
            if not xbe_path.exists():
                # Try case-insensitive search
                for file in mount_point.iterdir():
                    if file.name.lower() == 'default.xbe':
                        xbe_path = file
                        break
                else:
                    self._cleanup_mount()
                    raise Exception(f"default.xbe not found in ISO at {mount_point}")
        
        elif rom_path.suffix.lower() == '.xbe':
            xbe_path = rom_path
        
        else:
            raise Exception(f"Unsupported ROM format: {rom_path.suffix}. Cxbx-Reloaded requires .xbe or .iso files.")
        
        commandArray: list[str | Path] = [wine_runner.wine, cxbxr_exe, f'Z:{xbe_path}']
        
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
        
        # Wrap the command to ensure cleanup after execution
        return self._wrap_with_cleanup(Command.Command(array=commandArray, env=environment))
    
    def _get_mount_point(self, iso_path: Path) -> Path:
        """Generate a predictable mount point path based on ISO filename"""
        # Use first 8 chars of MD5 hash of the ISO path for uniqueness
        path_hash = hashlib.md5(str(iso_path).encode()).hexdigest()[:8]
        # Sanitize the ISO stem (filename without extension)
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in iso_path.stem)
        mount_name = f"{safe_name}_{path_hash}"
        mount_point = ISO_MOUNT_BASE / mount_name
        mkdir_if_not_exists(ISO_MOUNT_BASE)
        return mount_point
    
    def _is_mounted(self, mount_point: Path) -> bool:
        """Check if the mount point is already mounted"""
        try:
            result = subprocess.run(
                ['mountpoint', '-q', str(mount_point)],
                capture_output=True
            )
            return result.returncode == 0
        except Exception as e:
            _logger.warning(f"Error checking mount point: {e}")
            return False
    
    def _mount_iso(self, iso_path: Path, mount_point: Path) -> None:
        """Mount an ISO file to the specified mount point"""
        mkdir_if_not_exists(mount_point)
        
        try:
            subprocess.run(
                ['mount', '-o', 'loop,ro', str(iso_path), str(mount_point)],
                check=True,
                capture_output=True,
                text=True
            )
            _logger.info(f"Successfully mounted {iso_path} to {mount_point}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to mount ISO: {e.stderr}")
    
    def _unmount_iso(self, mount_point: Path) -> None:
        """Unmount an ISO from the specified mount point"""
        if not self._is_mounted(mount_point):
            _logger.debug(f"Mount point {mount_point} not mounted, skipping unmount")
            return
        
        try:
            subprocess.run(
                ['umount', str(mount_point)],
                check=True,
                capture_output=True,
                text=True
            )
            _logger.info(f"Successfully unmounted {mount_point}")
        except subprocess.CalledProcessError as e:
            _logger.error(f"Failed to unmount {mount_point}: {e.stderr}")
    
    def _cleanup_mount(self) -> None:
        """Clean up any mounted ISO after emulator exit"""
        if self._mount_point and self._mounted_iso:
            _logger.info(f"Cleaning up mount for {self._mounted_iso}")
            self._unmount_iso(self._mount_point)
            self._mounted_iso = None
            self._mount_point = None
    
    def _wrap_with_cleanup(self, command: Command.Command) -> Command.Command:
        """Wrap the command to ensure cleanup happens after execution"""
        if self._mount_point:
            # Create a wrapper script that ensures cleanup
            wrapper_script = XBOX_EXTRA / 'cxbx-wrapper.sh'
            wrapper_content = f'''#!/bin/bash
# Auto-generated wrapper for Cxbx-Reloaded with ISO cleanup

# Run the emulator
{' '.join(str(arg) for arg in command.array)}
EXIT_CODE=$?

# Cleanup mount
if mountpoint -q "{self._mount_point}"; then
    umount "{self._mount_point}" 2>/dev/null || true
fi

exit $EXIT_CODE
'''
            wrapper_script.write_text(wrapper_content)
            wrapper_script.chmod(0o755)
            
            # Return a new command that runs the wrapper
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
        
        if system.isOptSet('cxbxr_fullscreen'):
            config.set('video', 'FullScreen', 'true' if system.getOptBoolean('cxbxr_fullscreen') else 'false')
        else:
            config.set('video', 'FullScreen', 'true')
        
        if system.isOptSet('cxbxr_resolution'):
            resolution = system.config['cxbxr_resolution']
            config.set('video', 'VideoResolution', resolution)
        else:
            config.set('video', 'VideoResolution', f"{gameResolution['width']}x{gameResolution['height']}")
        
        if system.isOptSet('cxbxr_vsync'):
            config.set('video', 'VSync', 'true' if system.getOptBoolean('cxbxr_vsync') else 'false')
        else:
            config.set('video', 'VSync', 'false')
        
        if system.isOptSet('cxbxr_aspect'):
            config.set('video', 'MaintainAspect', 'true' if system.getOptBoolean('cxbxr_aspect') else 'false')
        else:
            config.set('video', 'MaintainAspect', 'true')
        
        if system.isOptSet('cxbxr_render_scale'):
            config.set('video', 'RenderResolution', system.config['cxbxr_render_scale'])
        
        if system.isOptSet('cxbxr_debug'):
            debug_mode = '1' if system.getOptBoolean('cxbxr_debug') else '0'
            config.set('gui', 'CxbxDebugMode', debug_mode)
            config.set('core', 'KrnlDebugMode', debug_mode)
        
        if system.isOptSet('cxbxr_lle_gpu'):
            config.set('core', 'FlagsLLE', '0x1' if system.getOptBoolean('cxbxr_lle_gpu') else '0x0')
        
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
