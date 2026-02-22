"""Generic confirmation modal."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmModal(ModalScreen[bool]):
	"""A reusable yes/no confirmation dialog.

	Returns True if confirmed, False if cancelled.
	"""

	DEFAULT_CSS = """
	ConfirmModal {
		align: center middle;
	}

	#confirm-dialog {
		width: 50;
		height: auto;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
	}

	#confirm-title {
		text-style: bold;
		text-align: center;
		width: 100%;
		margin-bottom: 1;
	}

	#confirm-message {
		text-align: center;
		width: 100%;
		margin-bottom: 1;
	}

	#confirm-buttons {
		height: auto;
		align-horizontal: center;
	}

	#confirm-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(
		self,
		title: str = "Confirm",
		message: str = "Are you sure?",
		confirm_label: str = "Confirm",
		cancel_label: str = "Cancel",
	) -> None:
		super().__init__()
		self._title = title
		self._message = message
		self._confirm_label = confirm_label
		self._cancel_label = cancel_label

	def compose(self) -> ComposeResult:
		with Vertical(id="confirm-dialog"):
			yield Static(self._title, id="confirm-title")
			yield Static(self._message, id="confirm-message")
			with Horizontal(id="confirm-buttons"):
				yield Button(self._confirm_label, variant="primary", id="btn-confirm")
				yield Button(self._cancel_label, variant="default", id="btn-cancel")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		self.dismiss(event.button.id == "btn-confirm")
