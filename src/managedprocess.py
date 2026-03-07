import subprocess
import threading
from typing import Callable, Optional, List


class ManagedProcess:
	def __init__(self, executable: str, args: Optional[List[str]] = None, cwd: Optional[str] = None):
		self.executable = executable
		self.args = args or []
		self.cwd = cwd

		self._process: Optional[subprocess.Popen] = None
		self._exit_code: Optional[int] = None

		self._on_start: Optional[Callable[[], None]] = None
		self._on_stdout: Optional[Callable[[str], None]] = None
		self._on_stderr: Optional[Callable[[str], None]] = None
		self._on_finish: Optional[Callable[[int], None]] = None

		self._stdout_thread: Optional[threading.Thread] = None
		self._stderr_thread: Optional[threading.Thread] = None
		self._wait_thread: Optional[threading.Thread] = None

		self._lock = threading.Lock()

	# -----------------------------
	# Callback binding
	# -----------------------------

	def on_start(self, func: Callable[[], None]):
		self._on_start = func

	def on_stdout(self, func: Callable[[str], None]):
		self._on_stdout = func

	def on_stderr(self, func: Callable[[str], None]):
		self._on_stderr = func

	def on_finish(self, func: Callable[[int], None]):
		self._on_finish = func

	# -----------------------------
	# Process control
	# -----------------------------

	def start(self):
		if self._process is not None:
			raise RuntimeError("Process already started")

		self._process = subprocess.Popen(
			[self.executable] + self.args,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			bufsize=1,
			cwd=self.cwd
		)

		if self._on_start:
			self._on_start()

		self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
		self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
		self._wait_thread = threading.Thread(target=self._wait_for_exit, daemon=True)

		self._stdout_thread.start()
		self._stderr_thread.start()
		self._wait_thread.start()

	def stop(self):
		if self._process and self._process.poll() is None:
			self._process.terminate()

	def kill(self):
		if self._process and self._process.poll() is None:
			self._process.kill()

	def exit_code(self) -> Optional[int]:
		if self._process is None:
			return None
		return self._process.poll()

	def is_running(self) -> bool:
		return self.exit_code() is None

	# -----------------------------
	# Internal
	# -----------------------------

	def _read_stdout(self):
		if not self._process or not self._process.stdout:
			return

		for line in self._process.stdout:
			if self._on_stdout:
				self._on_stdout(line)

	def _read_stderr(self):
		if not self._process or not self._process.stderr:
			return

		for line in self._process.stderr:
			if self._on_stderr:
				self._on_stderr(line)

	def _wait_for_exit(self):
		if not self._process:
			return

		code = self._process.wait()

		with self._lock:
			self._exit_code = code

		if self._on_finish:
			self._on_finish(code)
