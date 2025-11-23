"""Settings storage and retrieval."""

from pathlib import Path

from small_business.models import Settings


def save_settings(settings: Settings, data_dir: Path) -> None:
	"""Save application settings.

	Args:
		settings: Settings to save
		data_dir: Root data directory

	Notes:
		Settings are stored in {data_dir}/settings.json
	"""
	data_dir = Path(data_dir)
	data_dir.mkdir(parents=True, exist_ok=True)

	settings_file = data_dir / "settings.json"
	settings_file.write_text(settings.model_dump_json(indent=2))


def load_settings(data_dir: Path) -> Settings:
	"""Load application settings.

	Args:
		data_dir: Root data directory

	Returns:
		Settings object, or default Settings if file doesn't exist

	Notes:
		If settings.json doesn't exist, returns Settings() with defaults.
	"""
	settings_file = Path(data_dir) / "settings.json"

	if not settings_file.exists():
		return Settings()

	settings_json = settings_file.read_text()
	return Settings.model_validate_json(settings_json)
