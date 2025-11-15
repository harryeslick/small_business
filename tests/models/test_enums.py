"""Tests for status enums."""

from small_business.models.enums import (
	AccountType,
	InvoiceStatus,
	JobStatus,
	QuoteStatus,
)


def test_quote_status_has_all_values():
	"""Test QuoteStatus enum has all required status values."""
	assert QuoteStatus.DRAFT.value == "draft"
	assert QuoteStatus.SENT.value == "sent"
	assert QuoteStatus.ACCEPTED.value == "accepted"
	assert QuoteStatus.REJECTED.value == "rejected"
	assert QuoteStatus.EXPIRED.value == "expired"


def test_job_status_has_all_values():
	"""Test JobStatus enum has all required status values."""
	assert JobStatus.SCHEDULED.value == "scheduled"
	assert JobStatus.IN_PROGRESS.value == "in_progress"
	assert JobStatus.COMPLETED.value == "completed"
	assert JobStatus.INVOICED.value == "invoiced"


def test_invoice_status_has_all_values():
	"""Test InvoiceStatus enum has all required status values."""
	assert InvoiceStatus.DRAFT.value == "draft"
	assert InvoiceStatus.SENT.value == "sent"
	assert InvoiceStatus.PAID.value == "paid"
	assert InvoiceStatus.OVERDUE.value == "overdue"
	assert InvoiceStatus.CANCELLED.value == "cancelled"


def test_account_type_has_all_values():
	"""Test AccountType enum has all required account types."""
	assert AccountType.ASSET.value == "asset"
	assert AccountType.LIABILITY.value == "liability"
	assert AccountType.EQUITY.value == "equity"
	assert AccountType.INCOME.value == "income"
	assert AccountType.EXPENSE.value == "expense"


def test_enums_serialize_as_strings():
	"""Test that enums serialize to JSON as strings."""
	# Enums that inherit from str should serialize as strings
	assert isinstance(QuoteStatus.DRAFT.value, str)
	assert isinstance(JobStatus.SCHEDULED.value, str)
	assert isinstance(InvoiceStatus.DRAFT.value, str)
	assert isinstance(AccountType.ASSET.value, str)
