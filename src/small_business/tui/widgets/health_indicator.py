"""HealthIndicator widget — colour-coded status label."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class HealthIndicator(Static):
	"""Coloured health status: green (good), amber (attention), red (urgent)."""

	level: reactive[str] = reactive("good")

	LEVEL_STYLES = {
		"good": ("action-info", ""),
		"attention": ("action-warning", "!"),
		"urgent": ("action-urgent", "!!"),
	}

	def __init__(
		self,
		text: str = "",
		level: str = "good",
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)
		self._text = text
		self.level = level

	def set_text(self, text: str, level: str = "good") -> None:
		"""Update the text and level."""
		self._text = text
		self.level = level

	def watch_level(self, level: str) -> None:
		"""Update display when level changes."""
		css_class, icon = self.LEVEL_STYLES.get(level, ("action-info", ""))
		for cls in ("action-info", "action-warning", "action-urgent"):
			self.remove_class(cls)
		self.add_class(css_class)
		prefix = f" {icon} " if icon else "  "
		self.update(f"{prefix}{self._text}")
