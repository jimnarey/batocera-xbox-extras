#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from configgen.batoceraPaths import SAVES
from configgen.Emulator import Emulator
from configgen.utils.logger import setup_logging
from configgen.controller import Controller
from configgen.gun import Gun
from generators.GeneratorImporter import getGenerator

eslog = logging.getLogger(__name__)

def main(args, maxnbplayers):
    return start_rom(args, maxnbplayers, args.rom, args.rom)

def start_rom(args, maxnbplayers, rom, romConfiguration):
    playersControllers = Controller.load_for_players(maxnbplayers, args)
    
    systemName = args.system
    eslog.debug(f"Running system: {systemName}")
    system = Emulator(args, romConfiguration)
    
    if args.emulator is not None:
        system.config["emulator"] = args.emulator
        system.config["emulator-forced"] = True
    if args.core is not None:
        system.config["core"] = args.core
        system.config["core-forced"] = True
    
    debugDisplay = dict(system.config)
    if "retroachievements.password" in debugDisplay:
        debugDisplay["retroachievements.password"] = "***"
    eslog.debug(f"Settings: {debugDisplay}")
    if "emulator" in system.config and "core" in system.config:
        eslog.debug("emulator: {}, core: {}".format(system.config["emulator"], system.config["core"]))
    else:
        if "emulator" in system.config:
            eslog.debug("emulator: {}".format(system.config["emulator"]))

    metadata = {}
    
    if args.lightgun:
        system.config["use_guns"] = True
    
    if system.config.get('use_guns') and system.config.use_guns:
        guns = Gun.get_and_precalibrate_all(system, rom)
        eslog.info(f"Found {len(guns)} gun(s) for Xbox")
    else:
        eslog.info("Guns disabled for Xbox")
        guns = []
    
    wheels: dict = {}
    
    from configgen.utils import videoMode
    gameResolution = videoMode.getCurrentResolution()
    eslog.debug("resolution: {}x{}".format(str(gameResolution["width"]), str(gameResolution["height"])))
    dirname = SAVES / system.name
    if not dirname.exists():
        dirname.mkdir(parents=True)
    
    core = system.config.get('core')
    if core is None or not isinstance(core, str):
        core = None
    
    generator = getGenerator(system.config['emulator'], core)
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
        parser.add_argument("-rom", help="rom absolute path", type=Path, required=True)
        parser.add_argument("-emulator", help="force emulator", type=str, required=False)
        parser.add_argument("-core", help="force emulator core", type=str, required=False)
        parser.add_argument("-netplaymode", help="host/client", type=str, required=False)
        parser.add_argument("-netplaypass", help="enable spectator mode", type=str, required=False)
        parser.add_argument("-netplayip", help="remote ip", type=str, required=False)
        parser.add_argument("-netplayport", help="remote port", type=str, required=False)
        parser.add_argument("-netplaysession", help="netplay session", type=str, required=False)
        parser.add_argument("-state_slot", help="state slot", type=str, required=False)
        parser.add_argument("-state_filename", help="state filename", type=str, required=False)
        parser.add_argument("-autosave", help="autosave", type=str, required=False)
        parser.add_argument("-systemname", help="system fancy name", type=str, required=False)
        parser.add_argument("-gameinfoxml", help="game info xml", type=str, nargs='?', default='/dev/null', required=False)
        parser.add_argument("-lightgun", help="configure lightguns", action="store_true")
        parser.add_argument("-wheel", help="configure wheel", action="store_true")
        
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
