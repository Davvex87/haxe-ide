import tempfile
import os
import time
import shutil
from typing import Callable, Optional, List
from managedprocess import ManagedProcess
import haxe
from pathlib import Path


def find_lang_executable(base: str = "lua", versions: List[str] = None) -> Optional[str]:
	if versions is None:
		if base == "lua":
			versions = ["5.4", "5.3", "5.2", "5.1"]
		elif base == "python":
			versions = ["3"]

	if shutil.which(base):
		return base

	for version in versions:
		candidates = [
			f"{base}{version}",
			f"{base}{version.replace('.', '_')}",
			f"{base}{version.replace('.', '')}"
		]

		for candidate in candidates:
			if shutil.which(candidate):
				return candidate

	return None

class TestWorkspace:
	def __init__(self, main_class: str, target: str, haxelibs: List[str], custom_hxml_flags: List[str], modules: List[dict]):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.path = self.temp_dir.name

		self.main_class = main_class
		self.target = target
		self.haxelibs = haxelibs
		self.custom_hxml_flags = custom_hxml_flags
		self.modules = modules

		self._on_setup: Optional[Callable[[], None]] = None
		self._on_cleanup: Optional[Callable[[], None]] = None
		self._on_start: Optional[Callable[[], None]] = None
		self._on_stdout: Optional[Callable[[str], None]] = None
		self._on_stderr: Optional[Callable[[str], None]] = None
		self._on_finish: Optional[Callable[[int], None]] = None

		self._proc: Optional[ManagedProcess] = None
		self._compile_proc: Optional[ManagedProcess] = None
		self._stopped_during_compile = False
		self._output_path: Optional[str] = None

		"""
		# For debugging purposes, you can uncomment the following code to output the workspace configuration to a JSON file.
		import json
		with open('out.json', 'w', encoding='utf-8') as f:
			json.dump({
				"main_class": main_class,
				"target": target,
				"haxelibs": haxelibs,
				"custom_hxml_flags": custom_hxml_flags,
				"modules": modules
			}, f, ensure_ascii=False, indent=4)
		"""

	def setup(self):
		if self._on_setup:
			self._on_setup()

		self._stopped_during_compile = False
		resources = []

		for mod in self.modules:
			path:str = mod["path"]
			type:str = mod["type"]
			content:str = mod["content"]

			if type == "haxe_module":
				if not path.endswith(".hx"):
					path += ".hx"
			else:
				if type == "json_resource":
					if not path.endswith(".json"):
						path += ".json"
				resources.append(path)
				
			file = os.path.join(self.path, path)
			os.makedirs(os.path.dirname(file), exist_ok=True)
			with open(file, "w") as f:
				f.write(content)

		args = ["-m", self.main_class]

		if self.target == "eval":
			args.append("--interp")
		elif self.target == "javascript":
			args.append("--js")
			self._output_path = os.path.join(self.path, "output.js")
			args.append(self._output_path)
		elif self.target == "neko":
			args.append("--neko")
			self._output_path = os.path.join(self.path, "output.n")
			args.append(self._output_path)
		elif self.target == "hashlink":
			args.append("--hl")
			self._output_path = os.path.join(self.path, "output.hl")
			args.append(self._output_path)
		elif self.target == "cppia":
			args.append("--cppia")
			self._output_path = os.path.join(self.path, "output.cppia")
			args.append(self._output_path)
		elif self.target == "lua":
			args.append("--lua")
			self._output_path = os.path.join(self.path, "output.lua")
			args.append(self._output_path)
		elif self.target == "python":
			args.append("--python")
			self._output_path = os.path.join(self.path, "output.py")
			args.append(self._output_path)
		elif self.target == "c":
			args.append("--cpp")
			self._output_path = os.path.join(self.path, "output")
			args.append(self._output_path)

		for lib in self.haxelibs:
			args.append("-L")
			args.append(lib)

		for flag in self.custom_hxml_flags:
			args.append(flag)

		for res in resources:
			args.append("--resource")
			args.append(os.path.join(self.path, res) + "@" + Path(res).stem)
	
		if self.target == "eval":
			self._proc = ManagedProcess(
				"haxe",
				args,
				cwd=self.path
			)
			
			if self._on_start is not None:
				self._proc.on_start(self._on_start)

			if self._on_stdout is not None:
				self._proc.on_stdout(self._on_stdout)

			if self._on_stderr is not None:
				self._proc.on_stderr(self._on_stderr)

			if self._on_finish is not None:
				self._proc.on_finish(self._on_finish)
		else:
			self._compile_proc = ManagedProcess(
				"haxe",
				args,
				cwd=self.path
			)
			
			if self._on_stdout is not None:
				self._compile_proc.on_stdout(self._on_stdout)
			
			if self._on_stderr is not None:
				self._compile_proc.on_stderr(self._on_stderr)
			
			self._compile_proc.on_finish(self._on_compile_finish)

	def _on_compile_finish(self, exit_code: int):
		try:
			if exit_code != 0 or self._stopped_during_compile:
				if self._on_finish:
					self._on_finish(exit_code)
				return
			
			self._run_compiled_output()
		except Exception as e:
			if self._on_stderr:
				compiler = None
				addStr = ""

				if self.target == "javascript":
					targetName = "'node'"
				elif self.target == "neko":
					targetName = "'Neko VM'"
				elif self.target == "hashlink":
					targetName = "'Hashlink VM'"
				elif self.target == "cppia":
					targetName = "'HXCPP'"
				elif self.target == "lua":
					targetName = "'lua'"
				elif self.target == "python":
					targetName = "'python'"
				elif self.target == "c":
					targetName = "'HXCPP' and 'clang'"

				if targetName is not None:
					addStr = f"Do you have {targetName} installed?\n"

				self._on_stderr(f"Error during compilation: {str(e)}\n{addStr}")
			if self._on_finish:
				self._on_finish(1)

	def _run_compiled_output(self):
	
		if self.target == "javascript":
			runtime_cmd = "node"
			runtime_args = [self._output_path]
		elif self.target == "neko":
			runtime_cmd = "neko"
			runtime_args = [self._output_path]
		elif self.target == "hashlink":
			runtime_cmd = "hl"
			runtime_args = [self._output_path]
		elif self.target == "cppia":
			runtime_cmd = "haxelib"
			runtime_args = ["run", "hxcpp", self._output_path]
		elif self.target == "lua":
			runtime_cmd = find_lang_executable("lua")
			runtime_args = [self._output_path]
		elif self.target == "python":
			runtime_cmd = find_lang_executable("python")
			runtime_args = [self._output_path]
		elif self.target == "c":
			runtime_cmd = Path.joinpath(Path(self._output_path), self.main_class)
			runtime_args = []
		else:
			return

		self._proc = ManagedProcess(
			runtime_cmd,
			runtime_args,
			cwd=self.path
		)

		if self._on_start is not None:
			self._proc.on_start(self._on_start)

		if self._on_stdout is not None:
			self._proc.on_stdout(self._on_stdout)

		if self._on_stderr is not None:
			self._proc.on_stderr(self._on_stderr)

		if self._on_finish is not None:
			self._proc.on_finish(self._on_finish)

		self._proc.start()

	def run(self):
		if self.target == "eval":
			self._proc.start()
		else:
			self._compile_proc.start()

	def stop(self):
		if self._compile_proc is not None:
			self._stopped_during_compile = True
			self._compile_proc.stop()
		if self._proc is not None:
			self._proc.stop()

	def cleanup(self):
		if self._on_cleanup:
			self._on_cleanup()

		self.temp_dir.cleanup()


	def on_setup(self, func: Callable[[], None]):
		self._on_setup = func

	def on_cleanup(self, func: Callable[[], None]):
		self._on_cleanup = func

	def on_start(self, func: Callable[[], None]):
		self._on_start = func

	def on_stdout(self, func: Callable[[str], None]):
		self._on_stdout = func

	def on_stderr(self, func: Callable[[str], None]):
		self._on_stderr = func

	def on_finish(self, func: Callable[[int], None]):
		self._on_finish = func