"""Invoice model."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

from .enums import InvoiceStatus
from .line_item import LineItem
from .utils import generate_invoice_id, get_financial_year


class Invoice(BaseModel):
	"""Invoice for completed work.

	Status is derived from date fields:
	- DRAFT: No date_issued
	- SENT: date_issued set, not paid/cancelled, not overdue
	- OVERDUE: date_issued set, date.today() > date_due, not paid/cancelled
	- PAID: date_paid set
	- CANCELLED: date_cancelled set
	"""

	invoice_id: str = Field(default_factory=generate_invoice_id)
	job_id: str | None = None
	client_id: str
	date_created: date = Field(default_factory=date.today)
	date_issued: date | None = None
	date_due: date
	date_paid: date | None = None
	date_cancelled: date | None = None
	payment_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
	payment_reference: str = ""
	line_items: list[LineItem] = Field(min_length=1)
	version: int = 1
	notes: str = ""

	@computed_field
	@property
	def status(self) -> InvoiceStatus:
		"""Derive status from date fields."""
		if self.date_cancelled:
			return InvoiceStatus.CANCELLED
		if self.date_paid:
			return InvoiceStatus.PAID
		if self.date_issued:
			if date.today() > self.date_due:
				return InvoiceStatus.OVERDUE
			return InvoiceStatus.SENT
		return InvoiceStatus.DRAFT

	@computed_field
	@property
	def days_outstanding(self) -> int | None:
		"""Days since invoice was issued (if sent and not paid)."""
		if self.date_issued and not self.date_paid and not self.date_cancelled:
			return (date.today() - self.date_issued).days
		return None

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on date_issued or date_created."""
		return get_financial_year(self.date_issued or self.date_created)

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
