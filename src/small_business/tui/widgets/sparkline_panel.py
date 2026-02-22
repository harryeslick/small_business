"""SparklinePanel widget — shows a sparkline chart using Unicode block characters."""

from __future__ import annotations

from decimal import Decimal

from textual.reactive import reactive
from textual.widgets import Static

# Unicode block elements for sparkline rendering (8 levels)
_BLOCKS = " ▁▂▃▄▅▆▇█"


class SparklinePanel(Static):
	"""Display a sparkline chart with a title and optional value label.

	Uses Unicode block characters to render a mini bar chart.
	"""

	title: reactive[str] = reactive("")
	values: reactive[tuple] = reactive(())

	def __init__(
		self,
		title: str = "",
		values: list[Decimal] | None = None,
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)
		self.title = title
		if values:
			self.values = tuple(values)

	def watch_values(self, values: tuple) -> None:
		"""Re-render when values change."""
		self._render()

	def watch_title(self, title: str) -> None:
		"""Re-render when title changes."""
		self._render()

	def _render(self) -> None:
		"""Render the sparkline."""
		if not self.values:
			self.update(f"{self.title}: No data")
			return

		vals = [float(v) for v in self.values]
		min_val = min(vals)
		max_val = max(vals)
		val_range = max_val - min_val

		if val_range == 0:
			# All values are the same
			bars = _BLOCKS[4] * len(vals)
		else:
			bars = ""
			for v in vals:
				# Normalize to 0-8 range
				level = int(((v - min_val) / val_range) * 8)
				level = max(0, min(8, level))
				bars += _BLOCKS[level]

		latest = vals[-1] if vals else 0
		self.update(f"{self.title}: {bars} (${latest:,.0f})")
