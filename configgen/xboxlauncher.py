#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add the configgen module to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import from batocera's configgen
from configgen.batoceraPaths import SAVES
from configgen.Emulator import Emulator
from configgen.utils.logger import setup_logging
import configgen.controllersConfig as controllers
from generators.GeneratorImporter import getGenerator

eslog = logging.getLogger(__name__)

def main(args, maxnbplayers):
    return start_rom(args, maxnbplayers, args.rom, args.rom)

def start_rom(args, maxnbplayers, rom, romConfiguration):
    playersControllers = {}
    
    controllersInput = []
    for p in range(1, maxnbplayers + 1):
        ci = {
            "index": getattr(args, f"p{p}index"),
            "guid": getattr(args, f"p{p}guid"),
            "name": getattr(args, f"p{p}name"),
            "devicepath": getattr(args, f"p{p}devicepath"),
            "nbbuttons": getattr(args, f"p{p}nbbuttons"),
            "nbhats": getattr(args, f"p{p}nbhats"),
            "nbaxes": getattr(args, f"p{p}nbaxes")
        }
        controllersInput.append(ci)
    
    playersControllers = controllers.loadControllerConfig(controllersInput)
    
    systemName = args.system
    eslog.debug(f"Running system: {systemName}")
    system = Emulator(systemName, romConfiguration)
    
    if args.emulator is not None:
        system.config["emulator"] = args.emulator
        system.config["emulator-forced"] = True
    if args.core is not None:
        system.config["core"] = args.core
        system.config["core-forced"] = True
    
    debugDisplay = system.config.copy()
    if "retroachievements.password" in debugDisplay:
        debugDisplay["retroachievements.password"] = "***"
    eslog.debug(f"Settings: {debugDisplay}")
    if "emulator" in system.config and "core" in system.config:
        eslog.debug("emulator: {}, core: {}".format(system.config["emulator"], system.config["core"]))
    else:
        if "emulator" in system.config:
            eslog.debug("emulator: {}".format(system.config["emulator"]))
    
    metadata = {}
    guns = []  # Temporary
    wheels = []
    
    from configgen.utils import videoMode
    gameResolution = videoMode.getCurrentResolution()
    eslog.debug("resolution: {}x{}".format(str(gameResolution["width"]), str(gameResolution["height"])))
    dirname = SAVES / system.name
    if not dirname.exists():
        dirname.mkdir(parents=True)
    generator = getGenerator(system.config['emulator'], system.config.get('core'))
    cmd = generator.generate(system, Path(rom), playersControllers, metadata, guns, wheels, gameResolution)
    exitCode = runCommand(cmd)
    
    return exitCode

def runCommand(command):
    """Execute the emulator command"""
    command.array.insert(0, "nice")
    command.array.insert(1, "-n")
    command.array.insert(2, "-11")
    
    envvars = dict(os.environ)
    envvars.update(command.env)
    command.env = envvars
    
    eslog.debug(f"command: {str(command)}")
    eslog.debug(f"command array: {str(command.array)}")
    eslog.debug(f"env: {str(command.env)}")
    
    exitcode = -1
    if command.array:
        proc = subprocess.Popen(command.array, env=command.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, err = proc.communicate()
            exitcode = proc.returncode
            eslog.debug(out.decode())
            if err:
                eslog.error(err.decode())
        except Exception as e:
            eslog.error(f"Emulator error: {e}")
    
    return exitcode

def launch():
    """Parse arguments and launch emulator"""
    with setup_logging():
        parser = argparse.ArgumentParser(description='Xbox emulator launcher')
        
        maxnbplayers = 4
        for p in range(1, maxnbplayers + 1):
            parser.add_argument(f"-p{p}index", help=f"player{p} controller index", type=int, required=False)
            parser.add_argument(f"-p{p}guid", help=f"player{p} controller SDL2 guid", type=str, required=False)
            parser.add_argument(f"-p{p}name", help=f"player{p} controller name", type=str, required=False)
            parser.add_argument(f"-p{p}devicepath", help=f"player{p} controller device", type=str, required=False)
            parser.add_argument(f"-p{p}nbbuttons", help=f"player{p} controller number of buttons", type=str, required=False)
            parser.add_argument(f"-p{p}nbhats", help=f"player{p} controller number of hats", type=str, required=False)
            parser.add_argument(f"-p{p}nbaxes", help=f"player{p} controller number of axes", type=str, required=False)
        
        parser.add_argument("-system", help="select the system to launch", type=str, required=True)
        parser.add_argument("-rom", help="rom absolute path", type=str, required=True)
        parser.add_argument("-emulator", help="force emulator", type=str, required=False)
        parser.add_argument("-core", help="force emulator core", type=str, required=False)
        parser.add_argument("-systemname", help="system fancy name", type=str, required=False)
        parser.add_argument("-gameinfoxml", help="game info xml", type=str, nargs='?', default='/dev/null', required=False)
        
        args = parser.parse_args()
        
        try:
            exitcode = main(args, maxnbplayers)
        except Exception as e:
            eslog.error("Xbox launcher exception: ", exc_info=True)
            exitcode = -1
        
        eslog.debug(f"Exiting with status {exitcode}")
        sys.exit(exitcode)

if __name__ == '__main__':
    launch()
