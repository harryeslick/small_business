"""First-time setup wizard modal for new business initialization."""

from __future__ import annotations

import shutil
from importlib.resources import files
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from small_business.models import Settings


class SetupWizardModal(ModalScreen[Path | None]):
	"""Modal wizard for first-time business setup.

	When init_dir is provided, initializes that directory in place
	(for the `small-business init` workflow). Otherwise, creates a
	subdirectory using init_business().

	Returns the created data_dir Path on success, or None if cancelled.
	"""

	DEFAULT_CSS = """
	SetupWizardModal {
		align: center middle;
	}

	#wizard-dialog {
		width: 65;
		height: auto;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
	}

	#wizard-title {
		text-style: bold;
		text-align: center;
		width: 100%;
		margin-bottom: 1;
	}

	#wizard-subtitle {
		text-align: center;
		color: $text-muted;
		width: 100%;
		margin-bottom: 1;
	}

	.wizard-field {
		margin-bottom: 1;
		height: auto;
	}

	.wizard-label {
		margin-bottom: 0;
	}

	#wizard-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#wizard-buttons Button {
		margin: 0 1;
	}

	#wizard-error {
		color: #ff1744;
		text-align: center;
		height: auto;
	}
	"""

	def __init__(self, init_dir: Path | None = None) -> None:
		super().__init__()
		self._init_dir = init_dir

	def compose(self) -> ComposeResult:
		with Vertical(id="wizard-dialog"):
			yield Static("Small Business Manager", id="wizard-title")
			yield Static("Set up your business to get started.", id="wizard-subtitle")

			with Vertical(classes="wizard-field"):
				yield Label("Business Name", classes="wizard-label")
				yield Input(placeholder="e.g. Earthworks Studio", id="business-name")

			with Vertical(classes="wizard-field"):
				yield Label("ABN (optional)", classes="wizard-label")
				yield Input(placeholder="e.g. 12 345 678 901", id="business-abn")

			with Vertical(classes="wizard-field"):
				yield Label("Email (optional)", classes="wizard-label")
				yield Input(placeholder="e.g. hello@example.com", id="business-email")

			with Vertical(classes="wizard-field"):
				yield Label("Phone (optional)", classes="wizard-label")
				yield Input(placeholder="e.g. 0412 345 678", id="business-phone")

			with Vertical(classes="wizard-field"):
				yield Label("Business Address (optional)", classes="wizard-label")
				yield Input(placeholder="e.g. 123 Main St, Sydney NSW 2000", id="business-address")

			if self._init_dir:
				yield Static(
					f"  Business folder: [bold]{self._init_dir}[/]",
					id="wizard-location",
				)

			yield Static("", id="wizard-error")

			with Vertical(id="wizard-buttons"):
				yield Button("Create Business", variant="primary", id="btn-create")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-create":
			self._create_business()

	def _create_business(self) -> None:
		"""Validate inputs and create the business."""
		name = self.query_one("#business-name", Input).value.strip()
		if not name:
			self.query_one("#wizard-error", Static).update("Business name is required.")
			return

		settings = Settings(
			business_name=name,
			business_abn=self.query_one("#business-abn", Input).value.strip(),
			business_email=self.query_one("#business-email", Input).value.strip(),
			business_phone=self.query_one("#business-phone", Input).value.strip(),
			business_address=self.query_one("#business-address", Input).value.strip(),
		)

		try:
			if self._init_dir:
				# Initialize the given directory in place
				created_path = _init_business_in_place(settings, self._init_dir)
			else:
				# Legacy mode: create a subdirectory
				from small_business.init_business import init_business

				created_path = init_business(settings)
			self.dismiss(created_path)
		except FileExistsError:
			self.query_one("#wizard-error", Static).update(
				"Business directory already exists. Choose a different location or name."
			)
		except Exception as e:
			self.query_one("#wizard-error", Static).update(f"Error: {e}")


def _init_business_in_place(settings: Settings, path: Path) -> Path:
	"""Initialize a business directly in the given directory (no subdirectory).

	Creates the standard business directory structure inside `path`.
	"""
	path.mkdir(parents=True, exist_ok=True)

	for subdir in (
		"clients",
		"quotes",
		"invoices",
		"jobs",
		"transactions",
		"receipts",
		"reports",
		"config",
	):
		(path / subdir).mkdir(exist_ok=True)

	# Save settings
	settings_path = path / "config" / "settings.json"
	settings_path.write_text(settings.model_dump_json(indent=2))

	# Copy default chart of accounts
	default_coa = files("small_business.data").joinpath("default_chart_of_accounts.yaml")
	shutil.copy(str(default_coa), path / "config" / "chart_of_accounts.yaml")

	return path
