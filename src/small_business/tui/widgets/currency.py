"""CurrencyDisplay widget — formats Decimal as coloured Australian currency."""

from __future__ import annotations

from decimal import Decimal

from textual.reactive import reactive
from textual.widgets import Label

from small_business.tui.utils import format_currency


class CurrencyDisplay(Label):
	"""Display a monetary value with colour coding.

	Green for positive, red for negative, muted for zero.
	"""

	amount: reactive[Decimal] = reactive(Decimal(0))
	show_sign: reactive[bool] = reactive(False)

	def __init__(
		self,
		amount: Decimal = Decimal(0),
		*,
		show_sign: bool = False,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)
		self.amount = amount
		self.show_sign = show_sign

	def watch_amount(self, amount: Decimal) -> None:
		"""Update display when amount changes."""
		self.update(format_currency(amount, show_sign=self.show_sign))
		self.remove_class("money-positive", "money-negative", "money-zero")
		if amount > 0:
			self.add_class("money-positive")
		elif amount < 0:
			self.add_class("money-negative")
		else:
			self.add_class("money-zero")

	def watch_show_sign(self, show_sign: bool) -> None:
		"""Re-render when show_sign changes."""
		self.watch_amount(self.amount)
