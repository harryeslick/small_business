"""Tests for StorageRegistry enhancements: Jobs, ChartOfAccounts, BankFormats, and transaction features."""

import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import (
	Account,
	BankFormat,
	BankFormats,
	ChartOfAccounts,
	Client,
	Invoice,
	Job,
	JournalEntry,
	LineItem,
	Quote,
	Settings,
	Transaction,
)
from small_business.models.enums import AccountType, JobStatus
from small_business.storage import StorageRegistry


# Fixtures


@pytest.fixture
def storage(tmp_path: Path) -> StorageRegistry:
	"""Create storage registry with temporary data directory."""
	return StorageRegistry(tmp_path)


@pytest.fixture
def sample_job() -> Job:
	"""Create a sample job for testing."""
	return Job(
		job_id="J-20251123-001",
		client_id="Woolworths",
		date_accepted=date(2025, 11, 23),
		scheduled_date=date(2025, 12, 1),
		notes="Sample job",
	)


@pytest.fixture
def sample_transaction() -> Transaction:
	"""Create a sample transaction for testing."""
	return Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 23),
		description="Payment received",
		entries=[
			JournalEntry(account_code="1100", debit=Decimal("1000.00"), credit=Decimal("0")),
			JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("1000.00")),
		],
	)


@pytest.fixture
def sample_chart_of_accounts() -> ChartOfAccounts:
	"""Create a sample chart of accounts."""
	return ChartOfAccounts(
		accounts=[
			Account(name="Bank Account", account_type=AccountType.ASSET),
			Account(name="Accounts Receivable", account_type=AccountType.ASSET),
			Account(name="Revenue", account_type=AccountType.INCOME),
			Account(name="Office Supplies", account_type=AccountType.EXPENSE),
		]
	)


@pytest.fixture
def sample_bank_formats() -> BankFormats:
	"""Create sample bank formats."""
	return BankFormats(
		formats=[
			BankFormat(
				name="CommBank",
				date_column="Date",
				description_column="Description",
				amount_column="Amount",
				date_format="%d/%m/%Y",
			),
			BankFormat(
				name="NAB",
				date_column="Transaction Date",
				description_column="Narrative",
				debit_column="Debit",
				credit_column="Credit",
			),
		]
	)


# ── Task 2: Job CRUD Tests ──


class TestJobCRUD:
	"""Test Job CRUD operations in StorageRegistry."""

	def test_save_and_get_job(self, storage, sample_job):
		"""Test saving and retrieving a job."""
		storage.save_job(sample_job)

		loaded = storage.get_job("J-20251123-001", sample_job.date_accepted)
		assert loaded.job_id == "J-20251123-001"
		assert loaded.client_id == "Woolworths"
		assert loaded.status == JobStatus.SCHEDULED

	def test_job_versioning(self, storage, sample_job):
		"""Test job creates new versions on save."""
		storage.save_job(sample_job)
		versions = storage.get_job_versions("J-20251123-001")
		assert versions == [1]

		# Save updated version
		updated = sample_job.model_copy(update={"date_started": date(2025, 12, 1)})
		storage.save_job(updated)

		versions = storage.get_job_versions("J-20251123-001")
		assert versions == [1, 2]

	def test_get_job_specific_version(self, storage, sample_job):
		"""Test retrieving specific job version."""
		storage.save_job(sample_job)

		updated = sample_job.model_copy(update={"notes": "Updated notes"})
		storage.save_job(updated)

		v1 = storage.get_job("J-20251123-001", sample_job.date_accepted, version=1)
		assert v1.notes == "Sample job"

		v2 = storage.get_job("J-20251123-001", sample_job.date_accepted, version=2)
		assert v2.notes == "Updated notes"

		latest = storage.get_job("J-20251123-001", sample_job.date_accepted)
		assert latest.notes == "Updated notes"

	def test_get_all_jobs_latest_only(self, storage):
		"""Test getting all jobs returns latest versions only by default."""
		job1 = Job(
			job_id="J-001",
			client_id="Client A",
			date_accepted=date(2025, 11, 23),
		)
		job2 = Job(
			job_id="J-002",
			client_id="Client B",
			date_accepted=date(2025, 11, 23),
		)

		storage.save_job(job1)
		storage.save_job(job1)  # Version 2
		storage.save_job(job2)

		all_jobs = storage.get_all_jobs(latest_only=True)
		assert len(all_jobs) == 2

		all_versions = storage.get_all_jobs(latest_only=False)
		assert len(all_versions) == 3

	def test_get_all_jobs_by_financial_year(self, storage):
		"""Test filtering jobs by financial year."""
		job_fy25 = Job(
			job_id="J-FY25",
			client_id="Client A",
			date_accepted=date(2025, 8, 1),  # FY 2025-26
		)
		job_fy24 = Job(
			job_id="J-FY24",
			client_id="Client B",
			date_accepted=date(2025, 3, 1),  # FY 2024-25
		)

		storage.save_job(job_fy25)
		storage.save_job(job_fy24)

		fy25_jobs = storage.get_all_jobs(financial_year="2025-26")
		assert len(fy25_jobs) == 1
		assert fy25_jobs[0].job_id == "J-FY25"

	def test_update_job(self, storage, sample_job):
		"""Test updating an existing job."""
		storage.save_job(sample_job)

		updated = sample_job.model_copy(update={"date_started": date(2025, 12, 1)})
		storage.update_job(updated)

		latest = storage.get_job("J-20251123-001", sample_job.date_accepted)
		assert latest.date_started == date(2025, 12, 1)
		assert latest.status == JobStatus.IN_PROGRESS

	def test_update_nonexistent_job_raises_error(self, storage, sample_job):
		"""Test updating non-existent job raises FileNotFoundError."""
		with pytest.raises(FileNotFoundError, match="Job not found"):
			storage.update_job(sample_job)

	def test_get_job_not_found(self, storage):
		"""Test getting non-existent job raises FileNotFoundError."""
		with pytest.raises(FileNotFoundError, match="Job not found: J-999"):
			storage.get_job("J-999", date(2025, 11, 23))

	def test_job_persistence_across_instances(self, tmp_path, sample_job):
		"""Test jobs persist and reload across registry instances."""
		storage1 = StorageRegistry(tmp_path)
		storage1.save_job(sample_job)

		storage2 = StorageRegistry(tmp_path)
		assert len(storage2.get_all_jobs()) == 1
		loaded = storage2.get_job("J-20251123-001", sample_job.date_accepted)
		assert loaded.client_id == "Woolworths"


# ── Task 3: Unclassified Transactions Tests ──


class TestUnclassifiedTransactions:
	"""Test get_unclassified_transactions method."""

	def test_get_unclassified_transactions(self, storage):
		"""Test finding transactions with UNCLASSIFIED account codes."""
		classified = Transaction(
			transaction_id="TXN-CL",
			date=date(2025, 11, 23),
			description="Classified payment",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("100"), credit=Decimal("0")),
				JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("100")),
			],
		)
		unclassified = Transaction(
			transaction_id="TXN-UC",
			date=date(2025, 11, 24),
			description="Unclassified payment",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("200"), credit=Decimal("0")),
				JournalEntry(
					account_code="UNCLASSIFIED", debit=Decimal("0"), credit=Decimal("200")
				),
			],
		)

		storage.save_transaction(classified)
		storage.save_transaction(unclassified)

		result = storage.get_unclassified_transactions()
		assert len(result) == 1
		assert result[0].transaction_id == "TXN-UC"

	def test_get_unclassified_empty_when_all_classified(self, storage, sample_transaction):
		"""Test returns empty list when no unclassified transactions."""
		storage.save_transaction(sample_transaction)

		result = storage.get_unclassified_transactions()
		assert result == []

	def test_get_unclassified_with_financial_year_filter(self, storage):
		"""Test unclassified transactions filtered by financial year."""
		txn_fy25 = Transaction(
			transaction_id="TXN-FY25",
			date=date(2025, 8, 1),
			description="FY25 unclassified",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("100"), credit=Decimal("0")),
				JournalEntry(
					account_code="UNCLASSIFIED", debit=Decimal("0"), credit=Decimal("100")
				),
			],
		)
		txn_fy24 = Transaction(
			transaction_id="TXN-FY24",
			date=date(2025, 3, 1),
			description="FY24 unclassified",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("50"), credit=Decimal("0")),
				JournalEntry(
					account_code="UNCLASSIFIED", debit=Decimal("0"), credit=Decimal("50")
				),
			],
		)

		storage.save_transaction(txn_fy25)
		storage.save_transaction(txn_fy24)

		result = storage.get_unclassified_transactions(financial_year="2025-26")
		assert len(result) == 1
		assert result[0].transaction_id == "TXN-FY25"


# ── Task 5: ChartOfAccounts Tests ──


class TestChartOfAccounts:
	"""Test ChartOfAccounts storage operations."""

	def test_save_and_get_chart_of_accounts(self, storage, sample_chart_of_accounts):
		"""Test saving and retrieving chart of accounts."""
		storage.save_chart_of_accounts(sample_chart_of_accounts)

		loaded = storage.get_chart_of_accounts()
		assert len(loaded.accounts) == 4
		assert loaded.accounts[0].name == "Bank Account"

	def test_get_account_codes(self, storage, sample_chart_of_accounts):
		"""Test getting account code list for TUI dropdowns."""
		storage.save_chart_of_accounts(sample_chart_of_accounts)

		codes = storage.get_account_codes()
		assert codes == ["Bank Account", "Accounts Receivable", "Revenue", "Office Supplies"]

	def test_get_chart_of_accounts_not_found(self, storage):
		"""Test getting chart of accounts when none exists."""
		with pytest.raises(FileNotFoundError, match="Chart of accounts not found"):
			storage.get_chart_of_accounts()

	def test_chart_of_accounts_persistence(self, tmp_path, sample_chart_of_accounts):
		"""Test chart of accounts persists across instances."""
		storage1 = StorageRegistry(tmp_path)
		storage1.save_chart_of_accounts(sample_chart_of_accounts)

		storage2 = StorageRegistry(tmp_path)
		loaded = storage2.get_chart_of_accounts()
		assert len(loaded.accounts) == 4

	def test_load_chart_of_accounts_from_yaml(self, tmp_path):
		"""Test loading chart of accounts from YAML fallback."""
		config_dir = tmp_path / "config"
		config_dir.mkdir(parents=True)

		yaml_content = """- name: asset
  accounts:
    - name: Cash
      description: Cash on hand
    - name: Bank
      description: Bank accounts
- name: income
  accounts:
    - name: Sales
      description: Sales income
"""
		(config_dir / "chart_of_accounts.yaml").write_text(yaml_content)

		storage = StorageRegistry(tmp_path)
		chart = storage.get_chart_of_accounts()
		assert len(chart.accounts) == 3
		assert chart.accounts[0].name == "Cash"
		assert chart.accounts[0].account_type == AccountType.ASSET

	def test_get_account_codes_not_found(self, storage):
		"""Test get_account_codes raises when no chart exists."""
		with pytest.raises(FileNotFoundError):
			storage.get_account_codes()


# ── Task 6: BankFormats Tests ──


class TestBankFormats:
	"""Test BankFormats storage operations."""

	def test_save_and_get_bank_formats(self, storage, sample_bank_formats):
		"""Test saving and retrieving bank formats."""
		storage.save_bank_formats(sample_bank_formats)

		loaded = storage.get_bank_formats()
		assert len(loaded.formats) == 2
		assert loaded.formats[0].name == "CommBank"

	def test_get_bank_formats_not_found(self, storage):
		"""Test getting bank formats when none exist."""
		with pytest.raises(FileNotFoundError, match="Bank formats not found"):
			storage.get_bank_formats()

	def test_bank_formats_persistence(self, tmp_path, sample_bank_formats):
		"""Test bank formats persist across instances."""
		storage1 = StorageRegistry(tmp_path)
		storage1.save_bank_formats(sample_bank_formats)

		storage2 = StorageRegistry(tmp_path)
		loaded = storage2.get_bank_formats()
		assert len(loaded.formats) == 2
		assert loaded.get_format("NAB").description_column == "Narrative"

	def test_update_bank_formats(self, storage, sample_bank_formats):
		"""Test updating bank formats replaces existing."""
		storage.save_bank_formats(sample_bank_formats)

		updated = BankFormats(
			formats=[
				BankFormat(
					name="Westpac",
					date_column="Date",
					description_column="Desc",
					amount_column="Amount",
				)
			]
		)
		storage.save_bank_formats(updated)

		loaded = storage.get_bank_formats()
		assert len(loaded.formats) == 1
		assert loaded.formats[0].name == "Westpac"


# ── Task 7: Delete and Void Transaction Tests ──


class TestDeleteAndVoidTransaction:
	"""Test delete_transaction and void_transaction methods."""

	def test_delete_transaction(self, storage, sample_transaction):
		"""Test deleting a transaction removes it from memory and disk."""
		storage.save_transaction(sample_transaction)
		assert storage.transaction_exists("TXN-001", date(2025, 11, 23))

		storage.delete_transaction("TXN-001", date(2025, 11, 23))
		assert not storage.transaction_exists("TXN-001", date(2025, 11, 23))

	def test_delete_transaction_persists(self, tmp_path, sample_transaction):
		"""Test deletion persists across registry instances."""
		storage1 = StorageRegistry(tmp_path)
		storage1.save_transaction(sample_transaction)
		storage1.delete_transaction("TXN-001", date(2025, 11, 23))

		storage2 = StorageRegistry(tmp_path)
		assert not storage2.transaction_exists("TXN-001", date(2025, 11, 23))

	def test_delete_nonexistent_transaction_raises_error(self, storage):
		"""Test deleting non-existent transaction raises KeyError."""
		with pytest.raises(KeyError, match="Transaction not found"):
			storage.delete_transaction("TXN-999", date(2025, 11, 23))

	def test_void_transaction(self, storage, sample_transaction):
		"""Test voiding a transaction creates a reversing entry."""
		storage.save_transaction(sample_transaction)

		void_txn = storage.void_transaction("TXN-001", date(2025, 11, 23))

		assert "VOID" in void_txn.description
		assert f"reverses TXN-001" in void_txn.description

		# Reversing entry should have swapped debits/credits
		original = storage.get_transaction("TXN-001", date(2025, 11, 23))
		for orig_entry, void_entry in zip(original.entries, void_txn.entries):
			assert void_entry.debit == orig_entry.credit
			assert void_entry.credit == orig_entry.debit

	def test_void_nonexistent_transaction_raises_error(self, storage):
		"""Test voiding non-existent transaction raises KeyError."""
		with pytest.raises(KeyError, match="Transaction not found"):
			storage.void_transaction("TXN-999", date(2025, 11, 23))

	def test_void_transaction_is_saved(self, storage, sample_transaction):
		"""Test void transaction is saved in storage."""
		storage.save_transaction(sample_transaction)

		void_txn = storage.void_transaction("TXN-001", date(2025, 11, 23))

		# Should be able to retrieve the void transaction
		loaded = storage.get_transaction(void_txn.transaction_id, void_txn.date)
		assert loaded.transaction_id == void_txn.transaction_id


# ── Task 8: Date-Range Filtering Tests ──


class TestDateRangeFiltering:
	"""Test date-range filtering on transactions."""

	def _create_transactions(self, storage):
		"""Helper to create transactions across multiple dates."""
		for day in [10, 15, 20, 25, 30]:
			txn = Transaction(
				transaction_id=f"TXN-NOV{day}",
				date=date(2025, 11, day),
				description=f"Transaction on Nov {day}",
				entries=[
					JournalEntry(
						account_code="1100", debit=Decimal("100"), credit=Decimal("0")
					),
					JournalEntry(
						account_code="4100", debit=Decimal("0"), credit=Decimal("100")
					),
				],
			)
			storage.save_transaction(txn)

	def test_filter_by_start_date(self, storage):
		"""Test filtering transactions with start_date."""
		self._create_transactions(storage)

		result = storage.get_all_transactions(start_date=date(2025, 11, 20))
		assert len(result) == 3  # 20, 25, 30

	def test_filter_by_end_date(self, storage):
		"""Test filtering transactions with end_date."""
		self._create_transactions(storage)

		result = storage.get_all_transactions(end_date=date(2025, 11, 20))
		assert len(result) == 3  # 10, 15, 20

	def test_filter_by_date_range(self, storage):
		"""Test filtering transactions with both start and end dates."""
		self._create_transactions(storage)

		result = storage.get_all_transactions(
			start_date=date(2025, 11, 15), end_date=date(2025, 11, 25)
		)
		assert len(result) == 3  # 15, 20, 25

	def test_get_transactions_by_account(self, storage):
		"""Test filtering transactions by account code."""
		txn1 = Transaction(
			transaction_id="TXN-A",
			date=date(2025, 11, 23),
			description="Sales payment",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("100"), credit=Decimal("0")),
				JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("100")),
			],
		)
		txn2 = Transaction(
			transaction_id="TXN-B",
			date=date(2025, 11, 24),
			description="Office supplies",
			entries=[
				JournalEntry(account_code="5100", debit=Decimal("50"), credit=Decimal("0")),
				JournalEntry(account_code="1100", debit=Decimal("0"), credit=Decimal("50")),
			],
		)
		txn3 = Transaction(
			transaction_id="TXN-C",
			date=date(2025, 11, 25),
			description="Rent payment",
			entries=[
				JournalEntry(account_code="5200", debit=Decimal("500"), credit=Decimal("0")),
				JournalEntry(account_code="1100", debit=Decimal("0"), credit=Decimal("500")),
			],
		)

		storage.save_transaction(txn1)
		storage.save_transaction(txn2)
		storage.save_transaction(txn3)

		# 1100 appears in all three
		result = storage.get_transactions_by_account("1100")
		assert len(result) == 3

		# 4100 appears in one
		result = storage.get_transactions_by_account("4100")
		assert len(result) == 1

		# 5200 appears in one
		result = storage.get_transactions_by_account("5200")
		assert len(result) == 1

	def test_get_transactions_by_account_with_date_range(self, storage):
		"""Test account filter combined with date range."""
		for day in [10, 20, 30]:
			txn = Transaction(
				transaction_id=f"TXN-D{day}",
				date=date(2025, 11, day),
				description=f"Payment {day}",
				entries=[
					JournalEntry(
						account_code="1100", debit=Decimal("100"), credit=Decimal("0")
					),
					JournalEntry(
						account_code="4100", debit=Decimal("0"), credit=Decimal("100")
					),
				],
			)
			storage.save_transaction(txn)

		result = storage.get_transactions_by_account(
			"1100", start_date=date(2025, 11, 15), end_date=date(2025, 11, 25)
		)
		assert len(result) == 1  # Only Nov 20


# ── Task 10: Transaction Search Tests ──


class TestTransactionSearch:
	"""Test search_transactions method."""

	def _create_search_data(self, storage):
		"""Helper to create diverse transactions for search tests."""
		txns = [
			Transaction(
				transaction_id="TXN-S1",
				date=date(2025, 11, 10),
				description="Payment from Woolworths",
				entries=[
					JournalEntry(
						account_code="1100", debit=Decimal("500"), credit=Decimal("0")
					),
					JournalEntry(
						account_code="4100", debit=Decimal("0"), credit=Decimal("500")
					),
				],
			),
			Transaction(
				transaction_id="TXN-S2",
				date=date(2025, 11, 20),
				description="Office supplies purchase",
				entries=[
					JournalEntry(
						account_code="5100", debit=Decimal("150"), credit=Decimal("0")
					),
					JournalEntry(
						account_code="1100", debit=Decimal("0"), credit=Decimal("150")
					),
				],
			),
			Transaction(
				transaction_id="TXN-S3",
				date=date(2025, 11, 25),
				description="Payment from Coles",
				entries=[
					JournalEntry(
						account_code="1100", debit=Decimal("2000"), credit=Decimal("0")
					),
					JournalEntry(
						account_code="4100", debit=Decimal("0"), credit=Decimal("2000")
					),
				],
			),
		]
		for txn in txns:
			storage.save_transaction(txn)

	def test_search_by_query(self, storage):
		"""Test case-insensitive description search."""
		self._create_search_data(storage)

		result = storage.search_transactions(query="payment")
		assert len(result) == 2  # Woolworths and Coles

		result = storage.search_transactions(query="OFFICE")
		assert len(result) == 1

	def test_search_by_account_code(self, storage):
		"""Test filtering by account code."""
		self._create_search_data(storage)

		result = storage.search_transactions(account_code="5100")
		assert len(result) == 1
		assert result[0].transaction_id == "TXN-S2"

	def test_search_by_min_amount(self, storage):
		"""Test filtering by minimum amount."""
		self._create_search_data(storage)

		result = storage.search_transactions(min_amount=Decimal("500"))
		assert len(result) == 2  # TXN-S1 (500) and TXN-S3 (2000)

	def test_search_by_max_amount(self, storage):
		"""Test filtering by maximum amount."""
		self._create_search_data(storage)

		result = storage.search_transactions(max_amount=Decimal("500"))
		assert len(result) == 2  # TXN-S1 (500) and TXN-S2 (150)

	def test_search_by_amount_range(self, storage):
		"""Test filtering by amount range."""
		self._create_search_data(storage)

		result = storage.search_transactions(
			min_amount=Decimal("200"), max_amount=Decimal("1000")
		)
		assert len(result) == 1  # TXN-S1 (500)

	def test_search_combined_filters(self, storage):
		"""Test combining multiple search criteria."""
		self._create_search_data(storage)

		result = storage.search_transactions(
			query="payment",
			account_code="4100",
			min_amount=Decimal("1000"),
		)
		assert len(result) == 1
		assert result[0].transaction_id == "TXN-S3"

	def test_search_with_date_range(self, storage):
		"""Test search combined with date filtering."""
		self._create_search_data(storage)

		result = storage.search_transactions(
			query="payment",
			start_date=date(2025, 11, 15),
		)
		assert len(result) == 1  # Only Coles (Nov 25)

	def test_search_no_results(self, storage):
		"""Test search returning no results."""
		self._create_search_data(storage)

		result = storage.search_transactions(query="nonexistent")
		assert result == []

	def test_search_no_filters_returns_all(self, storage):
		"""Test search with no filters returns all transactions."""
		self._create_search_data(storage)

		result = storage.search_transactions()
		assert len(result) == 3


# ── Reload and Initialization Tests ──


class TestReloadWithNewEntities:
	"""Test that reload properly handles all new entity types."""

	def test_reload_clears_jobs(self, storage, sample_job):
		"""Test reload clears job data."""
		storage.save_job(sample_job)
		assert len(storage.get_all_jobs()) == 1

		# Add unsaved job to memory
		storage._jobs[("J-UNSAVED", 1)] = sample_job
		storage._latest_jobs["J-UNSAVED"] = 1
		assert len(storage.get_all_jobs()) == 2

		storage.reload()
		assert len(storage.get_all_jobs()) == 1

	def test_initialization_empty_includes_new_entities(self, tmp_path):
		"""Test empty initialization works for all new entity types."""
		storage = StorageRegistry(tmp_path)

		assert storage.get_all_jobs() == []

		with pytest.raises(FileNotFoundError):
			storage.get_chart_of_accounts()

		with pytest.raises(FileNotFoundError):
			storage.get_bank_formats()
