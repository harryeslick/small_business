"""Test workflow service functions for business entity lifecycle transitions."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from small_business.models import (
	Invoice,
	Job,
	JobStatus,
	LineItem,
	Quote,
	QuoteStatus,
)
from small_business.storage import StorageRegistry
from small_business.workflows import accept_quote_to_job, complete_job_to_invoice


# Fixtures


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
	"""Provide a temporary data directory."""
	return tmp_path


@pytest.fixture
def storage(data_dir: Path) -> StorageRegistry:
	"""Create storage registry with temporary data directory."""
	return StorageRegistry(data_dir)


@pytest.fixture
def sample_line_items() -> list[LineItem]:
	"""Create sample line items for quotes and invoices."""
	return [
		LineItem(
			description="Consulting services",
			quantity=Decimal("10"),
			unit_price=Decimal("150.00"),
		),
		LineItem(
			description="Travel expenses",
			quantity=Decimal("1"),
			unit_price=Decimal("200.00"),
		),
	]


@pytest.fixture
def sent_quote(storage: StorageRegistry, sample_line_items: list[LineItem]) -> Quote:
	"""Create and save a quote in SENT status."""
	quote = Quote(
		quote_id="Q-20251123-001",
		client_id="Woolworths",
		date_created=date(2025, 11, 23),
		date_sent=date(2025, 11, 24),
		date_valid_until=date(2026, 11, 23),
		line_items=sample_line_items,
	)
	storage.save_quote(quote)
	return quote


@pytest.fixture
def draft_quote(storage: StorageRegistry, sample_line_items: list[LineItem]) -> Quote:
	"""Create and save a quote in DRAFT status."""
	quote = Quote(
		quote_id="Q-20251123-002",
		client_id="Woolworths",
		date_created=date(2025, 11, 23),
		date_valid_until=date(2026, 11, 23),
		line_items=sample_line_items,
	)
	storage.save_quote(quote)
	return quote


@pytest.fixture
def completed_job(storage: StorageRegistry) -> Job:
	"""Create and save a job in COMPLETED status (with linked quote)."""
	# First save a quote so the job can reference it
	quote = Quote(
		quote_id="Q-20251123-003",
		client_id="Woolworths",
		date_created=date(2025, 11, 23),
		date_sent=date(2025, 11, 24),
		date_accepted=date(2025, 11, 25),
		date_valid_until=date(2026, 11, 23),
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10"),
				unit_price=Decimal("150.00"),
			),
		],
	)
	storage.save_quote(quote)

	job = Job(
		job_id="J-20251125-001",
		quote_id="Q-20251123-003",
		client_id="Woolworths",
		date_accepted=date(2025, 11, 25),
		date_started=date(2025, 11, 26),
		date_completed=date(2025, 12, 1),
	)
	storage.save_job(job)
	return job


# Tests for accept_quote_to_job


class TestAcceptQuoteToJob:
	"""Tests for accept_quote_to_job workflow function."""

	def test_accept_sent_quote_creates_job(
		self, data_dir: Path, sent_quote: Quote
	) -> None:
		"""Accepting a SENT quote creates a new job linked to the quote."""
		job = accept_quote_to_job(sent_quote.quote_id, data_dir)

		assert job.quote_id == sent_quote.quote_id
		assert job.client_id == sent_quote.client_id
		assert job.date_accepted == date.today()
		assert job.status == JobStatus.SCHEDULED

	def test_accept_quote_saves_accepted_quote_version(
		self, data_dir: Path, storage: StorageRegistry, sent_quote: Quote
	) -> None:
		"""Accepting a quote saves a new version with date_accepted set."""
		accept_quote_to_job(sent_quote.quote_id, data_dir)

		# Reload storage to check persisted data
		fresh_storage = StorageRegistry(data_dir)
		updated_quote = [
			q
			for q in fresh_storage.get_all_quotes(latest_only=True)
			if q.quote_id == sent_quote.quote_id
		][0]

		assert updated_quote.date_accepted == date.today()
		assert updated_quote.status == QuoteStatus.ACCEPTED

	def test_accept_quote_with_scheduled_date(
		self, data_dir: Path, sent_quote: Quote
	) -> None:
		"""Accepting a quote with a scheduled date sets it on the job."""
		scheduled = date(2026, 1, 15)
		job = accept_quote_to_job(sent_quote.quote_id, data_dir, scheduled_date=scheduled)

		assert job.scheduled_date == scheduled

	def test_accept_quote_persists_job(
		self, data_dir: Path, sent_quote: Quote
	) -> None:
		"""Accepted quote creates a job that is persisted in storage."""
		job = accept_quote_to_job(sent_quote.quote_id, data_dir)

		fresh_storage = StorageRegistry(data_dir)
		saved_jobs = fresh_storage.get_all_jobs(latest_only=True)
		assert len(saved_jobs) == 1
		assert saved_jobs[0].job_id == job.job_id

	def test_accept_draft_quote_raises_error(
		self, data_dir: Path, draft_quote: Quote
	) -> None:
		"""Cannot accept a quote that has not been sent."""
		with pytest.raises(ValueError, match="status is draft"):
			accept_quote_to_job(draft_quote.quote_id, data_dir)

	def test_accept_expired_quote_raises_error(
		self, data_dir: Path, storage: StorageRegistry, sample_line_items: list[LineItem]
	) -> None:
		"""Cannot accept an expired quote."""
		quote = Quote(
			quote_id="Q-20251123-010",
			client_id="Woolworths",
			date_created=date(2025, 1, 1),
			date_sent=date(2025, 1, 2),
			date_valid_until=date(2025, 1, 3),  # Already expired
			line_items=sample_line_items,
		)
		storage.save_quote(quote)

		with pytest.raises(ValueError, match="status is expired"):
			accept_quote_to_job(quote.quote_id, data_dir)

	def test_accept_rejected_quote_raises_error(
		self, data_dir: Path, storage: StorageRegistry, sample_line_items: list[LineItem]
	) -> None:
		"""Cannot accept a rejected quote."""
		quote = Quote(
			quote_id="Q-20251123-011",
			client_id="Woolworths",
			date_created=date(2025, 11, 23),
			date_sent=date(2025, 11, 24),
			date_rejected=date(2025, 11, 25),
			date_valid_until=date(2026, 11, 23),
			line_items=sample_line_items,
		)
		storage.save_quote(quote)

		with pytest.raises(ValueError, match="status is rejected"):
			accept_quote_to_job(quote.quote_id, data_dir)

	def test_accept_already_accepted_quote_raises_error(
		self, data_dir: Path, storage: StorageRegistry, sample_line_items: list[LineItem]
	) -> None:
		"""Cannot accept a quote that is already accepted."""
		quote = Quote(
			quote_id="Q-20251123-012",
			client_id="Woolworths",
			date_created=date(2025, 11, 23),
			date_sent=date(2025, 11, 24),
			date_accepted=date(2025, 11, 25),
			date_valid_until=date(2026, 11, 23),
			line_items=sample_line_items,
		)
		storage.save_quote(quote)

		with pytest.raises(ValueError, match="status is accepted"):
			accept_quote_to_job(quote.quote_id, data_dir)

	def test_accept_nonexistent_quote_raises_error(self, data_dir: Path) -> None:
		"""Accepting a non-existent quote raises FileNotFoundError."""
		with pytest.raises(FileNotFoundError, match="Quote not found"):
			accept_quote_to_job("Q-NONEXISTENT", data_dir)


# Tests for complete_job_to_invoice


class TestCompleteJobToInvoice:
	"""Tests for complete_job_to_invoice workflow function."""

	def test_invoice_completed_job_inherits_quote_line_items(
		self, data_dir: Path, completed_job: Job
	) -> None:
		"""Invoicing a completed job with no line_items uses the linked quote's line items."""
		invoice = complete_job_to_invoice(completed_job.job_id, data_dir)

		assert invoice.client_id == completed_job.client_id
		assert invoice.job_id == completed_job.job_id
		assert len(invoice.line_items) == 1
		assert invoice.line_items[0].description == "Consulting services"
		assert invoice.date_issued == date.today()
		assert invoice.date_due == date.today() + timedelta(days=30)

	def test_invoice_with_custom_line_items(
		self, data_dir: Path, completed_job: Job
	) -> None:
		"""Custom line items override the quote's line items."""
		custom_items = [
			LineItem(
				description="Custom work",
				quantity=Decimal("5"),
				unit_price=Decimal("300.00"),
			),
		]
		invoice = complete_job_to_invoice(
			completed_job.job_id, data_dir, line_items=custom_items
		)

		assert len(invoice.line_items) == 1
		assert invoice.line_items[0].description == "Custom work"
		assert invoice.line_items[0].unit_price == Decimal("300.00")

	def test_invoice_with_custom_due_days(
		self, data_dir: Path, completed_job: Job
	) -> None:
		"""Custom due_days changes the invoice due date."""
		invoice = complete_job_to_invoice(completed_job.job_id, data_dir, due_days=14)

		assert invoice.date_due == date.today() + timedelta(days=14)

	def test_invoice_marks_job_as_invoiced(
		self, data_dir: Path, completed_job: Job
	) -> None:
		"""Creating an invoice marks the job as invoiced."""
		complete_job_to_invoice(completed_job.job_id, data_dir)

		fresh_storage = StorageRegistry(data_dir)
		updated_job = [
			j
			for j in fresh_storage.get_all_jobs(latest_only=True)
			if j.job_id == completed_job.job_id
		][0]

		assert updated_job.date_invoiced == date.today()
		assert updated_job.status == JobStatus.INVOICED

	def test_invoice_persists_to_storage(
		self, data_dir: Path, completed_job: Job
	) -> None:
		"""Created invoice is persisted to storage."""
		invoice = complete_job_to_invoice(completed_job.job_id, data_dir)

		fresh_storage = StorageRegistry(data_dir)
		saved_invoices = fresh_storage.get_all_invoices(latest_only=True)
		assert len(saved_invoices) == 1
		assert saved_invoices[0].invoice_id == invoice.invoice_id

	def test_invoice_scheduled_job_raises_error(
		self, data_dir: Path, storage: StorageRegistry
	) -> None:
		"""Cannot invoice a job that is only SCHEDULED."""
		job = Job(
			job_id="J-20251125-010",
			client_id="Woolworths",
			date_accepted=date(2025, 11, 25),
		)
		storage.save_job(job)

		with pytest.raises(ValueError, match="status is scheduled"):
			complete_job_to_invoice(job.job_id, data_dir)

	def test_invoice_in_progress_job_raises_error(
		self, data_dir: Path, storage: StorageRegistry
	) -> None:
		"""Cannot invoice a job that is IN_PROGRESS."""
		job = Job(
			job_id="J-20251125-011",
			client_id="Woolworths",
			date_accepted=date(2025, 11, 25),
			date_started=date(2025, 11, 26),
		)
		storage.save_job(job)

		with pytest.raises(ValueError, match="status is in_progress"):
			complete_job_to_invoice(job.job_id, data_dir)

	def test_invoice_already_invoiced_job_raises_error(
		self, data_dir: Path, storage: StorageRegistry
	) -> None:
		"""Cannot invoice a job that is already INVOICED."""
		job = Job(
			job_id="J-20251125-012",
			client_id="Woolworths",
			date_accepted=date(2025, 11, 25),
			date_started=date(2025, 11, 26),
			date_completed=date(2025, 12, 1),
			date_invoiced=date(2025, 12, 2),
		)
		storage.save_job(job)

		with pytest.raises(ValueError, match="status is invoiced"):
			complete_job_to_invoice(job.job_id, data_dir)

	def test_invoice_job_without_quote_and_no_line_items_raises_error(
		self, data_dir: Path, storage: StorageRegistry
	) -> None:
		"""Cannot invoice a job with no linked quote and no provided line items."""
		job = Job(
			job_id="J-20251125-013",
			client_id="Woolworths",
			date_accepted=date(2025, 11, 25),
			date_started=date(2025, 11, 26),
			date_completed=date(2025, 12, 1),
		)
		storage.save_job(job)

		with pytest.raises(ValueError, match="no linked quote"):
			complete_job_to_invoice(job.job_id, data_dir)

	def test_invoice_job_without_quote_but_with_line_items(
		self, data_dir: Path, storage: StorageRegistry
	) -> None:
		"""Can invoice a job with no linked quote if line items are provided."""
		job = Job(
			job_id="J-20251125-014",
			client_id="Woolworths",
			date_accepted=date(2025, 11, 25),
			date_started=date(2025, 11, 26),
			date_completed=date(2025, 12, 1),
		)
		storage.save_job(job)

		custom_items = [
			LineItem(
				description="Ad-hoc work",
				quantity=Decimal("2"),
				unit_price=Decimal("500.00"),
			),
		]
		invoice = complete_job_to_invoice(job.job_id, data_dir, line_items=custom_items)

		assert invoice.client_id == "Woolworths"
		assert len(invoice.line_items) == 1
		assert invoice.line_items[0].description == "Ad-hoc work"

	def test_invoice_nonexistent_job_raises_error(self, data_dir: Path) -> None:
		"""Invoicing a non-existent job raises FileNotFoundError."""
		with pytest.raises(FileNotFoundError, match="Job not found"):
			complete_job_to_invoice("J-NONEXISTENT", data_dir)
