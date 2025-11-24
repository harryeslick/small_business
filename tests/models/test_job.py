"""Tests for Job model."""

from datetime import date

from small_business.models.enums import JobStatus
from small_business.models.job import Job


def test_job_with_quote():
	"""Test creating a job from a quote."""
	job = Job(
		job_id="J-20251115-001",
		quote_id="Q-20251115-001",
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		scheduled_date=date(2025, 12, 1),
	)
	assert job.job_id == "J-20251115-001"
	assert job.quote_id == "Q-20251115-001"
	assert job.client_id == "Test Client"
	assert job.status == JobStatus.SCHEDULED
	assert job.financial_year == "2025-26"


def test_job_without_quote():
	"""Test creating a job without a quote."""
	job = Job(
		job_id="J-20251115-002",
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
	)
	assert job.quote_id is None
	assert job.scheduled_date is None


def test_job_auto_generates_id():
	"""Test job ID auto-generation."""
	job = Job(client_id="Test Client", date_accepted=date(2025, 11, 15))
	assert job.job_id.startswith("J-")


def test_job_with_actual_costs():
	"""Test job with tracked transaction costs."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		actual_costs=["TXN-20251115-001", "TXN-20251115-002"],
	)
	assert len(job.actual_costs) == 2
	assert "TXN-20251115-001" in job.actual_costs


def test_job_status_scheduled():
	"""Test job status is SCHEDULED when not started."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		scheduled_date=date(2025, 12, 1),
	)
	assert job.status == JobStatus.SCHEDULED
	assert job.duration_days is None


def test_job_status_in_progress():
	"""Test job status is IN_PROGRESS when started but not completed."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		date_started=date(2025, 11, 20),
	)
	assert job.status == JobStatus.IN_PROGRESS
	assert job.duration_days is None


def test_job_status_completed():
	"""Test job status is COMPLETED when completed but not invoiced."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		date_started=date(2025, 11, 20),
		date_completed=date(2025, 11, 22),
	)
	assert job.status == JobStatus.COMPLETED
	assert job.duration_days == 2


def test_job_status_invoiced():
	"""Test job status is INVOICED when invoiced."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 15),
		date_started=date(2025, 11, 20),
		date_completed=date(2025, 11, 22),
		date_invoiced=date(2025, 11, 25),
	)
	assert job.status == JobStatus.INVOICED
	assert job.duration_days == 2


def test_job_duration_calculation():
	"""Test job duration_days calculation."""
	job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 1),
		date_started=date(2025, 11, 10),
		date_completed=date(2025, 11, 15),
	)
	assert job.duration_days == 5

	# Job without completion has None duration
	ongoing_job = Job(
		client_id="Test Client",
		date_accepted=date(2025, 11, 1),
		date_started=date(2025, 11, 10),
	)
	assert ongoing_job.duration_days is None
