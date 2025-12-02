from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configgen.generators.Generator import Generator

def getGenerator(emulator: str, core: str | None = None) -> Generator:
    """Import and return the appropriate generator class based on emulator and core."""
    if emulator == 'cxbx-r' or (core and core == 'cxbxr'):
        from .cxbxr.cxbxrGenerator import CxbxrGenerator
        return CxbxrGenerator()
    
    if emulator == 'xemu':
        from configgen.generators.xemu.xemuGenerator import XemuGenerator
        return XemuGenerator()
    
    raise Exception(f"no generator found for emulator {emulator} with core {core}")
