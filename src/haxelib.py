import platform
from pathlib import Path

def getHaxelibPath():
	if platform.system() == "Windows":
		return "C:\\HaxeToolkit\\haxe\\lib"
	elif platform.system() == "Linux":
		return str(Path.home().joinpath("haxelib"))

def getActiveHaxelibs():
	paths = []

	for path in Path(getHaxelibPath()).glob("*"):
		if path.is_dir():
			paths.append(path.name.replace(",", "."))

	return paths