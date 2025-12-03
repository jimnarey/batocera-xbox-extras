from __future__ import annotations

import logging
import os
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

class CxbxrGenerator(Generator):
    
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
        
        os.environ['WINEARCH'] = 'win32'
        _logger.info("Installing Wine dependencies for Cxbx-Reloaded...")
        wine_runner.install_wine_trick('vcrun2015')
        wine_runner.install_wine_trick('d3dx9')
        wine_runner.install_wine_trick('d3dcompiler_43')
        wine_runner.install_wine_trick('d3dcompiler_47')
        self._configure_settings(settings_file, system, gameResolution)
        commandArray: list[str | Path] = [wine_runner.wine, cxbxr_exe]
        rom_path = Path(rom)
        if rom_path.suffix.lower() in ['.xbe', '.iso']:
            commandArray.append(f'Z:{rom_path}')
        else:
            raise Exception(f"Unsupported ROM format: {rom_path.suffix}")
        
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
        return Command.Command(array=commandArray, env=environment)
    
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
