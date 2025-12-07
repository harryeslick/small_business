"""Tests for business initialization."""

import shutil
import tempfile
from pathlib import Path

import pytest

from small_business import init_business
from small_business.models import Settings


def test_init_business_creates_directory_structure():
	"""Test that init_business creates all required directories."""
	# Create temporary directory for testing
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		# Create settings
		settings = Settings(
			business_name="Test Business",
			business_abn="12 345 678 901",
			business_email="test@example.com",
		)

		# Initialize business
		business_dir = init_business(settings, base_path)

		# Verify business directory was created
		assert business_dir == base_path / "test_business"
		assert business_dir.exists()

		# Verify all subdirectories were created
		assert (business_dir / "clients").is_dir()
		assert (business_dir / "quotes").is_dir()
		assert (business_dir / "invoices").is_dir()
		assert (business_dir / "jobs").is_dir()
		assert (business_dir / "transactions").is_dir()
		assert (business_dir / "receipts").is_dir()
		assert (business_dir / "reports").is_dir()
		assert (business_dir / "config").is_dir()


def test_init_business_saves_settings():
	"""Test that settings are saved to config/settings.json."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		settings = Settings(
			business_name="Earthworks Studio",
			business_abn="98 765 432 109",
			business_email="hello@earthworks.studio",
			business_phone="0400 123 456",
		)

		business_dir = init_business(settings, base_path)

		# Verify settings file exists
		settings_file = business_dir / "config" / "settings.json"
		assert settings_file.exists()

		# Verify settings content
		loaded_settings = Settings.model_validate_json(settings_file.read_text())
		assert loaded_settings.business_name == "Earthworks Studio"
		assert loaded_settings.business_abn == "98 765 432 109"
		assert loaded_settings.business_email == "hello@earthworks.studio"
		assert loaded_settings.business_phone == "0400 123 456"


def test_init_business_copies_chart_of_accounts():
	"""Test that default chart of accounts is copied to config."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		settings = Settings(business_name="Test Business")

		business_dir = init_business(settings, base_path)

		# Verify chart of accounts file exists
		coa_file = business_dir / "config" / "chart_of_accounts.yaml"
		assert coa_file.exists()

		# Verify it contains valid YAML content
		content = coa_file.read_text()
		assert "asset:" in content or "- name: asset" in content
		assert "liability:" in content or "- name: liability" in content
		assert "income:" in content or "- name: income" in content
		assert "expense:" in content or "- name: expense" in content


def test_init_business_sanitizes_directory_name():
	"""Test that business name is sanitized for directory name."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		settings = Settings(business_name="Creative Canvas Studio")

		business_dir = init_business(settings, base_path)

		# Verify directory name is sanitized
		assert business_dir.name == "creative_canvas_studio"
		assert business_dir.exists()


def test_init_business_raises_error_if_directory_exists_with_content():
	"""Test that init_business raises error if directory already has content."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		settings = Settings(business_name="Test Business")

		# Initialize first time
		business_dir = init_business(settings, base_path)

		# Try to initialize again - should raise error
		with pytest.raises(FileExistsError, match="already exists and contains data"):
			init_business(settings, base_path)


def test_init_business_works_with_empty_existing_directory():
	"""Test that init_business works if directory exists but is empty."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)

		settings = Settings(business_name="Test Business")

		# Create empty directory
		business_dir = base_path / "test_business"
		business_dir.mkdir()

		# Should work since directory is empty
		result = init_business(settings, base_path)

		assert result == business_dir
		assert (business_dir / "config" / "settings.json").exists()


def test_init_business_uses_current_directory_by_default():
	"""Test that init_business uses current directory when path not provided."""
	# Create temporary directory and change to it
	with tempfile.TemporaryDirectory() as tmpdir:
		original_cwd = Path.cwd()
		try:
			# Change to temp directory
			import os

			os.chdir(tmpdir)

			settings = Settings(business_name="Test Business")

			# Call without path argument
			business_dir = init_business(settings)

			# Should create in current directory (resolve both to handle symlinks)
			assert business_dir.resolve() == (Path(tmpdir) / "test_business").resolve()
			assert business_dir.exists()

		finally:
			# Restore original working directory
			import os

			os.chdir(original_cwd)


def test_init_business_returns_path():
	"""Test that init_business returns the created business directory path."""
	with tempfile.TemporaryDirectory() as tmpdir:
		base_path = Path(tmpdir)
		settings = Settings(business_name="Test Business")

		result = init_business(settings, base_path)

		assert isinstance(result, Path)
		assert result == base_path / "test_business"
		assert result.exists()
