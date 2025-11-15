"""Quote model."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from .enums import QuoteStatus
from .line_item import LineItem
from .utils import generate_quote_id, get_financial_year


class Quote(BaseModel):
	"""Quote/proposal for client work."""

	quote_id: str = Field(default_factory=generate_quote_id)
	client_id: str
	date_created: date = Field(default_factory=date.today)
	date_valid_until: date
	status: QuoteStatus = QuoteStatus.DRAFT
	line_items: list[LineItem] = Field(min_length=1)
	terms_and_conditions: str = ""
	version: int = 1
	notes: str = ""

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on date_created."""
		return get_financial_year(self.date_created)

	@computed_field
	@property
	def subtotal(self) -> Decimal:
		"""Sum of all line item subtotals."""
		return sum((item.subtotal for item in self.line_items), Decimal("0")).quantize(
			Decimal("0.01")
		)

	@computed_field
	@property
	def gst_amount(self) -> Decimal:
		"""Sum of all line item GST amounts."""
		return sum((item.gst_amount for item in self.line_items), Decimal("0")).quantize(
			Decimal("0.01")
		)

	@computed_field
	@property
	def total(self) -> Decimal:
		"""Total quote amount."""
		return sum((item.total for item in self.line_items), Decimal("0")).quantize(
			Decimal("0.01")
		)
