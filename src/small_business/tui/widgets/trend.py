"""TrendIndicator widget — shows percentage change with coloured arrow."""

from __future__ import annotations

from decimal import Decimal

from textual.reactive import reactive
from textual.widgets import Static


class TrendIndicator(Static):
	"""Display a percentage change with up/down arrow and colour."""

	percent: reactive[Decimal] = reactive(Decimal(0))

	def __init__(
		self,
		percent: Decimal = Decimal(0),
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)
		self.percent = percent

	def watch_percent(self, percent: Decimal) -> None:
		"""Update display when percent changes."""
		self.remove_class("money-positive", "money-negative", "money-zero")
		if percent > 0:
			self.update(f"▲{percent:.0f}%")
			self.add_class("money-positive")
		elif percent < 0:
			self.update(f"▼{abs(percent):.0f}%")
			self.add_class("money-negative")
		else:
			self.update("—")
			self.add_class("money-zero")
