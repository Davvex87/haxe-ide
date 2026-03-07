import platform
import os
from pathlib import Path

def getHaxeBinPath():
	if platform.system() == "Windows":
		return "C:\\HaxeToolkit\\haxe\\haxe.exe"
	elif platform.system() == "Linux":
		return "/usr/bin/haxe"

def getHaxeVersion():
	haxe_bin = Path(getHaxeBinPath())
	if haxe_bin.exists():
		version_output = os.popen(f'"{haxe_bin}" --version').read().strip()
		return version_output
	else:
		return None