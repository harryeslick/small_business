"""Status enums for workflow entities."""

from enum import Enum


class QuoteStatus(str, Enum):
	"""Quote status values."""

	DRAFT = "draft"
	SENT = "sent"
	ACCEPTED = "accepted"
	REJECTED = "rejected"
	EXPIRED = "expired"


class JobStatus(str, Enum):
	"""Job status values."""

	SCHEDULED = "scheduled"
	IN_PROGRESS = "in_progress"
	COMPLETED = "completed"
	INVOICED = "invoiced"


class InvoiceStatus(str, Enum):
	"""Invoice status values."""

	DRAFT = "draft"
	SENT = "sent"
	PAID = "paid"
	OVERDUE = "overdue"
	CANCELLED = "cancelled"


class AccountType(str, Enum):
	"""Account type values."""

	ASSET = "asset"
	LIABILITY = "liability"
	EQUITY = "equity"
	INCOME = "income"
	EXPENSE = "expense"
