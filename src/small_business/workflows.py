"""Workflow service functions for business entity lifecycle transitions.

These functions orchestrate transitions between business entities:
- Quote -> Job (accept_quote_to_job)
- Job -> Invoice (complete_job_to_invoice)

Each function auto-loads dependencies from the StorageRegistry,
validates preconditions, and persists the results.
"""

from datetime import date, timedelta
from pathlib import Path

from small_business.models import Invoice, Job, LineItem, Quote, QuoteStatus, JobStatus
from small_business.storage.registry import StorageRegistry


def _get_latest_quote(storage: StorageRegistry, quote_id: str) -> Quote:
	"""Get the latest version of a quote by ID.

	Args:
		storage: StorageRegistry instance
		quote_id: Quote identifier

	Returns:
		Latest version of the quote

	Raises:
		FileNotFoundError: If quote not found
	"""
	quotes = [q for q in storage.get_all_quotes(latest_only=True) if q.quote_id == quote_id]
	if not quotes:
		raise FileNotFoundError(f"Quote not found: {quote_id}")
	return quotes[0]


def _get_latest_job(storage: StorageRegistry, job_id: str) -> Job:
	"""Get the latest version of a job by ID.

	Args:
		storage: StorageRegistry instance
		job_id: Job identifier

	Returns:
		Latest version of the job

	Raises:
		FileNotFoundError: If job not found
	"""
	jobs = [j for j in storage.get_all_jobs(latest_only=True) if j.job_id == job_id]
	if not jobs:
		raise FileNotFoundError(f"Job not found: {job_id}")
	return jobs[0]


def accept_quote_to_job(
	quote_id: str,
	data_dir: Path,
	scheduled_date: date | None = None,
) -> Job:
	"""Accept a quote and create a job from it.

	Validates the quote is in an acceptable state (SENT status),
	sets date_accepted on the quote, saves a new quote version,
	then creates and saves a new Job linked to the quote.

	Args:
		quote_id: ID of the quote to accept
		data_dir: Base directory for data storage
		scheduled_date: Optional scheduled date for the job

	Returns:
		The newly created Job

	Raises:
		FileNotFoundError: If quote not found
		ValueError: If quote cannot be accepted (wrong status)
	"""
	storage = StorageRegistry(data_dir)

	quote = _get_latest_quote(storage, quote_id)

	if quote.status != QuoteStatus.SENT:
		raise ValueError(
			f"Quote {quote_id} cannot be accepted: status is {quote.status.value} "
			f"(must be {QuoteStatus.SENT.value})"
		)

	# Update quote with acceptance date and save new version
	accepted_quote = quote.model_copy(update={"date_accepted": date.today()})
	storage.save_quote(accepted_quote)

	# Create job from the accepted quote
	job = Job(
		client_id=quote.client_id,
		quote_id=quote.quote_id,
		date_accepted=date.today(),
		scheduled_date=scheduled_date,
	)
	storage.save_job(job)

	return job


def complete_job_to_invoice(
	job_id: str,
	data_dir: Path,
	line_items: list[LineItem] | None = None,
	due_days: int = 30,
) -> Invoice:
	"""Create an invoice from a completed job.

	Validates the job is in COMPLETED status (date_completed set, not yet invoiced),
	creates an invoice with line items (from the linked quote if not provided),
	and marks the job as invoiced.

	Args:
		job_id: ID of the job to invoice
		data_dir: Base directory for data storage
		line_items: Optional line items for the invoice (defaults to quote's line items)
		due_days: Number of days until invoice is due (default: 30)

	Returns:
		The newly created Invoice

	Raises:
		FileNotFoundError: If job not found, or linked quote not found when line_items not provided
		ValueError: If job cannot be invoiced (wrong status or no line items available)
	"""
	storage = StorageRegistry(data_dir)

	job = _get_latest_job(storage, job_id)

	if job.status != JobStatus.COMPLETED:
		raise ValueError(
			f"Job {job_id} cannot be invoiced: status is {job.status.value} "
			f"(must be {JobStatus.COMPLETED.value})"
		)

	# Resolve line items: use provided, or fall back to linked quote
	if line_items is None:
		if job.quote_id is None:
			raise ValueError(
				f"Job {job_id} has no linked quote and no line_items were provided"
			)
		quote = _get_latest_quote(storage, job.quote_id)
		line_items = quote.line_items

	# Create invoice
	today = date.today()
	invoice = Invoice(
		job_id=job.job_id,
		client_id=job.client_id,
		date_issued=today,
		date_due=today + timedelta(days=due_days),
		line_items=line_items,
	)
	storage.save_invoice(invoice)

	# Mark job as invoiced
	invoiced_job = job.model_copy(update={"date_invoiced": today})
	storage.update_job(invoiced_job)

	return invoice
