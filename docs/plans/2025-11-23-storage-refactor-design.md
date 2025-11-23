# Storage Layer Refactor: In-Memory Architecture

**Date:** 2025-11-23
**Status:** Design
**Target:** Phase 6 (Storage Optimization)

## Executive Summary

Refactor the storage layer from a functional approach (module-level functions) to a class-based `StorageRegistry` with in-memory data management. This design exploits the "small business" scale constraint to deliver radical simplification: load all data into memory at initialization, perform all operations in-memory, and persist incrementally to disk.

**Key Benefits:**
- **Simplicity** - No cache invalidation, no lazy loading complexity
- **Performance** - All queries are dictionary lookups (microseconds)
- **Predictability** - Data is always fresh after initialization
- **Scale-appropriate** - Optimized for small business data volumes (~20 MB)

**Key Trade-offs:**
- **Breaking Change** - Complete API redesign, no backward compatibility
- **Memory Usage** - ~20 MB per StorageRegistry instance (negligible on modern systems)
- **Startup Cost** - ~100ms to load all data on initialization
- **Scale Limit** - Not suitable for large enterprises (>100K entities)

## Motivation

### Current Architecture (Functional)

```python
from small_business.storage import load_client, save_client

client = load_client("Woolworths", data_dir)
client.contact_email = "new@example.com"
save_client(client, data_dir)
```

**Issues:**
- Each function call requires separate file I/O
- No shared state between operations
- Difficult to add features like caching without complexity
- Inconsistent patterns across different entity types

### Proposed Architecture (In-Memory Registry)

```python
from small_business.storage import StorageRegistry

storage = StorageRegistry(data_dir)  # Loads all data into memory

client = storage.get_client("Woolworths")  # Dictionary lookup
client.contact_email = "new@example.com"
storage.save_client(client)  # Updates memory + appends to disk
```

**Advantages:**
- Single initialization loads everything
- All queries are in-memory (fast)
- Clean, consistent API across all entity types
- Easy to add features (validation hooks, atomic transactions, etc.)

## Scale Analysis

### Typical Small Business Data Volumes

| Entity Type | Annual Volume | Size per Entity | Annual Storage |
|-------------|---------------|-----------------|----------------|
| Clients | 10-100 | ~10 KB | 1 MB |
| Quotes | 50-500 | ~5 KB | 2.5 MB |
| Invoices | 100-1,000 | ~5 KB | 5 MB |
| Transactions | 500-5,000 | ~1 KB | 5 MB |
| Settings | 1 | ~10 KB | 10 KB |

**Total in-memory footprint:** ~15-20 MB per year
**10-year footprint:** ~150-200 MB

### Memory vs Complexity Trade-off

Modern computers have 8-32 GB of RAM. Even a decade of small business data uses <1% of available memory. The real cost isn't memory—it's the cognitive overhead of managing lazy loading, cache invalidation, and partial updates.

**Conclusion:** For small business scale, in-memory simplicity beats "optimized" complexity.

## Architecture Overview

### Core Components

```
src/small_business/storage/
├── __init__.py              # Public API (export StorageRegistry)
├── registry.py              # StorageRegistry class (main implementation)
└── paths.py                 # Shared utilities (unchanged)
```

### StorageRegistry Class

**Initialization:**
```python
class StorageRegistry:
    """In-memory storage registry - loads all data on initialization."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

        # In-memory storage
        self._clients: dict[str, Client] = {}  # normalized_id -> Client
        self._quotes: dict[tuple[str, int], Quote] = {}  # (id, version) -> Quote
        self._invoices: dict[tuple[str, int], Invoice] = {}  # (id, version) -> Invoice
        self._transactions: dict[tuple[str, date], Transaction] = {}  # (id, date) -> Transaction
        self._settings: Settings | None = None

        # Latest version tracking for versioned entities
        self._latest_quotes: dict[str, int] = {}  # quote_id -> latest_version
        self._latest_invoices: dict[str, int] = {}  # invoice_id -> latest_version

        # Load all data from disk
        self._load_all_data()
```

**In-Memory Data Structures:**

1. **Clients** - `dict[str, Client]`
   - Key: `client_id.lower()` (case-insensitive lookups)
   - Value: `Client` object (preserves original case)

2. **Quotes** - `dict[tuple[str, int], Quote]`
   - Key: `(quote_id, version)`
   - Additional index: `_latest_quotes[quote_id] -> version`

3. **Invoices** - `dict[tuple[str, int], Invoice]`
   - Key: `(invoice_id, version)`
   - Additional index: `_latest_invoices[invoice_id] -> version`

4. **Transactions** - `dict[tuple[str, date], Transaction]`
   - Key: `(transaction_id, date)` - same ID can exist across financial years
   - Value: `Transaction` object

5. **Settings** - `Settings | None`
   - Single object (no dictionary needed)

## Persistence Strategy: Hybrid Append/Compact

### Core Principle

**Operations:**
- **Append on write** - Fast incremental persistence during operation
- **Compact on load** - Deduplicate and rewrite on next initialization

This leverages the in-memory architecture: writes are rare and batched (within a single session), loads establish canonical state.

### JSONL Entities (Clients, Transactions)

**Write Strategy - Append:**
```python
def save_client(self, client: Client) -> None:
    """Save client to memory and append to JSONL."""
    normalized_id = client.client_id.lower()
    self._clients[normalized_id] = client

    # Append to JSONL (fast, O(1) write)
    with open(self.clients_file, "a") as f:
        f.write(client.model_dump_json() + "\n")
```

**Read Strategy - Deduplicate and Compact:**
```python
def _load_clients(self) -> None:
    """Load clients and compact JSONL file."""
    if not self.clients_file.exists():
        return

    # Read all lines and deduplicate (last entry wins)
    clients_dict = {}
    with open(self.clients_file) as f:
        for line in f:
            if line := line.strip():
                client = Client.model_validate_json(line)
                clients_dict[client.client_id.lower()] = client

    self._clients = clients_dict

    # Compact file to remove duplicates
    self._compact_clients()

def _compact_clients(self) -> None:
    """Rewrite JSONL file with current in-memory state."""
    with open(self.clients_file, "w") as f:
        for client in self._clients.values():
            f.write(client.model_dump_json() + "\n")
```

**Properties:**
- ✅ Fast writes during operation (append-only)
- ✅ File is eventually consistent (compacted on next load)
- ✅ File serves as append-only log between sessions
- ✅ Automatic deduplication

### Versioned Entities (Quotes, Invoices)

**Write Strategy - New Files Only:**
```python
def save_quote(self, quote: Quote) -> None:
    """Save quote as new version file."""
    version = self._get_next_quote_version(quote.quote_id)

    # Update in-memory state
    self._quotes[(quote.quote_id, version)] = quote
    self._latest_quotes[quote.quote_id] = version

    # Write single new file (atomic)
    filepath = self._get_quote_path(quote.quote_id, quote.date, version)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(quote.model_dump_json(indent=2))
```

**Read Strategy - Load All Versions:**
```python
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
```

**Properties:**
- ✅ Naturally incremental (new files only)
- ✅ Immutable versions (never rewrite existing files)
- ✅ No compaction needed
- ✅ Each version is atomic

### Transaction Optimization

Transactions have special handling due to high volume and date partitioning:

**Write Strategy - Append to Financial Year File:**
```python
def save_transaction(self, transaction: Transaction) -> None:
    """Save transaction to memory and append to FY JSONL."""
    key = (transaction.transaction_id, transaction.date)
    if key in self._transactions:
        raise ValueError(f"Transaction already exists: {transaction.transaction_id}")

    self._transactions[key] = transaction

    # Append to financial year JSONL
    txn_file = self._get_transaction_file(transaction.date)
    txn_file.parent.mkdir(parents=True, exist_ok=True)
    with open(txn_file, "a") as f:
        f.write(transaction.model_dump_json() + "\n")

def update_transaction(self, transaction: Transaction) -> None:
    """Update transaction - append updated version to JSONL."""
    key = (transaction.transaction_id, transaction.date)
    if key not in self._transactions:
        raise KeyError(f"Transaction not found: {transaction.transaction_id}")

    self._transactions[key] = transaction

    # Append updated version (deduplication happens on load)
    txn_file = self._get_transaction_file(transaction.date)
    with open(txn_file, "a") as f:
        f.write(transaction.model_dump_json() + "\n")
```

**Read Strategy - Per-Year Deduplication:**
```python
def _load_transactions(self) -> None:
    """Load all transactions and compact per-year JSONL files."""
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

        # Compact this year's file only
        self._compact_transactions_for_file(txn_file, txns_for_year.values())
```

**Key Benefit:**
- Only compact ~500 transactions per year (not all years)
- Minimal write amplification for transaction updates
- Fast appends during classification workflow

## Public API Reference

### Client Operations

```python
def save_client(self, client: Client) -> None:
    """Save client to memory and persist to disk.

    Args:
        client: Client to save

    Notes:
        - Client ID matching is case-insensitive
        - Updates existing client if ID matches (case-insensitive)
        - Preserves the new client_id case when updating
    """

def get_client(self, client_id: str) -> Client:
    """Get client by ID (case-insensitive lookup).

    Args:
        client_id: Client business name (case-insensitive)

    Returns:
        Client matching the ID

    Raises:
        KeyError: If client not found
    """

def get_all_clients(self) -> list[Client]:
    """Get all clients.

    Returns:
        List of all clients (empty list if none exist)
    """

def client_exists(self, client_id: str) -> bool:
    """Check if client exists (case-insensitive).

    Args:
        client_id: Client business name

    Returns:
        True if client exists, False otherwise
    """
```

### Quote Operations

```python
def save_quote(self, quote: Quote) -> None:
    """Save quote as new version.

    Args:
        quote: Quote to save

    Notes:
        - Automatically determines next version number
        - Creates new versioned file (immutable)
        - Updates latest version index
    """

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

def get_quote_versions(self, quote_id: str) -> list[int]:
    """Get all version numbers for a quote.

    Args:
        quote_id: Quote identifier

    Returns:
        Sorted list of version numbers
    """

def get_all_quotes(self, latest_only: bool = True, financial_year: int | None = None) -> list[Quote]:
    """Get all quotes, optionally filtered.

    Args:
        latest_only: Only return latest version of each quote (default: True)
        financial_year: Filter by financial year (None = all years)

    Returns:
        List of quotes matching filters
    """
```

### Invoice Operations

```python
def save_invoice(self, invoice: Invoice) -> None:
    """Save invoice as new version."""

def get_invoice(self, invoice_id: str, date: date, version: int | None = None) -> Invoice:
    """Get invoice by ID and optional version (defaults to latest)."""

def get_invoice_versions(self, invoice_id: str) -> list[int]:
    """Get all version numbers for an invoice."""

def get_all_invoices(self, latest_only: bool = True, financial_year: int | None = None) -> list[Invoice]:
    """Get all invoices, optionally filtered."""
```

### Transaction Operations

```python
def save_transaction(self, transaction: Transaction) -> None:
    """Save new transaction.

    Args:
        transaction: Transaction to save

    Raises:
        ValueError: If transaction already exists (same ID and date)
    """

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

def transaction_exists(self, transaction_id: str, transaction_date: date) -> bool:
    """Check if transaction exists.

    Args:
        transaction_id: Transaction identifier
        transaction_date: Transaction date

    Returns:
        True if transaction exists, False otherwise
    """

def get_all_transactions(self, financial_year: int | None = None) -> list[Transaction]:
    """Get all transactions, optionally filtered by financial year.

    Args:
        financial_year: Filter by financial year (None = all years)

    Returns:
        List of transactions matching filter
    """
```

### Settings Operations

```python
def get_settings(self) -> Settings:
    """Get settings.

    Returns:
        Settings object

    Raises:
        FileNotFoundError: If settings not initialized
    """

def save_settings(self, settings: Settings) -> None:
    """Save settings to memory and disk.

    Args:
        settings: Settings to save
    """

def settings_exist(self) -> bool:
    """Check if settings are initialized.

    Returns:
        True if settings exist, False otherwise
    """
```

### Utility Operations

```python
def reload(self) -> None:
    """Reload all data from disk (discard in-memory changes).

    Notes:
        - Clears all in-memory state
        - Reloads from disk files
        - Useful when external process modified files
        - Any unsaved changes are lost
    """
```

## Usage Examples

### Basic Usage

```python
from small_business.storage import StorageRegistry
from small_business.models import Client

# Initialize storage (loads all data into memory)
storage = StorageRegistry(Path("./data"))

# Get client (dictionary lookup - fast)
client = storage.get_client("Woolworths")
print(f"Contact: {client.contact_email}")

# Update client (updates memory + appends to JSONL)
client.contact_email = "new@example.com"
storage.save_client(client)

# List all clients
for client in storage.get_all_clients():
    print(f"{client.client_id}: {client.business_name}")
```

### Working with Quotes

```python
from small_business.models import Quote, LineItem
from datetime import date
from decimal import Decimal

storage = StorageRegistry(Path("./data"))

# Create new quote
quote = Quote(
    quote_id="Q-20251123-001",
    date=date(2025, 11, 23),
    client_id="Woolworths",
    line_items=[
        LineItem(description="Consulting", quantity=10, unit_price=Decimal("150.00"))
    ]
)

# Save quote (creates version 1)
storage.save_quote(quote)

# Get latest version
latest = storage.get_quote("Q-20251123-001", quote.date)
print(f"Version: {storage.get_quote_versions(quote.quote_id)}")  # [1]

# Update quote (creates version 2)
quote.line_items.append(LineItem(description="Extra work", quantity=5, unit_price=Decimal("150.00")))
storage.save_quote(quote)

# Get specific version
v1 = storage.get_quote("Q-20251123-001", quote.date, version=1)
v2 = storage.get_quote("Q-20251123-001", quote.date, version=2)
```

### Working with Transactions

```python
from small_business.models import Transaction, JournalEntry
from datetime import date
from decimal import Decimal

storage = StorageRegistry(Path("./data"))

# Save transaction
txn = Transaction(
    transaction_id="TXN-001",
    date=date(2025, 11, 23),
    description="Payment received",
    entries=[
        JournalEntry(account_code="1100", debit=Decimal("1000.00"), credit=Decimal("0")),
        JournalEntry(account_code="4100", debit=Decimal("0"), credit=Decimal("1000.00"))
    ]
)
storage.save_transaction(txn)

# Update transaction (e.g., after classification)
txn.description = "Payment from Woolworths"
storage.update_transaction(txn)

# Get all transactions for current financial year
from small_business.models.financial_year import get_financial_year
current_fy = get_financial_year(date.today())
txns = storage.get_all_transactions(financial_year=current_fy)
```

### Document Generation Pattern

```python
from small_business.storage import StorageRegistry
from small_business.documents import generate_quote_document
from pathlib import Path

storage = StorageRegistry(Path("./data"))

# Load dependencies automatically from storage
quote = storage.get_quote("Q-20251123-001", date(2025, 11, 23))
client = storage.get_client(quote.client_id)
settings = storage.get_settings()

# Generate document
output_path = Path("./output/quote.docx")
generate_quote_document(quote, client, settings, output_path)
```

### Jupyter Notebook Pattern

```python
# One-time initialization
storage = StorageRegistry(Path("./data"))

# Fast exploratory queries (all in-memory)
clients_nsw = [c for c in storage.get_all_clients() if c.state == "NSW"]
high_value_quotes = [q for q in storage.get_all_quotes() if q.total_inc_gst > 10000]

# No cache invalidation worries - data is always current in-memory
```

## Migration from Functional API

### Breaking Changes

**OLD (Functional API):**
```python
from small_business.storage import load_client, save_client

client = load_client("Woolworths", data_dir)
save_client(client, data_dir)
```

**NEW (Registry API):**
```python
from small_business.storage import StorageRegistry

storage = StorageRegistry(data_dir)
client = storage.get_client("Woolworths")
storage.save_client(client)
```

### Migration Strategy

**Phase 1: Implement StorageRegistry**
- Create `registry.py` with full implementation
- Export only `StorageRegistry` from `__init__.py`
- Remove old `*_store.py` modules

**Phase 2: Update Internal Code**
- Migrate `documents/generator.py` to use registry
- Migrate `classification/storage_integration.py` to use registry
- Update all notebooks
- Update all tests

**Phase 3: Documentation**
- Update API docs
- Update examples and tutorials
- Update CLAUDE.md with new patterns

### Function Name Mapping

| Old Function | New Method | Notes |
|-------------|-----------|-------|
| `save_client(client, data_dir)` | `storage.save_client(client)` | No data_dir parameter |
| `load_client(id, data_dir)` | `storage.get_client(id)` | Renamed to `get_*` for consistency |
| `load_clients(data_dir)` | `storage.get_all_clients()` | Returns all clients |
| `save_quote(quote, data_dir)` | `storage.save_quote(quote)` | No data_dir parameter |
| `load_quote(id, date, data_dir, version)` | `storage.get_quote(id, date, version)` | No data_dir parameter |
| `save_transaction(txn, data_dir)` | `storage.save_transaction(txn)` | No data_dir parameter |
| `update_transaction(txn, data_dir)` | `storage.update_transaction(txn)` | Separate method for updates |
| `transaction_exists(id, date, data_dir)` | `storage.transaction_exists(id, date)` | No data_dir parameter |
| `load_settings(data_dir)` | `storage.get_settings()` | Returns settings object |
| `save_settings(settings, data_dir)` | `storage.save_settings(settings)` | No data_dir parameter |

### No Backward Compatibility

There are **no current users** of this package, so we will:
- ✅ Make a clean break from the old API
- ✅ Remove all old functional code
- ✅ No deprecation warnings needed
- ✅ Focus on the best API for the new design

## Testing Strategy

### Unit Tests for StorageRegistry

**Test Coverage:**
1. **Initialization**
   - Load empty data directory
   - Load populated data directory
   - Handle missing/corrupted files

2. **Client Operations**
   - Save new client
   - Update existing client (case-insensitive)
   - Get client (case-insensitive)
   - Get all clients
   - Client exists check

3. **Quote Operations**
   - Save new quote (creates version 1)
   - Save existing quote (creates next version)
   - Get latest version
   - Get specific version
   - Get all versions
   - Get all quotes (latest only vs all versions)

4. **Invoice Operations**
   - Same as quotes

5. **Transaction Operations**
   - Save new transaction
   - Update existing transaction
   - Get transaction by ID and date
   - Transaction exists check
   - Get all transactions
   - Get transactions by financial year

6. **Settings Operations**
   - Save settings
   - Get settings
   - Settings exist check

7. **Persistence**
   - JSONL compaction on load
   - Append-only writes during operation
   - Versioned files created correctly
   - Financial year organization

8. **In-Memory Behavior**
   - Multiple operations without reload
   - `reload()` discards in-memory changes
   - In-memory queries are fast

### Test Fixtures

```python
import pytest
from pathlib import Path
from small_business.storage import StorageRegistry

@pytest.fixture
def storage(tmp_path: Path) -> StorageRegistry:
    """Create storage registry with temporary data directory."""
    return StorageRegistry(tmp_path)

@pytest.fixture
def populated_storage(tmp_path: Path) -> StorageRegistry:
    """Create storage registry with sample data."""
    storage = StorageRegistry(tmp_path)

    # Add sample clients
    storage.save_client(Client(client_id="ClientA", business_name="Client A Pty Ltd"))
    storage.save_client(Client(client_id="ClientB", business_name="Client B Pty Ltd"))

    # Add sample quotes
    # ... etc

    return storage
```

### Performance Tests

```python
def test_large_dataset_performance(tmp_path: Path):
    """Test performance with realistic small business data volume."""
    storage = StorageRegistry(tmp_path)

    # Create 100 clients
    for i in range(100):
        client = Client(client_id=f"Client{i}", business_name=f"Client {i} Pty Ltd")
        storage.save_client(client)

    # Create 1000 quotes
    for i in range(1000):
        quote = Quote(...)
        storage.save_quote(quote)

    # Create 5000 transactions
    for i in range(5000):
        txn = Transaction(...)
        storage.save_transaction(txn)

    # Measure reload time
    import time
    start = time.time()
    storage.reload()
    elapsed = time.time() - start

    # Should load in < 1 second
    assert elapsed < 1.0
```

## Implementation Notes

### File Organization

**Disk Structure (Unchanged):**
```
data/
├── clients/
│   └── clients.jsonl              # JSONL with duplicates (compacted on load)
├── settings.json                   # Single JSON file
├── FY2024/
│   ├── quotes/
│   │   ├── Q-20241115-001_v1.json
│   │   ├── Q-20241115-001_v2.json
│   │   └── Q-20241201-001_v1.json
│   ├── invoices/
│   │   └── INV-20241130-001_v1.json
│   └── transactions.jsonl         # JSONL with duplicates (compacted on load)
└── FY2025/
    ├── quotes/
    ├── invoices/
    └── transactions.jsonl
```

### Error Handling

**Consistent Exception Types:**
- `KeyError` - Entity not found (clients, transactions)
- `FileNotFoundError` - Versioned entity not found (quotes, invoices, settings)
- `ValueError` - Duplicate entity (transactions)
- `ValidationError` - Pydantic validation failure

### Atomic Operations

Each save operation is atomic:
1. Update in-memory state
2. Append to disk file
3. If step 2 fails, in-memory state is corrupted (reload required)

**Note:** For critical operations, consider wrapping in try/except and calling `reload()` on failure.

### Thread Safety

**Not thread-safe** - `StorageRegistry` is designed for single-threaded use cases (notebooks, scripts, CLI tools). If concurrent access is needed in the future, consider:
- Thread locks around operations
- Copy-on-write semantics
- Separate registry instances per thread

### Future Enhancements

**Potential Features (YAGNI for now):**
1. **Atomic Transactions** - Batch multiple saves, rollback on error
2. **Change Hooks** - Callbacks when entities are saved/updated
3. **Search/Filter DSL** - More powerful query API
4. **Export/Import** - Bulk data operations
5. **Backup/Restore** - Snapshot and restore operations
6. **Audit Logs** - Track who changed what when
7. **Alternative Backends** - SQLite, PostgreSQL, cloud storage

**When to Add:**
- Only if actual user demand
- Only if simple in-memory approach becomes limiting
- Only if benefits outweigh complexity cost

## Conclusion

The in-memory `StorageRegistry` architecture is optimized for the small business domain:
- **Simple** - No cache complexity
- **Fast** - Dictionary lookups instead of file I/O
- **Predictable** - Data is always fresh after initialization
- **Scale-appropriate** - Exploits bounded context constraints

This design trades a small amount of memory (~20 MB) for radical simplification and performance. For small business accounting, this is the right trade-off.

### Design Principles Applied

1. **YAGNI** - No caching, lazy loading, or other premature optimization
2. **Domain-Driven** - Architecture exploits "small business" scale constraint
3. **Simplicity** - Complexity is more expensive than memory
4. **Consistency** - Single pattern for all entity types
5. **Predictability** - In-memory means data is always current

### Success Criteria

This design succeeds if:
- ✅ Code using storage layer is simpler and easier to understand
- ✅ Operations are fast (no noticeable latency)
- ✅ Tests are easier to write and more reliable
- ✅ Adding new entity types follows clear pattern
- ✅ Package works well for target users (small businesses)

### Risks and Mitigation

| Risk | Mitigation |
|------|-----------|
| **Scale beyond small business** | Document scale limits, provide migration path if needed |
| **Concurrent access** | Document single-threaded constraint, add locking if needed |
| **Data corruption from interrupted writes** | Reload on exception, consider atomic file writes |
| **Memory usage on resource-constrained systems** | Document requirements (recommend 4+ GB RAM) |

Overall, this design provides the right balance of simplicity and performance for small business accounting use cases.
