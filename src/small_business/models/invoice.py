"""Invoice model."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from .enums import InvoiceStatus
from .line_item import LineItem
from .utils import generate_invoice_id, get_financial_year


class Invoice(BaseModel):
	"""Invoice for completed work."""

	invoice_id: str = Field(default_factory=generate_invoice_id)
	job_id: str | None = None
	client_id: str
	date_issued: date = Field(default_factory=date.today)
	date_due: date
	status: InvoiceStatus = InvoiceStatus.DRAFT
	payment_date: date | None = None
	payment_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
	payment_reference: str = ""
	line_items: list[LineItem] = Field(min_length=1)
	version: int = 1
	notes: str = ""

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on date_issued."""
		return get_financial_year(self.date_issued)

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
		"""Total invoice amount."""
		return sum((item.total for item in self.line_items), Decimal("0")).quantize(Decimal("0.01"))
