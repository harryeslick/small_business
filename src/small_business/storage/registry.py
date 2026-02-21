"""In-memory storage registry for small business data.

This module implements an in-memory storage system optimized for small business scale.
All data is loaded into memory at initialization and persisted incrementally to disk.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import (
	BankFormats,
	ChartOfAccounts,
	Client,
	Invoice,
	Job,
	Quote,
	Settings,
	Transaction,
	get_financial_year,
)
from small_business.storage.paths import get_financial_year_dir


class StorageRegistry:
	"""In-memory storage registry - loads all data on initialization.

	This class provides a unified interface for managing all business entities
	(clients, quotes, invoices, transactions, settings) with in-memory operations
	and incremental persistence to disk.

	The registry loads all data into memory at initialization and performs all
	queries as dictionary lookups. Writes are immediately persisted to disk using
	an append-only strategy, with compaction performed on next load.

	Args:
		data_dir: Base directory for data storage

	Examples:
		>>> storage = StorageRegistry(Path("./data"))
		>>> client = storage.get_client("Woolworths")
		>>> storage.save_client(client)
	"""

	def __init__(self, data_dir: Path):
		"""Initialize storage registry and load all data from disk.

		Args:
			data_dir: Base directory for data storage
		"""
		self.data_dir = Path(data_dir)

		# In-memory storage
		self._clients: dict[str, Client] = {}  # normalized_id -> Client
		self._quotes: dict[tuple[str, int], Quote] = {}  # (id, version) -> Quote
		self._invoices: dict[tuple[str, int], Invoice] = {}  # (id, version) -> Invoice
		self._jobs: dict[tuple[str, int], Job] = {}  # (id, version) -> Job
		self._transactions: dict[tuple[str, date], Transaction] = {}  # (id, date) -> Transaction
		self._settings: Settings | None = None
		self._bank_formats: BankFormats | None = None
		self._chart_of_accounts: ChartOfAccounts | None = None

		# Latest version tracking for versioned entities
		self._latest_quotes: dict[str, int] = {}  # quote_id -> latest_version
		self._latest_invoices: dict[str, int] = {}  # invoice_id -> latest_version
		self._latest_jobs: dict[str, int] = {}  # job_id -> latest_version

		# Load all data from disk
		self._load_all_data()

	def _load_all_data(self) -> None:
		"""Load all entities from disk into memory."""
		self._load_clients()
		self._load_quotes()
		self._load_invoices()
		self._load_jobs()
		self._load_transactions()
		self._load_settings()
		self._load_bank_formats()
		self._load_chart_of_accounts()

	def reload(self) -> None:
		"""Reload all data from disk (discard in-memory changes).

		This method clears all in-memory state and reloads from disk files.
		Any unsaved changes are lost.
		"""
		self._clients.clear()
		self._quotes.clear()
		self._invoices.clear()
		self._jobs.clear()
		self._transactions.clear()
		self._latest_quotes.clear()
		self._latest_invoices.clear()
		self._latest_jobs.clear()
		self._settings = None
		self._bank_formats = None
		self._chart_of_accounts = None

		self._load_all_data()

	# Client Operations

	def save_client(self, client: Client) -> None:
		"""Save client to memory and persist to disk.

		Args:
			client: Client to save

		Notes:
			- Client ID matching is case-insensitive
			- Updates existing client if ID matches (case-insensitive)
			- Preserves the new client_id case when updating
		"""
		normalized_id = client.client_id.lower()
		self._clients[normalized_id] = client

		# Persist to disk (append to JSONL)
		clients_file = self._get_clients_file()
		clients_file.parent.mkdir(parents=True, exist_ok=True)

		with open(clients_file, "a") as f:
			f.write(client.model_dump_json() + "\n")

	def get_client(self, client_id: str) -> Client:
		"""Get client by ID (case-insensitive lookup).

		Args:
			client_id: Client business name (case-insensitive)

		Returns:
			Client matching the ID

		Raises:
			KeyError: If client not found
		"""
		normalized_id = client_id.lower()
		if normalized_id not in self._clients:
			raise KeyError(f"Client not found: {client_id}")
		return self._clients[normalized_id]

	def get_all_clients(self) -> list[Client]:
		"""Get all clients.

		Returns:
			List of all clients (empty list if none exist)
		"""
		return list(self._clients.values())

	def client_exists(self, client_id: str) -> bool:
		"""Check if client exists (case-insensitive).

		Args:
			client_id: Client business name

		Returns:
			True if client exists, False otherwise
		"""
		return client_id.lower() in self._clients

	def _load_clients(self) -> None:
		"""Load all clients from JSONL file and compact."""
		clients_file = self._get_clients_file()

		if not clients_file.exists():
			return

		# Read and deduplicate (last entry wins)
		clients_dict = {}
		with open(clients_file) as f:
			for line in f:
				if line := line.strip():
					client = Client.model_validate_json(line)
					clients_dict[client.client_id.lower()] = client

		self._clients = clients_dict

		# Compact file
		self._compact_clients()

	def _compact_clients(self) -> None:
		"""Rewrite JSONL file with current in-memory state."""
		clients_file = self._get_clients_file()

		if not self._clients:
			# No clients - ensure file doesn't exist or is empty
			if clients_file.exists():
				clients_file.unlink()
			return

		clients_file.parent.mkdir(parents=True, exist_ok=True)

		with open(clients_file, "w") as f:
			for client in self._clients.values():
				f.write(client.model_dump_json() + "\n")

	def _get_clients_file(self) -> Path:
		"""Get path to clients JSONL file."""
		return self.data_dir / "clients" / "clients.jsonl"

	# Quote Operations

	def save_quote(self, quote: Quote) -> None:
		"""Save quote as new version.

		Args:
			quote: Quote to save

		Notes:
			- Automatically determines next version number
			- Creates new versioned file (immutable)
			- Updates latest version index
		"""
		version = self._get_next_quote_version(quote.quote_id)

		# Store in memory
		self._quotes[(quote.quote_id, version)] = quote
		self._latest_quotes[quote.quote_id] = version

		# Persist to disk (write new version file)
		filepath = self._get_quote_path(quote.quote_id, quote.date_created, version)
		filepath.parent.mkdir(parents=True, exist_ok=True)
		filepath.write_text(quote.model_dump_json(indent=2))

	def get_quote(self, quote_id: str, date: date, version: int | None = None) -> Quote:
		"""Get quote by ID and optional version.

		Args:
			quote_id: Quote identifier
			date: Quote date (for financial year organization)
			version: Specific version to load (None = latest)

		Returns:
			Quote matching the ID and version

		Raises:
			FileNotFoundError: If quote or version not found
		"""
		if version is None:
			version = self._latest_quotes.get(quote_id)
			if version is None:
				raise FileNotFoundError(f"Quote not found: {quote_id}")

		key = (quote_id, version)
		if key not in self._quotes:
			raise FileNotFoundError(f"Quote not found: {quote_id} version {version}")

		return self._quotes[key]

	def get_quote_versions(self, quote_id: str) -> list[int]:
		"""Get all version numbers for a quote.

		Args:
			quote_id: Quote identifier

		Returns:
			Sorted list of version numbers
		"""
		return sorted([v for qid, v in self._quotes.keys() if qid == quote_id])

	def get_all_quotes(self, latest_only: bool = True, financial_year: str | None = None) -> list[Quote]:
		"""Get all quotes, optionally filtered.

		Args:
			latest_only: Only return latest version of each quote (default: True)
			financial_year: Filter by financial year string like "2025-26" (None = all years)

		Returns:
			List of quotes matching filters
		"""
		if latest_only:
			quotes = [self._quotes[(qid, v)] for qid, v in self._latest_quotes.items()]
		else:
			quotes = list(self._quotes.values())

		if financial_year is not None:
			quotes = [q for q in quotes if get_financial_year(q.date_created) == financial_year]

		return quotes

	def _load_quotes(self) -> None:
		"""Load all quote versions from all financial years."""
		for fy_dir in self._get_all_fy_dirs():
			quotes_dir = fy_dir / "quotes"
			if not quotes_dir.exists():
				continue

			# Load all versioned files
			for filepath in quotes_dir.glob("*_v*.json"):
				quote = Quote.model_validate_json(filepath.read_text())
				quote_id, version = self._parse_quote_filename(filepath.name)

				self._quotes[(quote_id, version)] = quote

				# Track latest version
				if quote_id not in self._latest_quotes or version > self._latest_quotes[quote_id]:
					self._latest_quotes[quote_id] = version

	def _get_next_quote_version(self, quote_id: str) -> int:
		"""Get next version number for a quote."""
		if quote_id in self._latest_quotes:
			return self._latest_quotes[quote_id] + 1
		return 1

	def _get_quote_path(self, quote_id: str, quote_created_date: date, version: int) -> Path:
		"""Get file path for a quote version."""
		fy_dir = get_financial_year_dir(self.data_dir, quote_created_date)
		quotes_dir = fy_dir / "quotes"
		return quotes_dir / f"{quote_id}_v{version}.json"

	def _parse_quote_filename(self, filename: str) -> tuple[str, int]:
		"""Parse quote filename to extract ID and version."""
		return self._parse_versioned_filename(filename)

	# Invoice Operations

	def save_invoice(self, invoice: Invoice) -> None:
		"""Save invoice as new version.

		Args:
			invoice: Invoice to save

		Notes:
			- Automatically determines next version number
			- Creates new versioned file (immutable)
			- Updates latest version index
		"""
		version = self._get_next_invoice_version(invoice.invoice_id)

		# Store in memory
		self._invoices[(invoice.invoice_id, version)] = invoice
		self._latest_invoices[invoice.invoice_id] = version

		# Persist to disk (use date_issued if available, otherwise date_created)
		invoice_date = invoice.date_issued or invoice.date_created
		filepath = self._get_invoice_path(invoice.invoice_id, invoice_date, version)
		filepath.parent.mkdir(parents=True, exist_ok=True)
		filepath.write_text(invoice.model_dump_json(indent=2))

	def get_invoice(self, invoice_id: str, date: date, version: int | None = None) -> Invoice:
		"""Get invoice by ID and optional version (defaults to latest).

		Args:
			invoice_id: Invoice identifier
			date: Invoice date (for financial year organization)
			version: Specific version to load (None = latest)

		Returns:
			Invoice matching the ID and version

		Raises:
			FileNotFoundError: If invoice or version not found
		"""
		if version is None:
			version = self._latest_invoices.get(invoice_id)
			if version is None:
				raise FileNotFoundError(f"Invoice not found: {invoice_id}")

		key = (invoice_id, version)
		if key not in self._invoices:
			raise FileNotFoundError(f"Invoice not found: {invoice_id} version {version}")

		return self._invoices[key]

	def get_invoice_versions(self, invoice_id: str) -> list[int]:
		"""Get all version numbers for an invoice.

		Args:
			invoice_id: Invoice identifier

		Returns:
			Sorted list of version numbers
		"""
		return sorted([v for iid, v in self._invoices.keys() if iid == invoice_id])

	def get_all_invoices(self, latest_only: bool = True, financial_year: str | None = None) -> list[Invoice]:
		"""Get all invoices, optionally filtered.

		Args:
			latest_only: Only return latest version of each invoice (default: True)
			financial_year: Filter by financial year string like "2025-26" (None = all years)

		Returns:
			List of invoices matching filters
		"""
		if latest_only:
			invoices = [self._invoices[(iid, v)] for iid, v in self._latest_invoices.items()]
		else:
			invoices = list(self._invoices.values())

		if financial_year is not None:
			invoices = [
				i
				for i in invoices
				if get_financial_year(i.date_issued or i.date_created) == financial_year
			]

		return invoices

	def _load_invoices(self) -> None:
		"""Load all invoice versions from all financial years."""
		for fy_dir in self._get_all_fy_dirs():
			invoices_dir = fy_dir / "invoices"
			if not invoices_dir.exists():
				continue

			# Load all versioned files
			for filepath in invoices_dir.glob("*_v*.json"):
				invoice = Invoice.model_validate_json(filepath.read_text())
				invoice_id, version = self._parse_invoice_filename(filepath.name)

				self._invoices[(invoice_id, version)] = invoice

				# Track latest version
				if invoice_id not in self._latest_invoices or version > self._latest_invoices[invoice_id]:
					self._latest_invoices[invoice_id] = version

	def _get_next_invoice_version(self, invoice_id: str) -> int:
		"""Get next version number for an invoice."""
		if invoice_id in self._latest_invoices:
			return self._latest_invoices[invoice_id] + 1
		return 1

	def _get_invoice_path(self, invoice_id: str, invoice_issued_date: date, version: int) -> Path:
		"""Get file path for an invoice version."""
		fy_dir = get_financial_year_dir(self.data_dir, invoice_issued_date)
		invoices_dir = fy_dir / "invoices"
		return invoices_dir / f"{invoice_id}_v{version}.json"

	def _parse_invoice_filename(self, filename: str) -> tuple[str, int]:
		"""Parse invoice filename to extract ID and version."""
		return self._parse_versioned_filename(filename)

	# Job Operations

	def save_job(self, job: Job) -> None:
		"""Save job as new version.

		Args:
			job: Job to save
		"""
		version = self._get_next_job_version(job.job_id)

		self._jobs[(job.job_id, version)] = job
		self._latest_jobs[job.job_id] = version

		filepath = self._get_job_path(job.job_id, job.date_accepted, version)
		filepath.parent.mkdir(parents=True, exist_ok=True)
		filepath.write_text(job.model_dump_json(indent=2))

	def get_job(self, job_id: str, date: date, version: int | None = None) -> Job:
		"""Get job by ID and optional version (defaults to latest).

		Args:
			job_id: Job identifier
			date: Job date (for financial year organization)
			version: Specific version to load (None = latest)

		Returns:
			Job matching the ID and version

		Raises:
			FileNotFoundError: If job or version not found
		"""
		if version is None:
			version = self._latest_jobs.get(job_id)
			if version is None:
				raise FileNotFoundError(f"Job not found: {job_id}")

		key = (job_id, version)
		if key not in self._jobs:
			raise FileNotFoundError(f"Job not found: {job_id} version {version}")

		return self._jobs[key]

	def get_job_versions(self, job_id: str) -> list[int]:
		"""Get all version numbers for a job.

		Args:
			job_id: Job identifier

		Returns:
			Sorted list of version numbers
		"""
		return sorted([v for jid, v in self._jobs.keys() if jid == job_id])

	def get_all_jobs(
		self, latest_only: bool = True, financial_year: str | None = None
	) -> list[Job]:
		"""Get all jobs, optionally filtered.

		Args:
			latest_only: Only return latest version of each job (default: True)
			financial_year: Filter by financial year string like "2025-26" (None = all years)

		Returns:
			List of jobs matching filters
		"""
		if latest_only:
			jobs = [self._jobs[(jid, v)] for jid, v in self._latest_jobs.items()]
		else:
			jobs = list(self._jobs.values())

		if financial_year is not None:
			jobs = [j for j in jobs if get_financial_year(j.date_accepted) == financial_year]

		return jobs

	def update_job(self, job: Job) -> None:
		"""Update existing job by saving a new version.

		Args:
			job: Job with updated data

		Raises:
			FileNotFoundError: If job not found
		"""
		if job.job_id not in self._latest_jobs:
			raise FileNotFoundError(f"Job not found: {job.job_id}")

		self.save_job(job)

	def _load_jobs(self) -> None:
		"""Load all job versions from all financial years."""
		for fy_dir in self._get_all_fy_dirs():
			jobs_dir = fy_dir / "jobs"
			if not jobs_dir.exists():
				continue

			for filepath in jobs_dir.glob("*_v*.json"):
				job = Job.model_validate_json(filepath.read_text())
				job_id, version = self._parse_versioned_filename(filepath.name)

				self._jobs[(job_id, version)] = job

				if job_id not in self._latest_jobs or version > self._latest_jobs[job_id]:
					self._latest_jobs[job_id] = version

	def _get_next_job_version(self, job_id: str) -> int:
		"""Get next version number for a job."""
		if job_id in self._latest_jobs:
			return self._latest_jobs[job_id] + 1
		return 1

	def _get_job_path(self, job_id: str, job_accepted_date: date, version: int) -> Path:
		"""Get file path for a job version."""
		fy_dir = get_financial_year_dir(self.data_dir, job_accepted_date)
		jobs_dir = fy_dir / "jobs"
		return jobs_dir / f"{job_id}_v{version}.json"

	# Transaction Operations

	def save_transaction(self, transaction: Transaction) -> None:
		"""Save new transaction.

		Args:
			transaction: Transaction to save

		Raises:
			ValueError: If transaction already exists (same ID and date)
		"""
		key = (transaction.transaction_id, transaction.date)
		if key in self._transactions:
			raise ValueError(f"Transaction already exists: {transaction.transaction_id}")

		self._transactions[key] = transaction

		# Persist to disk (append to financial year JSONL)
		txn_file = self._get_transaction_file(transaction.date)
		txn_file.parent.mkdir(parents=True, exist_ok=True)

		with open(txn_file, "a") as f:
			f.write(transaction.model_dump_json() + "\n")

	def update_transaction(self, transaction: Transaction) -> None:
		"""Update existing transaction.

		Args:
			transaction: Transaction with updated data

		Raises:
			KeyError: If transaction not found

		Notes:
			- Transaction must exist (same ID and date)
			- Appends updated version to JSONL (deduplication on next load)
		"""
		key = (transaction.transaction_id, transaction.date)
		if key not in self._transactions:
			raise KeyError(f"Transaction not found: {transaction.transaction_id}")

		self._transactions[key] = transaction

		# Persist to disk (append updated version)
		txn_file = self._get_transaction_file(transaction.date)

		with open(txn_file, "a") as f:
			f.write(transaction.model_dump_json() + "\n")

	def get_transaction(self, transaction_id: str, transaction_date: date) -> Transaction:
		"""Get transaction by ID and date.

		Args:
			transaction_id: Transaction identifier
			transaction_date: Transaction date

		Returns:
			Transaction matching the ID and date

		Raises:
			KeyError: If transaction not found
		"""
		key = (transaction_id, transaction_date)
		if key not in self._transactions:
			raise KeyError(f"Transaction not found: {transaction_id}")
		return self._transactions[key]

	def transaction_exists(self, transaction_id: str, transaction_date: date) -> bool:
		"""Check if transaction exists.

		Args:
			transaction_id: Transaction identifier
			transaction_date: Transaction date

		Returns:
			True if transaction exists, False otherwise
		"""
		return (transaction_id, transaction_date) in self._transactions

	def get_all_transactions(
		self,
		financial_year: str | None = None,
		start_date: date | None = None,
		end_date: date | None = None,
	) -> list[Transaction]:
		"""Get all transactions, optionally filtered.

		Args:
			financial_year: Filter by financial year string like "2025-26" (None = all years)
			start_date: Include only transactions on or after this date
			end_date: Include only transactions on or before this date

		Returns:
			List of transactions matching filters
		"""
		txns = list(self._transactions.values())

		if financial_year is not None:
			txns = [t for t in txns if get_financial_year(t.date) == financial_year]

		if start_date is not None:
			txns = [t for t in txns if t.date >= start_date]

		if end_date is not None:
			txns = [t for t in txns if t.date <= end_date]

		return txns

	def get_unclassified_transactions(
		self, financial_year: str | None = None
	) -> list[Transaction]:
		"""Get transactions with any UNCLASSIFIED entry.

		Args:
			financial_year: Filter by financial year (None = all years)

		Returns:
			List of transactions with at least one UNCLASSIFIED account_code
		"""
		txns = self.get_all_transactions(financial_year=financial_year)
		return [
			t
			for t in txns
			if any("UNCLASSIFIED" in entry.account_code for entry in t.entries)
		]

	def get_transactions_by_account(
		self,
		account_code: str,
		financial_year: str | None = None,
		start_date: date | None = None,
		end_date: date | None = None,
	) -> list[Transaction]:
		"""Get transactions that involve a specific account code.

		Args:
			account_code: Account code to filter by
			financial_year: Filter by financial year (None = all years)
			start_date: Include only transactions on or after this date
			end_date: Include only transactions on or before this date

		Returns:
			List of transactions with at least one entry matching the account code
		"""
		txns = self.get_all_transactions(
			financial_year=financial_year, start_date=start_date, end_date=end_date
		)
		return [
			t for t in txns if any(e.account_code == account_code for e in t.entries)
		]

	def delete_transaction(self, transaction_id: str, transaction_date: date) -> None:
		"""Delete a transaction from memory and disk.

		Args:
			transaction_id: Transaction identifier
			transaction_date: Transaction date

		Raises:
			KeyError: If transaction not found
		"""
		key = (transaction_id, transaction_date)
		if key not in self._transactions:
			raise KeyError(f"Transaction not found: {transaction_id}")

		del self._transactions[key]

		# Rewrite JSONL file without the deleted transaction
		txn_file = self._get_transaction_file(transaction_date)
		remaining = [
			t
			for t in self._transactions.values()
			if get_financial_year(t.date) == get_financial_year(transaction_date)
		]
		self._compact_transactions_for_file(txn_file, remaining)

	def void_transaction(self, transaction_id: str, transaction_date: date) -> Transaction:
		"""Void a transaction by creating a reversing entry.

		Creates a new transaction with opposite debits/credits and a description
		referencing the original. This is the preferred accounting practice over deletion.

		Args:
			transaction_id: Transaction identifier to void
			transaction_date: Transaction date

		Returns:
			The new reversing transaction

		Raises:
			KeyError: If transaction not found
		"""
		from small_business.models import JournalEntry as JE

		original = self.get_transaction(transaction_id, transaction_date)

		reversed_entries = [
			JE(
				account_code=entry.account_code,
				debit=entry.credit,
				credit=entry.debit,
			)
			for entry in original.entries
		]

		void_txn = Transaction(
			date=date.today(),
			description=f"VOID: {original.description} (reverses {transaction_id})",
			entries=reversed_entries,
		)

		self.save_transaction(void_txn)
		return void_txn

	def search_transactions(
		self,
		query: str | None = None,
		account_code: str | None = None,
		min_amount: Decimal | None = None,
		max_amount: Decimal | None = None,
		financial_year: str | None = None,
		start_date: date | None = None,
		end_date: date | None = None,
	) -> list[Transaction]:
		"""Search transactions with multiple filter criteria.

		Args:
			query: Case-insensitive substring match on description
			account_code: Filter to transactions with this account code
			min_amount: Minimum transaction amount (absolute value of any entry)
			max_amount: Maximum transaction amount (absolute value of any entry)
			financial_year: Filter by financial year
			start_date: Include only transactions on or after this date
			end_date: Include only transactions on or before this date

		Returns:
			List of transactions matching all provided criteria
		"""
		txns = self.get_all_transactions(
			financial_year=financial_year, start_date=start_date, end_date=end_date
		)

		if query is not None:
			query_lower = query.lower()
			txns = [t for t in txns if query_lower in t.description.lower()]

		if account_code is not None:
			txns = [
				t for t in txns if any(e.account_code == account_code for e in t.entries)
			]

		if min_amount is not None:
			txns = [
				t
				for t in txns
				if any(
					e.debit >= min_amount or e.credit >= min_amount for e in t.entries
				)
			]

		if max_amount is not None:
			txns = [
				t
				for t in txns
				if any(
					(e.debit > 0 and e.debit <= max_amount)
					or (e.credit > 0 and e.credit <= max_amount)
					for e in t.entries
				)
			]

		return txns

	def _load_transactions(self) -> None:
		"""Load all transactions from all financial years and compact per-year JSONL."""
		for fy_dir in self._get_all_fy_dirs():
			txn_file = fy_dir / "transactions.jsonl"
			if not txn_file.exists():
				continue

			# Read and deduplicate by (id, date) for this year
			txns_for_year = {}
			with open(txn_file) as f:
				for line in f:
					if line := line.strip():
						txn = Transaction.model_validate_json(line)
						txns_for_year[(txn.transaction_id, txn.date)] = txn

			# Add to main dict
			self._transactions.update(txns_for_year)

			# Compact this year's file
			self._compact_transactions_for_file(txn_file, txns_for_year.values())

	def _compact_transactions_for_file(self, txn_file: Path, transactions: list[Transaction]) -> None:
		"""Rewrite transaction JSONL file with deduplicated data."""
		if not transactions:
			# No transactions - remove file if it exists
			if txn_file.exists():
				txn_file.unlink()
			return

		with open(txn_file, "w") as f:
			for txn in transactions:
				f.write(txn.model_dump_json() + "\n")

	def _get_transaction_file(self, transaction_date: date) -> Path:
		"""Get path to transactions JSONL file for a given date."""
		fy_dir = get_financial_year_dir(self.data_dir, transaction_date)
		return fy_dir / "transactions.jsonl"

	# Settings Operations

	def get_settings(self) -> Settings:
		"""Get settings.

		Returns:
			Settings object

		Raises:
			FileNotFoundError: If settings not initialized
		"""
		if self._settings is None:
			raise FileNotFoundError("Settings not initialized")
		return self._settings

	def save_settings(self, settings: Settings) -> None:
		"""Save settings to memory and disk.

		Args:
			settings: Settings to save
		"""
		self._settings = settings

		# Persist to disk
		settings_file = self._get_settings_file()
		settings_file.parent.mkdir(parents=True, exist_ok=True)
		settings_file.write_text(settings.model_dump_json(indent=2))

	def settings_exist(self) -> bool:
		"""Check if settings are initialized.

		Returns:
			True if settings exist, False otherwise
		"""
		return self._settings is not None

	def _load_settings(self) -> None:
		"""Load settings from disk."""
		settings_file = self._get_settings_file()

		if not settings_file.exists():
			return

		self._settings = Settings.model_validate_json(settings_file.read_text())

	def _get_settings_file(self) -> Path:
		"""Get path to settings JSON file."""
		return self.data_dir / "settings.json"

	# ChartOfAccounts Operations

	def get_chart_of_accounts(self) -> ChartOfAccounts:
		"""Get chart of accounts.

		Returns:
			ChartOfAccounts object

		Raises:
			FileNotFoundError: If chart of accounts not found
		"""
		if self._chart_of_accounts is None:
			raise FileNotFoundError("Chart of accounts not found")
		return self._chart_of_accounts

	def save_chart_of_accounts(self, chart: ChartOfAccounts) -> None:
		"""Save chart of accounts to memory and disk.

		Args:
			chart: ChartOfAccounts to save
		"""
		self._chart_of_accounts = chart

		coa_file = self._get_chart_of_accounts_file()
		coa_file.parent.mkdir(parents=True, exist_ok=True)
		coa_file.write_text(chart.model_dump_json(indent=2))

	def get_account_codes(self) -> list[str]:
		"""Get list of all account code strings (account names).

		Returns:
			List of account name strings

		Raises:
			FileNotFoundError: If chart of accounts not found
		"""
		chart = self.get_chart_of_accounts()
		return [acc.name for acc in chart.accounts]

	def _load_chart_of_accounts(self) -> None:
		"""Load chart of accounts from disk."""
		# Try JSON first (our save format)
		json_file = self._get_chart_of_accounts_file()
		if json_file.exists():
			self._chart_of_accounts = ChartOfAccounts.model_validate_json(
				json_file.read_text()
			)
			return

		# Fall back to YAML config
		yaml_file = self.data_dir / "config" / "chart_of_accounts.yaml"
		if yaml_file.exists():
			self._chart_of_accounts = ChartOfAccounts.from_yaml(yaml_file)

	def _get_chart_of_accounts_file(self) -> Path:
		"""Get path to chart of accounts JSON file."""
		return self.data_dir / "config" / "chart_of_accounts.json"

	# BankFormats Operations

	def get_bank_formats(self) -> BankFormats:
		"""Get bank format configurations.

		Returns:
			BankFormats object

		Raises:
			FileNotFoundError: If bank formats not found
		"""
		if self._bank_formats is None:
			raise FileNotFoundError("Bank formats not found")
		return self._bank_formats

	def save_bank_formats(self, bank_formats: BankFormats) -> None:
		"""Save bank formats to memory and disk.

		Args:
			bank_formats: BankFormats to save
		"""
		self._bank_formats = bank_formats

		bf_file = self._get_bank_formats_file()
		bf_file.parent.mkdir(parents=True, exist_ok=True)
		bf_file.write_text(bank_formats.model_dump_json(indent=2))

	def _load_bank_formats(self) -> None:
		"""Load bank formats from disk."""
		bf_file = self._get_bank_formats_file()
		if bf_file.exists():
			self._bank_formats = BankFormats.model_validate_json(bf_file.read_text())

	def _get_bank_formats_file(self) -> Path:
		"""Get path to bank formats JSON file."""
		return self.data_dir / "config" / "bank_formats.json"

	# Utility Methods

	def _get_all_fy_dirs(self) -> list[Path]:
		"""Get all financial year directories.

		Returns:
			List of financial year directory paths (e.g., [2024-25, 2025-26])
		"""
		if not self.data_dir.exists():
			return []

		# Match directories that look like financial years (YYYY-YY format)
		import re
		fy_pattern = re.compile(r"^\d{4}-\d{2}$")
		return sorted([d for d in self.data_dir.iterdir() if d.is_dir() and fy_pattern.match(d.name)])

	def _parse_versioned_filename(self, filename: str) -> tuple[str, int]:
		"""Parse versioned filename to extract ID and version.

		Args:
			filename: Filename like "Q-20251123-001_v2.json"

		Returns:
			Tuple of (entity_id, version)
		"""
		name = filename.removesuffix(".json")
		parts = name.rsplit("_v", 1)
		return parts[0], int(parts[1])
