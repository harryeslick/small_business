"""Test StorageRegistry in-memory storage implementation."""

import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import (
	Client,
	Quote,
	Invoice,
	Transaction,
	LineItem,
	JournalEntry,
	Settings,
)
from small_business.storage import StorageRegistry


# Fixtures


@pytest.fixture
def storage(tmp_path: Path) -> StorageRegistry:
	"""Create storage registry with temporary data directory."""
	return StorageRegistry(tmp_path)


@pytest.fixture
def sample_client() -> Client:
	"""Create a sample client for testing."""
	return Client(
		client_id="Woolworths",
		name="Woolworths",
		email="contact@woolworths.com.au",
		phone="1300 767 969",
		abn="88 000 014 675",
	)


@pytest.fixture
def sample_quote() -> Quote:
	"""Create a sample quote for testing."""
	return Quote(
		quote_id="Q-20251123-001",
		date_created=date(2025, 11, 23),
		date_valid_until=date(2025, 12, 23),
		client_id="Woolworths",
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10"),
				unit_price=Decimal("150.00"),
			)
		],
	)


@pytest.fixture
def sample_invoice() -> Invoice:
	"""Create a sample invoice for testing."""
	return Invoice(
		invoice_id="INV-20251123-001",
		date_issued=date(2025, 11, 23),
		date_due=date(2025, 12, 23),
		client_id="Woolworths",
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10"),
				unit_price=Decimal("150.00"),
			)
		],
	)


@pytest.fixture
def sample_transaction() -> Transaction:
	"""Create a sample transaction for testing."""
	return Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 23),
		description="Payment received",
		entries=[
			JournalEntry(
				account_code="1100",
				debit=Decimal("1000.00"),
				credit=Decimal("0"),
			),
			JournalEntry(
				account_code="4100",
				debit=Decimal("0"),
				credit=Decimal("1000.00"),
			),
		],
	)


@pytest.fixture
def sample_settings(tmp_path: Path) -> Settings:
	"""Create sample settings for testing."""
	return Settings(
		business_name="Test Business Pty Ltd",
		business_abn="12 345 678 901",
		business_email="admin@test.com",
		business_phone="0400 000 000",
		business_address="123 Test St, Sydney NSW 2000",
		quote_template_path=str(tmp_path / "templates" / "quote.docx"),
		invoice_template_path=str(tmp_path / "templates" / "invoice.docx"),
	)


# Client Storage Tests


def test_initialization_empty_directory(tmp_path):
	"""Test StorageRegistry initializes with empty data directory."""
	storage = StorageRegistry(tmp_path)

	assert storage.get_all_clients() == []
	assert storage.get_all_quotes() == []
	assert storage.get_all_invoices() == []
	assert storage.get_all_transactions() == []
	assert not storage.settings_exist()


def test_save_and_get_client(storage, sample_client):
	"""Test saving and retrieving a client."""
	storage.save_client(sample_client)

	loaded = storage.get_client("Woolworths")
	assert loaded.client_id == "Woolworths"
	assert loaded.email == "contact@woolworths.com.au"


def test_client_case_insensitive_lookup(storage, sample_client):
	"""Test client lookup is case-insensitive."""
	storage.save_client(sample_client)

	# Load with different cases
	lower = storage.get_client("woolworths")
	upper = storage.get_client("WOOLWORTHS")
	mixed = storage.get_client("WoOlWoRtHs")

	# All should return same client with original case
	assert lower.client_id == "Woolworths"
	assert upper.client_id == "Woolworths"
	assert mixed.client_id == "Woolworths"


def test_update_existing_client(storage, sample_client):
	"""Test updating an existing client."""
	storage.save_client(sample_client)

	# Update client
	updated = Client(
		client_id="Woolworths",
		name="Woolworths Group",
		email="new@woolworths.com.au",
		phone="1300 111 222",
		abn="88 000 014 675",
	)
	storage.save_client(updated)

	# Should have one client with updated data
	all_clients = storage.get_all_clients()
	assert len(all_clients) == 1
	assert all_clients[0].name == "Woolworths Group"
	assert all_clients[0].email == "new@woolworths.com.au"


def test_client_case_insensitive_update(storage):
	"""Test update works with different case."""
	client_v1 = Client(
		client_id="MyCompany",
		name="MyCompany",
		email="old@mycompany.com",
	)
	storage.save_client(client_v1)

	# Update with different case
	client_v2 = Client(
		client_id="mycompany",
		name="mycompany",
		email="new@mycompany.com",
	)
	storage.save_client(client_v2)

	# Should have one client with new case
	all_clients = storage.get_all_clients()
	assert len(all_clients) == 1
	assert all_clients[0].client_id == "mycompany"
	assert all_clients[0].email == "new@mycompany.com"


def test_get_all_clients(storage):
	"""Test loading all clients."""
	clients = [
		Client(client_id="Client A", name="Client A", email="a@example.com"),
		Client(client_id="Client B", name="Client B", email="b@example.com"),
		Client(client_id="Client C", name="Client C", email="c@example.com"),
	]

	for client in clients:
		storage.save_client(client)

	loaded = storage.get_all_clients()
	assert len(loaded) == 3

	loaded_ids = {c.client_id for c in loaded}
	assert loaded_ids == {"Client A", "Client B", "Client C"}


def test_client_exists(storage, sample_client):
	"""Test client_exists check."""
	assert not storage.client_exists("Woolworths")

	storage.save_client(sample_client)
	assert storage.client_exists("Woolworths")
	assert storage.client_exists("woolworths")  # Case-insensitive


def test_get_client_not_found(storage):
	"""Test getting non-existent client raises KeyError."""
	with pytest.raises(KeyError, match="Client not found: NonExistent"):
		storage.get_client("NonExistent")


# Quote Storage Tests


def test_save_and_get_quote(storage, sample_quote):
	"""Test saving and retrieving a quote."""
	storage.save_quote(sample_quote)

	loaded = storage.get_quote("Q-20251123-001", sample_quote.date_created)
	assert loaded.quote_id == "Q-20251123-001"
	assert loaded.client_id == "Woolworths"
	assert len(loaded.line_items) == 1


def test_quote_versioning(storage, sample_quote):
	"""Test quote creates new versions on save."""
	# Save version 1
	storage.save_quote(sample_quote)

	versions = storage.get_quote_versions("Q-20251123-001")
	assert versions == [1]

	# Save version 2 (modify and save again)
	sample_quote.line_items.append(
		LineItem(
			description="Extra work",
			quantity=Decimal("5"),
			unit_price=Decimal("150.00"),
		)
	)
	storage.save_quote(sample_quote)

	versions = storage.get_quote_versions("Q-20251123-001")
	assert versions == [1, 2]


def test_get_quote_specific_version(storage, sample_quote):
	"""Test retrieving specific quote version."""
	# Save version 1
	storage.save_quote(sample_quote)

	# Create version 2 with changes (copy to avoid mutating original)
	quote_v2 = sample_quote.model_copy(deep=True)
	quote_v2.line_items.append(
		LineItem(
			description="Extra work",
			quantity=Decimal("5"),
			unit_price=Decimal("150.00"),
		)
	)
	storage.save_quote(quote_v2)

	# Get version 1
	v1 = storage.get_quote("Q-20251123-001", sample_quote.date_created, version=1)
	assert len(v1.line_items) == 1

	# Get version 2
	v2 = storage.get_quote("Q-20251123-001", sample_quote.date_created, version=2)
	assert len(v2.line_items) == 2

	# Get latest (should be v2)
	latest = storage.get_quote("Q-20251123-001", sample_quote.date_created)
	assert len(latest.line_items) == 2


def test_get_all_quotes_latest_only(storage):
	"""Test getting all quotes returns latest versions only by default."""
	# Create quote with multiple versions
	quote = Quote(
		quote_id="Q-001",
		date_created=date(2025, 11, 23),
		date_valid_until=date(2025, 12, 23),
		client_id="Client A",
		line_items=[
			LineItem(description="Item", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	storage.save_quote(quote)  # Version 1
	storage.save_quote(quote)  # Version 2

	# Create another quote
	quote2 = Quote(
		quote_id="Q-002",
		date_created=date(2025, 11, 23),
		date_valid_until=date(2025, 12, 23),
		client_id="Client B",
		line_items=[
			LineItem(description="Item", quantity=Decimal("1"), unit_price=Decimal("200"))
		],
	)
	storage.save_quote(quote2)  # Version 1

	# Get all (latest only)
	all_quotes = storage.get_all_quotes(latest_only=True)
	assert len(all_quotes) == 2  # 2 quotes, each latest version

	# Get all versions
	all_versions = storage.get_all_quotes(latest_only=False)
	assert len(all_versions) == 3  # 2 versions of Q-001 + 1 version of Q-002


def test_get_quote_not_found(storage):
	"""Test getting non-existent quote raises FileNotFoundError."""
	with pytest.raises(FileNotFoundError, match="Quote not found: Q-999"):
		storage.get_quote("Q-999", date(2025, 11, 23))


# Invoice Storage Tests


def test_save_and_get_invoice(storage, sample_invoice):
	"""Test saving and retrieving an invoice."""
	storage.save_invoice(sample_invoice)

	loaded = storage.get_invoice("INV-20251123-001", sample_invoice.date_issued)
	assert loaded.invoice_id == "INV-20251123-001"
	assert loaded.client_id == "Woolworths"


def test_invoice_versioning(storage, sample_invoice):
	"""Test invoice versioning works like quotes."""
	storage.save_invoice(sample_invoice)
	versions = storage.get_invoice_versions("INV-20251123-001")
	assert versions == [1]

	storage.save_invoice(sample_invoice)
	versions = storage.get_invoice_versions("INV-20251123-001")
	assert versions == [1, 2]


# Transaction Storage Tests


def test_save_and_get_transaction(storage, sample_transaction):
	"""Test saving and retrieving a transaction."""
	storage.save_transaction(sample_transaction)

	loaded = storage.get_transaction("TXN-001", date(2025, 11, 23))
	assert loaded.transaction_id == "TXN-001"
	assert loaded.description == "Payment received"


def test_transaction_unique_by_id_and_date(storage):
	"""Test transactions are unique by ID + date combination."""
	txn1 = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 23),
		description="Payment 1",
		entries=[
			JournalEntry(account_code="1100", debit=Decimal("100"), credit=Decimal("0")),
			JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("100")),
		],
	)

	txn2 = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 24),  # Different date
		description="Payment 2",
		entries=[
			JournalEntry(account_code="1100", debit=Decimal("200"), credit=Decimal("0")),
			JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("200")),
		],
	)

	storage.save_transaction(txn1)
	storage.save_transaction(txn2)  # Should succeed (different date)

	# Both should exist
	assert storage.transaction_exists("TXN-001", date(2025, 11, 23))
	assert storage.transaction_exists("TXN-001", date(2025, 11, 24))


def test_save_duplicate_transaction_raises_error(storage, sample_transaction):
	"""Test saving duplicate transaction raises ValueError."""
	storage.save_transaction(sample_transaction)

	with pytest.raises(ValueError, match="Transaction already exists: TXN-001"):
		storage.save_transaction(sample_transaction)


def test_update_transaction(storage, sample_transaction):
	"""Test updating an existing transaction."""
	storage.save_transaction(sample_transaction)

	# Update description
	updated = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 23),
		description="Updated: Payment from Woolworths",
		entries=sample_transaction.entries,
	)
	storage.update_transaction(updated)

	loaded = storage.get_transaction("TXN-001", date(2025, 11, 23))
	assert loaded.description == "Updated: Payment from Woolworths"


def test_update_nonexistent_transaction_raises_error(storage, sample_transaction):
	"""Test updating non-existent transaction raises KeyError."""
	with pytest.raises(KeyError, match="Transaction not found: TXN-001"):
		storage.update_transaction(sample_transaction)


def test_transaction_exists(storage, sample_transaction):
	"""Test transaction_exists check."""
	assert not storage.transaction_exists("TXN-001", date(2025, 11, 23))

	storage.save_transaction(sample_transaction)
	assert storage.transaction_exists("TXN-001", date(2025, 11, 23))


def test_get_all_transactions(storage):
	"""Test getting all transactions."""
	txns = [
		Transaction(
			transaction_id=f"TXN-{i:03d}",
			date=date(2025, 11, i + 1),
			description=f"Transaction {i}",
			entries=[
				JournalEntry(account_code="1100", debit=Decimal("100"), credit=Decimal("0")),
				JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("100")),
			],
		)
		for i in range(5)
	]

	for txn in txns:
		storage.save_transaction(txn)

	all_txns = storage.get_all_transactions()
	assert len(all_txns) == 5


def test_get_transaction_not_found(storage):
	"""Test getting non-existent transaction raises KeyError."""
	with pytest.raises(KeyError, match="Transaction not found: TXN-999"):
		storage.get_transaction("TXN-999", date(2025, 11, 23))


# Settings Storage Tests


def test_save_and_get_settings(storage, sample_settings):
	"""Test saving and retrieving settings."""
	storage.save_settings(sample_settings)

	loaded = storage.get_settings()
	assert loaded.business_name == "Test Business Pty Ltd"
	assert loaded.business_abn == "12 345 678 901"


def test_settings_exist(storage, sample_settings):
	"""Test settings_exist check."""
	assert not storage.settings_exist()

	storage.save_settings(sample_settings)
	assert storage.settings_exist()


def test_get_settings_not_initialized(storage):
	"""Test getting settings when not initialized raises FileNotFoundError."""
	with pytest.raises(FileNotFoundError, match="Settings not initialized"):
		storage.get_settings()


# Persistence Tests


def test_data_persists_across_registry_instances(tmp_path, sample_client, sample_quote):
	"""Test data is persisted and reloaded across registry instances."""
	# Save data with first instance
	storage1 = StorageRegistry(tmp_path)
	storage1.save_client(sample_client)
	storage1.save_quote(sample_quote)

	# Create new instance (should load persisted data)
	storage2 = StorageRegistry(tmp_path)

	assert len(storage2.get_all_clients()) == 1
	assert storage2.get_client("Woolworths").email == "contact@woolworths.com.au"

	assert len(storage2.get_all_quotes()) == 1
	assert storage2.get_quote("Q-20251123-001", sample_quote.date_created).client_id == "Woolworths"


def test_reload_discards_unsaved_changes(tmp_path, sample_client):
	"""Test reload() discards in-memory changes not persisted to disk."""
	storage = StorageRegistry(tmp_path)

	# Save initial client
	storage.save_client(sample_client)

	# Modify in-memory only (don't save)
	clients = storage.get_all_clients()
	assert len(clients) == 1

	# Manually modify the in-memory dict (simulating unsaved changes)
	storage._clients["test"] = Client(
		client_id="Test",
		name="Test Client",
		email="test@example.com",
	)

	assert len(storage.get_all_clients()) == 2  # In-memory has 2

	# Reload from disk
	storage.reload()

	# Should only have the persisted client
	assert len(storage.get_all_clients()) == 1
	assert not storage.client_exists("Test")


def test_jsonl_compaction_on_load(tmp_path):
	"""Test JSONL files are compacted on load (duplicates removed)."""
	clients_file = tmp_path / "clients" / "clients.jsonl"
	clients_file.parent.mkdir(parents=True)

	# Write duplicate entries (simulating append-only log)
	client_v1 = Client(client_id="Test", name="Test", email="v1@test.com")
	client_v2 = Client(client_id="Test", name="Test", email="v2@test.com")
	client_v3 = Client(client_id="Test", name="Test", email="v3@test.com")

	with open(clients_file, "w") as f:
		f.write(client_v1.model_dump_json() + "\n")
		f.write(client_v2.model_dump_json() + "\n")
		f.write(client_v3.model_dump_json() + "\n")

	# Load (should compact)
	storage = StorageRegistry(tmp_path)

	# Should have only latest version
	all_clients = storage.get_all_clients()
	assert len(all_clients) == 1
	assert all_clients[0].email == "v3@test.com"

	# File should be compacted (only 1 line)
	with open(clients_file) as f:
		lines = [line for line in f if line.strip()]
	assert len(lines) == 1


# In-Memory Behavior Tests


def test_multiple_operations_without_reload(storage, sample_client, sample_quote):
	"""Test multiple operations work in-memory without reloading."""
	# Save client
	storage.save_client(sample_client)

	# Immediately get client (from memory)
	client = storage.get_client("Woolworths")
	assert client.client_id == "Woolworths"

	# Save quote
	storage.save_quote(sample_quote)

	# Get quote (from memory)
	quote = storage.get_quote("Q-20251123-001", sample_quote.date_created)
	assert quote.client_id == "Woolworths"

	# All in-memory, no file reads after initialization


def test_in_memory_queries_are_fast(storage):
	"""Test in-memory queries work on loaded data."""
	# Create many clients
	for i in range(100):
		client = Client(
			client_id=f"Client{i:03d}",
			name=f"Client {i}",
			email=f"client{i}@example.com",
		)
		storage.save_client(client)

	# Filter in-memory (Python list comprehension)
	all_clients = storage.get_all_clients()
	# Example: filter for NSW clients (none in this test, but demonstrates filtering)
	_ = [c for c in all_clients if c.state == "NSW"]

	# This works because data is already in memory
	assert isinstance(all_clients, list)
	assert len(all_clients) == 100
