"""Entry point for the Small Business Manager TUI.

Usage:
    small-business              Open the app (from within your business folder)
    small-business init         Set up a new business in the current folder
    small-business /path/to/dir Open the app with a specific business folder
"""

from __future__ import annotations

import sys
from pathlib import Path

from small_business.tui.app import SmallBusinessApp


def _is_business_dir(path: Path) -> bool:
	"""Check if a directory looks like an initialized business folder.

	Looks for the config/settings.json file created by init_business(),
	or the settings.json file used by StorageRegistry.
	"""
	return (path / "config" / "settings.json").exists() or (path / "settings.json").exists()


def main() -> None:
	"""Launch the Small Business Manager TUI."""
	args = sys.argv[1:]

	# small-business init — set up current directory as a new business
	if args and args[0] == "init":
		_run_init()
		return

	# small-business /path — explicit business directory
	if args and args[0] not in ("--help", "-h"):
		data_dir = Path(args[0]).expanduser().resolve()
		if not data_dir.exists():
			print(f"Error: '{data_dir}' does not exist.")
			sys.exit(1)
		if not _is_business_dir(data_dir):
			print(f"Error: '{data_dir}' is not a business folder.")
			print(f"Run 'cd {data_dir} && small-business init' to set one up.")
			sys.exit(1)
		app = SmallBusinessApp(data_dir=data_dir)
		app.run()
		return

	if args and args[0] in ("--help", "-h"):
		_print_help()
		return

	# small-business (no args) — use current directory
	cwd = Path.cwd()
	if _is_business_dir(cwd):
		app = SmallBusinessApp(data_dir=cwd)
		app.run()
	else:
		print("This folder is not a business directory.\n")
		print("To set up a new business here:")
		print("  small-business init\n")
		print("Or open an existing business:")
		print("  cd /path/to/your/business")
		print("  small-business")
		sys.exit(1)


def _run_init() -> None:
	"""Initialize the current directory as a business folder via the setup wizard."""
	cwd = Path.cwd()

	if _is_business_dir(cwd):
		print(f"This folder is already a business directory: {cwd}")
		print("Run 'small-business' to open it.")
		sys.exit(1)

	# Launch the app without a data_dir — triggers the setup wizard
	# The wizard will initialize CWD
	app = SmallBusinessApp(data_dir=None, init_dir=cwd)
	app.run()


def _print_help() -> None:
	"""Print usage help."""
	print("Small Business Manager — accounting for Australian sole traders\n")
	print("Usage:")
	print("  small-business              Open the app (from your business folder)")
	print("  small-business init         Set up a new business in the current folder")
	print("  small-business /path/to/dir Open a specific business folder")
	print()
	print("First time? Create a folder for your business, then:")
	print("  mkdir 'My Business'")
	print("  cd 'My Business'")
	print("  small-business init")


if __name__ == "__main__":
	main()
