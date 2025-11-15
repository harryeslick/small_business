"""Transaction and JournalEntry models."""

import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field, model_validator

from .utils import generate_transaction_id, get_financial_year


class JournalEntry(BaseModel):
	"""Individual journal entry (debit or credit)."""

	account_code: str
	debit: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2)
	credit: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2)

	@model_validator(mode="after")
	def check_debit_or_credit(self):
		"""Ensure exactly one of debit or credit is non-zero."""
		if self.debit > 0 and self.credit > 0:
			raise ValueError("Entry cannot have both debit and credit")
		if self.debit == 0 and self.credit == 0:
			raise ValueError("Entry must have either debit or credit")
		return self


class Transaction(BaseModel):
	"""Transaction with double-entry journal entries."""

	transaction_id: str = Field(default_factory=generate_transaction_id)
	date: datetime.date = Field(default_factory=datetime.date.today)
	description: str = Field(min_length=1)
	entries: list[JournalEntry] = Field(min_length=2)
	receipt_path: str | None = None
	gst_inclusive: bool = False
	notes: str = ""

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on transaction date."""
		return get_financial_year(self.date)

	@model_validator(mode="after")
	def check_balanced(self):
		"""Ensure total debits equal total credits."""
		total_debits = sum(entry.debit for entry in self.entries)
		total_credits = sum(entry.credit for entry in self.entries)

		if total_debits != total_credits:
			raise ValueError(
				f"Transaction not balanced: debits={total_debits}, credits={total_credits}"
			)

		return self

	@computed_field
	@property
	def amount(self) -> Decimal:
		"""Transaction amount (total debits or credits)."""
		return sum((entry.debit for entry in self.entries), Decimal("0")).quantize(Decimal("0.01"))
