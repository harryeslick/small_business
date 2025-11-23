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
