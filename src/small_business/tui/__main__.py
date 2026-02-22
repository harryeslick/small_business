"""Entry point for the Small Business Manager TUI.

Usage:
    python -m small_business.tui [DATA_DIR]
    small-business [DATA_DIR]
"""

from __future__ import annotations

import sys
from pathlib import Path

from small_business.tui.app import SmallBusinessApp


def main() -> None:
	"""Launch the Small Business Manager TUI."""
	data_dir: Path | None = None

	if len(sys.argv) > 1:
		data_dir = Path(sys.argv[1]).expanduser().resolve()
		if not data_dir.exists():
			print(f"Warning: Data directory '{data_dir}' does not exist.")
			print("The setup wizard will guide you through creating a new business.\n")
			data_dir = None

	app = SmallBusinessApp(data_dir=data_dir)
	app.run()


if __name__ == "__main__":
	main()
