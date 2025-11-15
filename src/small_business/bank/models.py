"""Bank import data models."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class BankTransaction(BaseModel):
	"""Single bank transaction from CSV import."""

	date: date
	description: str = Field(min_length=1)
	debit: Decimal = Field(ge=0, decimal_places=2)
	credit: Decimal = Field(ge=0, decimal_places=2)
	balance: Decimal | None = Field(default=None, decimal_places=2)

	@computed_field
	@property
	def amount(self) -> Decimal:
		"""Net amount (credit - debit)."""
		return (self.credit - self.debit).quantize(Decimal("0.01"))

	@computed_field
	@property
	def is_debit(self) -> bool:
		"""True if transaction is a debit (outgoing)."""
		return self.debit > 0


class ImportedBankStatement(BaseModel):
	"""Collection of imported bank transactions."""

	bank_name: str = Field(min_length=1)
	account_name: str = Field(min_length=1)
	import_date: date = Field(default_factory=date.today)
	transactions: list[BankTransaction] = Field(default_factory=list)
