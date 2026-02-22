"""NotificationBar widget — docked bar showing the most urgent notification."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class NotificationBar(Static):
	"""A bar docked below the header showing the most urgent notification.

	Cycles through multiple notifications. Dismissible.
	"""

	DEFAULT_CSS = """
	NotificationBar {
		height: 1;
		width: 100%;
		background: $primary 15%;
		color: $text;
		padding: 0 2;
	}

	NotificationBar.hidden {
		display: none;
	}

	NotificationBar.urgent {
		background: #ff1744 15%;
	}

	NotificationBar.warning {
		background: #ffab00 15%;
	}
	"""

	notifications: reactive[tuple] = reactive(())

	def __init__(
		self,
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=f"hidden {classes}" if classes else "hidden")
		self._index = 0

	def set_notifications(self, items: list[tuple[str, str]]) -> None:
		"""Set notification items. Each is (message, level) where level is 'info'|'warning'|'urgent'."""
		self.notifications = tuple(items)

	def watch_notifications(self, notifications: tuple) -> None:
		"""Update display when notifications change."""
		if not notifications:
			self.add_class("hidden")
			return

		self.remove_class("hidden")
		self._index = 0
		self._show_current()

	def _show_current(self) -> None:
		"""Display the current notification."""
		if not self.notifications:
			return

		idx = self._index % len(self.notifications)
		message, level = self.notifications[idx]

		self.remove_class("urgent", "warning")
		if level == "urgent":
			self.add_class("urgent")
		elif level == "warning":
			self.add_class("warning")

		count = len(self.notifications)
		indicator = f" [{idx + 1}/{count}] " if count > 1 else " "
		self.update(f"{indicator}{message}")

	def action_next(self) -> None:
		"""Cycle to next notification."""
		if self.notifications:
			self._index = (self._index + 1) % len(self.notifications)
			self._show_current()

	def action_dismiss(self) -> None:
		"""Hide the notification bar."""
		self.add_class("hidden")
