#!/usr/bin/env python3

# I have no idea wtf is going on here, all I know is that OpenCode cooked and it works so I'm not going to touch it lol


"""
Small launcher to run the app from project root while keeping `src/` on
the import path so imports like `import haxe` work and resource paths
resolve to the project root.

Usage:
  python run.py

This is the recommended quick way to test the app during development.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
SRC = ROOT.joinpath("src")

if str(SRC) not in sys.path:
	# Put src at front so local modules are preferred over site packages
	sys.path.insert(0, str(SRC))

# Run the main module
import main  # noqa: E402

if __name__ == "__main__":
	# If main defines a `main` entrypoint function later, call it; otherwise
	# the module's top-level `if __name__ == '__main__'` will run when
	# executed as a script, but importing won't trigger it. We call run()
	# by creating the App instance as main.py expects.
	try:
		# Prefer `main.Application.run()` if the module set it up already
		if hasattr(main, "Application") and main.Application is not None:
			main.Application.run()
		else:
			# Fallback: try to invoke the module as a script
			# Some modules implement a `main()` function
			if hasattr(main, "main"):
				main.main()
			else:
				# Last resort: re-execute the module as a script
				import runpy
				runpy.run_module("main", run_name="__main__")
	except Exception:
		raise
