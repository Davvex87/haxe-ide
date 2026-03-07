"""Resource location helper.

Provides `resource_path(*parts)` which returns a Path to a resource whether the
app is running from source or frozen with PyInstaller.
"""
from pathlib import Path
import sys

def project_root() -> Path:
	if getattr(sys, "frozen", False):
		# PyInstaller extracts bundled files to sys._MEIPASS at runtime
		return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)).resolve()
	# Source layout: src/resources.py -> project root is the parent of src/
	return Path(__file__).parent.parent.resolve()

def resource_path(*parts) -> Path:
	"""Return an absolute Path to a resource inside the project.

	Example: resource_path('examples', 'Hello world.json')
	"""
	return project_root().joinpath(*parts)
