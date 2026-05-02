"""Quote model."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from .enums import QuoteStatus
from .line_item import LineItem
from .utils import generate_quote_id, get_financial_year


class Quote(BaseModel):
	"""Quote/proposal for client work.

	Status is derived from date fields:
	- DRAFT: No date_sent
	- SENT: date_sent set, not accepted/rejected, not expired
	- ACCEPTED: date_accepted set
	- REJECTED: date_rejected set
	- EXPIRED: date.today() > date_valid_until and not accepted/rejected
	"""

	quote_id: str = Field(default_factory=generate_quote_id)
	client_id: str
	date_created: date = Field(default_factory=date.today)
	date_sent: date | None = None
	date_accepted: date | None = None
	date_rejected: date | None = None
	date_valid_until: date
	line_items: list[LineItem] = Field(min_length=1)
	terms_and_conditions: str = ""
	version: int = 1
	notes: str = ""

	@computed_field
	@property
	def status(self) -> QuoteStatus:
		"""Derive status from date fields."""
		if self.date_accepted:
			return QuoteStatus.ACCEPTED
		if self.date_rejected:
			return QuoteStatus.REJECTED
		if date.today() > self.date_valid_until:
			return QuoteStatus.EXPIRED
		if self.date_sent:
			return QuoteStatus.SENT
		return QuoteStatus.DRAFT

	@computed_field
	@property
	def is_active(self) -> bool:
		"""Whether quote can still be accepted."""
		return self.status in (QuoteStatus.DRAFT, QuoteStatus.SENT)

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
		return sum((item.total for item in self.line_items), Decimal("0")).quantize(Decimal("0.01"))
