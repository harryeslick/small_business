# Phase 4: Income Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build quote, job, and invoice management with Word document generation using Jinja2 templates and workflow enforcement.

**Architecture:** Implement storage modules for quotes, jobs, and invoices in financial-year-based directories, create Jinja2 template system for Word document generation, build workflow orchestration to ensure quotes → jobs → invoices progression, and implement calendar event (.ics) generation.

**Tech Stack:** Python 3.13+, Pydantic (Phase 1 models), python-docx (Word documents), Jinja2 (templating), icalendar (calendar events)

---

## Task 1: Quote Storage Module

**Files:**
- Create: `src/small_business/storage/quote_store.py`
- Test: `tests/storage/test_quote_store.py`

**Step 1: Write the failing test**

Create `tests/storage/test_quote_store.py`:


```python
"""Test quote storage."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import LineItem, Quote, QuoteStatus
from small_business.storage.quote_store import load_quote, load_quotes, save_quote

# NOTE: Client_id should use a human-readable string. not a sequential code, use business name eg client_id="Woolworths", these should be unique, no 2 businesses will have the same name. Job, quote, and invoice should be sequential ids (currently correct. )

def test_save_and_load_quote(tmp_path):
	"""Test saving and loading a quote."""
	data_dir = tmp_path / "data"

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="C-20251116-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)

	# Save quote
	save_quote(quote, data_dir)

	# Verify file exists
	quote_file = data_dir / "quotes" / "2025-26" / "Q-20251116-001_v1.json"
	assert quote_file.exists()

	# Load quote
	loaded = load_quote("Q-20251116-001", 1, data_dir)
	assert loaded.quote_id == "Q-20251116-001"
	assert loaded.version == 1
	assert len(loaded.line_items) == 1


def test_save_multiple_versions(tmp_path):
	"""Test saving multiple versions of a quote."""
	data_dir = tmp_path / "data"

	# Save version 1
	quote_v1 = Quote(
		quote_id="Q-20251116-001",
		client_id="C-20251116-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("100.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)
	save_quote(quote_v1, data_dir)

	# Save version 2 (modified)
	quote_v2 = Quote(
		quote_id="Q-20251116-001",
		client_id="C-20251116-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.SENT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("120.00"),  # Price increased
				gst_inclusive=False,
			)
		],
		version=2,
	)
	save_quote(quote_v2, data_dir)

	# Load both versions
	v1_loaded = load_quote("Q-20251116-001", 1, data_dir)
	v2_loaded = load_quote("Q-20251116-001", 2, data_dir)

	assert v1_loaded.line_items[0].unit_price == Decimal("100.00")
	assert v2_loaded.line_items[0].unit_price == Decimal("120.00")
	assert v2_loaded.status == QuoteStatus.SENT

NOTE: user should not have to know how many versions of the quote exist. load_quote without a version number should return the latest version, this should be the default. `load_quote("Q-20251116-001", None, data_dir)==v2_loaded`

def test_load_quotes_for_year(tmp_path):
	"""Test loading all quotes for a financial year."""
	data_dir = tmp_path / "data"

	# Save quotes in different years
	quote_2025 = Quote(
		quote_id="Q-20251116-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	quote_2024 = Quote(
		quote_id="Q-20240601-001",
		client_id="C-001",
		date_created=date(2024, 6, 1),
		date_valid_until=date(2024, 7, 1),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	save_quote(quote_2025, data_dir)
	save_quote(quote_2024, data_dir)

	# Load 2025-26 quotes
	quotes_2025 = load_quotes(data_dir, date(2025, 11, 16))
	assert len(quotes_2025) == 1
	assert quotes_2025[0].quote_id == "Q-20251116-001"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_quote_store.py::test_save_and_load_quote -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.storage.quote_store'"

**Step 3: Write minimal implementation**

Create `src/small_business/storage/quote_store.py`:

```python
"""Quote storage using JSON format."""

import json
from datetime import date
from pathlib import Path

from small_business.models import Quote
from small_business.storage.paths import get_financial_year_dir


def save_quote(quote: Quote, data_dir: Path) -> None:
	"""Save quote to JSON file.

	Saves to: data/quotes/YYYY-YY/QUOTE_ID_vVERSION.json

	Args:
		quote: Quote to save
		data_dir: Base data directory
	"""
	# Get financial year directory
	fy_dir = get_financial_year_dir(data_dir, quote.date_created)
	quotes_dir = data_dir / "quotes" / fy_dir.name
	quotes_dir.mkdir(parents=True, exist_ok=True)

	# Save quote file
	quote_file = quotes_dir / f"{quote.quote_id}_v{quote.version}.json"
	with open(quote_file, "w") as f:
		json_str = quote.model_dump_json(indent=2)
		f.write(json_str)


def load_quote(quote_id: str, version: int, data_dir: Path) -> Quote:
	"""Load a specific quote version.

	Args:
		quote_id: Quote ID
		version: Version number
		data_dir: Base data directory

	Returns:
		Quote

	Raises:
		FileNotFoundError: If quote file doesn't exist
	"""
	# Search through financial years
	quotes_base = data_dir / "quotes"
	if not quotes_base.exists():
		raise FileNotFoundError(f"Quote not found: {quote_id} v{version}")

	for fy_dir in quotes_base.iterdir():
		if fy_dir.is_dir():
			quote_file = fy_dir / f"{quote_id}_v{version}.json"
			if quote_file.exists():
				with open(quote_file) as f:
					data = json.load(f)
					return Quote.model_validate(data)

	raise FileNotFoundError(f"Quote not found: {quote_id} v{version}")


def load_quotes(data_dir: Path, txn_date: date) -> list[Quote]:
	"""Load all quotes for a financial year.

	Returns latest version of each quote.

	Args:
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		List of quotes
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	quotes_dir = data_dir / "quotes" / fy_dir.name

	if not quotes_dir.exists():
		return []

	# Load all quote files
	quotes = []
	quote_versions: dict[str, list[Quote]] = {}

	for quote_file in quotes_dir.glob("*.json"):
		with open(quote_file) as f:
			data = json.load(f)
			quote = Quote.model_validate(data)

			# Group by quote_id
			if quote.quote_id not in quote_versions:
				quote_versions[quote.quote_id] = []
			quote_versions[quote.quote_id].append(quote)

	# Return latest version of each quote
	for quote_id, versions in quote_versions.items():
		latest = max(versions, key=lambda q: q.version)
		quotes.append(latest)

	return quotes
```

Update `src/small_business/storage/__init__.py`:

```python
"""Storage and data persistence."""

NOTE: ALWAYS use absolute imports. small_business.paths not .paths 
from .paths import ensure_data_directory, get_financial_year_dir, get_transaction_file_path
from .quote_store import load_quote, load_quotes, save_quote
from .transaction_store import load_transactions, save_transaction, transaction_exists

__all__ = [
	"ensure_data_directory",
	"get_financial_year_dir",
	"get_transaction_file_path",
	"save_transaction",
	"load_transactions",
	"transaction_exists",
	"save_quote",
	"load_quote",
	"load_quotes",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_quote_store.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/storage/quote_store.py tests/storage/test_quote_store.py src/small_business/storage/__init__.py
git commit -m "feat: add quote storage module

Implement save/load functionality for quotes using JSON format
in financial-year-based directories. Supports versioning with
latest version retrieval.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Job and Invoice Storage Modules

**Files:**
- Create: `src/small_business/storage/job_store.py`
- Create: `src/small_business/storage/invoice_store.py`
- Test: `tests/storage/test_job_store.py`
- Test: `tests/storage/test_invoice_store.py`

**Step 1: Write the failing test**

Create `tests/storage/test_job_store.py`:

```python
"""Test job storage."""

from datetime import date
from pathlib import Path

from small_business.models import Job, JobStatus
from small_business.storage.job_store import load_job, load_jobs, save_job


def test_save_and_load_job(tmp_path):
	"""Test saving and loading a job."""
	data_dir = tmp_path / "data"

	job = Job(
		job_id="J-20251116-001",
		quote_id="Q-20251116-001",
		client_id="C-20251116-001",
		date_accepted=date(2025, 11, 16),
		scheduled_date=date(2025, 12, 1),
		status=JobStatus.SCHEDULED,
	)

	# Save job
	save_job(job, data_dir)

	# Verify file exists
	job_file = data_dir / "jobs" / "2025-26" / "J-20251116-001.json"
	assert job_file.exists()

	# Load job
	loaded = load_job("J-20251116-001", data_dir)
	assert loaded.job_id == "J-20251116-001"
	assert loaded.status == JobStatus.SCHEDULED


def test_load_jobs_for_year(tmp_path):
	"""Test loading all jobs for a financial year."""
	data_dir = tmp_path / "data"

	job1 = Job(
		job_id="J-20251116-001",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		status=JobStatus.SCHEDULED,
	)

	job2 = Job(
		job_id="J-20251117-001",
		client_id="C-002",
		date_accepted=date(2025, 11, 17),
		status=JobStatus.IN_PROGRESS,
	)

	save_job(job1, data_dir)
	save_job(job2, data_dir)

	jobs = load_jobs(data_dir, date(2025, 11, 16))
	assert len(jobs) == 2
```

Create `tests/storage/test_invoice_store.py`:

```python
"""Test invoice storage."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import Invoice, InvoiceStatus, LineItem
from small_business.storage.invoice_store import load_invoice, load_invoices, save_invoice


def test_save_and_load_invoice(tmp_path):
	"""Test saving and loading an invoice."""
	data_dir = tmp_path / "data"

	invoice = Invoice(
		invoice_id="INV-20251116-001",
		job_id="J-20251116-001",
		client_id="C-20251116-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		status=InvoiceStatus.DRAFT,
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)

	# Save invoice
	save_invoice(invoice, data_dir)

	# Verify file exists
	invoice_file = data_dir / "invoices" / "2025-26" / "INV-20251116-001_v1.json"
	assert invoice_file.exists()

	# Load invoice
	loaded = load_invoice("INV-20251116-001", 1, data_dir)
	assert loaded.invoice_id == "INV-20251116-001"
	assert loaded.version == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_job_store.py::test_save_and_load_job -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/storage/job_store.py`:

```python
"""Job storage using JSON format."""

import json
from datetime import date
from pathlib import Path

from small_business.models import Job
from small_business.storage.paths import get_financial_year_dir


def save_job(job: Job, data_dir: Path) -> None:
	"""Save job to JSON file.

	Args:
		job: Job to save
		data_dir: Base data directory
	"""
	fy_dir = get_financial_year_dir(data_dir, job.date_accepted)
	jobs_dir = data_dir / "jobs" / fy_dir.name
	jobs_dir.mkdir(parents=True, exist_ok=True)

	job_file = jobs_dir / f"{job.job_id}.json"
	with open(job_file, "w") as f:
		json_str = job.model_dump_json(indent=2)
		f.write(json_str)


def load_job(job_id: str, data_dir: Path) -> Job:
	"""Load a job by ID.

	Args:
		job_id: Job ID
		data_dir: Base data directory

	Returns:
		Job

	Raises:
		FileNotFoundError: If job doesn't exist
	"""
	jobs_base = data_dir / "jobs"
	if not jobs_base.exists():
		raise FileNotFoundError(f"Job not found: {job_id}")

	for fy_dir in jobs_base.iterdir():
		if fy_dir.is_dir():
			job_file = fy_dir / f"{job_id}.json"
			if job_file.exists():
				with open(job_file) as f:
					data = json.load(f)
					return Job.model_validate(data)

	raise FileNotFoundError(f"Job not found: {job_id}")


def load_jobs(data_dir: Path, txn_date: date) -> list[Job]:
	"""Load all jobs for a financial year.

	Args:
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		List of jobs
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	jobs_dir = data_dir / "jobs" / fy_dir.name

	if not jobs_dir.exists():
		return []

	jobs = []
	for job_file in jobs_dir.glob("*.json"):
		with open(job_file) as f:
			data = json.load(f)
			job = Job.model_validate(data)
			jobs.append(job)

	return jobs
```

Create `src/small_business/storage/invoice_store.py`:

```python
"""Invoice storage using JSON format."""

import json
from datetime import date
from pathlib import Path

from small_business.models import Invoice
from small_business.storage.paths import get_financial_year_dir


def save_invoice(invoice: Invoice, data_dir: Path) -> None:
	"""Save invoice to JSON file.

	Args:
		invoice: Invoice to save
		data_dir: Base data directory
	"""
	fy_dir = get_financial_year_dir(data_dir, invoice.date_issued)
	invoices_dir = data_dir / "invoices" / fy_dir.name
	invoices_dir.mkdir(parents=True, exist_ok=True)

	invoice_file = invoices_dir / f"{invoice.invoice_id}_v{invoice.version}.json"
	with open(invoice_file, "w") as f:
		json_str = invoice.model_dump_json(indent=2)
		f.write(json_str)


def load_invoice(invoice_id: str, version: int, data_dir: Path) -> Invoice:
	"""Load a specific invoice version.

	Args:
		invoice_id: Invoice ID
		version: Version number
		data_dir: Base data directory

	Returns:
		Invoice

	Raises:
		FileNotFoundError: If invoice doesn't exist
	"""
	invoices_base = data_dir / "invoices"
	if not invoices_base.exists():
		raise FileNotFoundError(f"Invoice not found: {invoice_id} v{version}")

	for fy_dir in invoices_base.iterdir():
		if fy_dir.is_dir():
			invoice_file = fy_dir / f"{invoice_id}_v{version}.json"
			if invoice_file.exists():
				with open(invoice_file) as f:
					data = json.load(f)
					return Invoice.model_validate(data)

	raise FileNotFoundError(f"Invoice not found: {invoice_id} v{version}")


def load_invoices(data_dir: Path, txn_date: date) -> list[Invoice]:
	"""Load all invoices for a financial year.

	Returns latest version of each invoice.

	Args:
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		List of invoices
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	invoices_dir = data_dir / "invoices" / fy_dir.name

	if not invoices_dir.exists():
		return []

	invoice_versions: dict[str, list[Invoice]] = {}

	for invoice_file in invoices_dir.glob("*.json"):
		with open(invoice_file) as f:
			data = json.load(f)
			invoice = Invoice.model_validate(data)

			if invoice.invoice_id not in invoice_versions:
				invoice_versions[invoice.invoice_id] = []
			invoice_versions[invoice.invoice_id].append(invoice)

	# Return latest version of each invoice
	invoices = []
	for invoice_id, versions in invoice_versions.items():
		latest = max(versions, key=lambda i: i.version)
		invoices.append(latest)

	return invoices
```

Update `src/small_business/storage/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_job_store.py tests/storage/test_invoice_store.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/storage/job_store.py src/small_business/storage/invoice_store.py tests/storage/test_job_store.py tests/storage/test_invoice_store.py src/small_business/storage/__init__.py
git commit -m "feat: add job and invoice storage modules

Implement JSON storage for jobs and invoices in financial-year
directories. Invoice storage supports versioning like quotes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Client Storage Module

**Files:**
- Create: `src/small_business/storage/client_store.py`
- Test: `tests/storage/test_client_store.py`

**Step 1: Write the failing test**

Create `tests/storage/test_client_store.py`:

```python
"""Test client storage."""

from pathlib import Path

from small_business.models import Client
from small_business.storage.client_store import load_client, load_clients, save_client


def test_save_and_load_client(tmp_path):
	"""Test saving and loading a client."""
	data_dir = tmp_path / "data"

	client = Client(
		client_id="C-20251116-001",
		name="Acme Corp",
		email="contact@acme.com",
		phone="0400 000 000",
		abn="12 345 678 901",
	)

	# Save client
	save_client(client, data_dir)

	# Verify file exists
	client_file = data_dir / "clients" / "clients.jsonl"
	assert client_file.exists()

	# Load client
	loaded = load_client("C-20251116-001", data_dir)
	assert loaded.client_id == "C-20251116-001"
	assert loaded.name == "Acme Corp"


def test_load_all_clients(tmp_path):
	"""Test loading all clients."""
	data_dir = tmp_path / "data"

	clients = [
		Client(client_id="C-001", name="Client 1", email="c1@example.com"),
		Client(client_id="C-002", name="Client 2", email="c2@example.com"),
	]

	for client in clients:
		save_client(client, data_dir)

	loaded = load_clients(data_dir)
	assert len(loaded) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_client_store.py::test_save_and_load_client -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/storage/client_store.py`:

```python
"""Client storage using JSONL format."""

import json
from pathlib import Path

from small_business.models import Client


def save_client(client: Client, data_dir: Path) -> None:
	"""Save or update client in JSONL file.

	Args:
		client: Client to save
		data_dir: Base data directory
	"""
	clients_dir = data_dir / "clients"
	clients_dir.mkdir(parents=True, exist_ok=True)
	clients_file = clients_dir / "clients.jsonl"

	# Load existing clients
	existing_clients = load_clients(data_dir)

	# Update or add client
	updated = False
	for i, existing in enumerate(existing_clients):
		if existing.client_id == client.client_id:
			existing_clients[i] = client
			updated = True
			break

	if not updated:
		existing_clients.append(client)

	# Rewrite file
	with open(clients_file, "w") as f:
		for c in existing_clients:
			f.write(c.model_dump_json() + "\n")


def load_client(client_id: str, data_dir: Path) -> Client:
	"""Load a client by ID.

	Args:
		client_id: Client ID
		data_dir: Base data directory

	Returns:
		Client

	Raises:
		KeyError: If client not found
	"""
	clients = load_clients(data_dir)
	for client in clients:
		if client.client_id == client_id:
			return client

	raise KeyError(f"Client not found: {client_id}")


def load_clients(data_dir: Path) -> list[Client]:
	"""Load all clients.

	Args:
		data_dir: Base data directory

	Returns:
		List of clients
	"""
	clients_file = data_dir / "clients" / "clients.jsonl"

	if not clients_file.exists():
		return []

	clients = []
	with open(clients_file) as f:
		for line in f:
			line = line.strip()
			if line:
				data = json.loads(line)
				client = Client.model_validate(data)
				clients.append(client)

	return clients
```

Update `src/small_business/storage/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_client_store.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/storage/client_store.py tests/storage/test_client_store.py src/small_business/storage/__init__.py
git commit -m "feat: add client storage module

Implement JSONL storage for clients with update capability.
Clients stored in single file for easy access.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Word Document Template System

**Files:**
- Create: `src/small_business/documents/__init__.py`
- Create: `src/small_business/documents/templates.py`
- Test: `tests/documents/test_templates.py`

**Step 1: Write the failing test**

Create `tests/documents/test_templates.py`:

```python
"""Test document template system."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.documents.templates import render_quote_context, render_invoice_context
from small_business.models import Client, Invoice, LineItem, Quote


def test_render_quote_context():
	"""Test rendering quote context for template."""
	client = Client(
		client_id="C-001",
		name="Acme Corp",
		email="contact@acme.com",
		phone="0400 000 000",
		abn="12 345 678 901",
	)

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			),
			LineItem(
				description="Training workshop",
				quantity=Decimal("1.0"),
				unit_price=Decimal("500.00"),
				gst_inclusive=False,
			),
		],
	)

	business_details = {
		"name": "My Business",
		"abn": "98 765 432 109",
		"email": "info@mybusiness.com",
		"phone": "0400 123 456",
		"address": "123 Business St, Sydney NSW 2000",
	}

	context = render_quote_context(quote, client, business_details)

	assert context["quote_id"] == "Q-20251116-001"
	assert context["client_name"] == "Acme Corp"
	assert context["business_name"] == "My Business"
	assert len(context["line_items"]) == 2
	assert context["subtotal"] == "2,000.00"
	assert context["gst_amount"] == "200.00"
	assert context["total"] == "2,200.00"
	assert context["date_created"] == "16/11/2025"


def test_render_invoice_context():
	"""Test rendering invoice context for template."""
	client = Client(
		client_id="C-001",
		name="Acme Corp",
		email="contact@acme.com",
	)

	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="C-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			)
		],
	)

	business_details = {"name": "My Business"}

	context = render_invoice_context(invoice, client, business_details)

	assert context["invoice_id"] == "INV-20251116-001"
	assert context["date_due"] == "16/12/2025"
	assert len(context["line_items"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/documents/test_templates.py::test_render_quote_context -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/documents/__init__.py`:

```python
"""Document generation functionality."""

from .templates import render_invoice_context, render_quote_context

__all__ = ["render_quote_context", "render_invoice_context"]
```

Create `src/small_business/documents/templates.py`:

```python
"""Template context rendering for documents."""

from decimal import Decimal

from small_business.models import Client, Invoice, Quote


def format_currency(amount: Decimal) -> str:
	"""Format currency with thousands separator.

	Args:
		amount: Decimal amount

	Returns:
		Formatted string (e.g., "1,234.56")
	"""
	return f"{amount:,.2f}"


def format_date(date_obj) -> str:
	"""Format date as DD/MM/YYYY.

	Args:
		date_obj: Date object

	Returns:
		Formatted date string
	"""
	return date_obj.strftime("%d/%m/%Y")


def render_quote_context(
	quote: Quote,
	client: Client,
	business_details: dict[str, str],
) -> dict:
	"""Render template context for a quote.

	Args:
		quote: Quote to render
		client: Client information
		business_details: Business information dict

	Returns:
		Context dictionary for template rendering
	"""
	# Format line items
	line_items = []
	for item in quote.line_items:
		line_items.append(
			{
				"description": item.description,
				"quantity": format_currency(item.quantity),
				"unit_price": format_currency(item.unit_price),
				"subtotal": format_currency(item.subtotal),
				"gst_inclusive": "Yes" if item.gst_inclusive else "No",
			}
		)

	return {
		"quote_id": quote.quote_id,
		"date_created": format_date(quote.date_created),
		"date_valid_until": format_date(quote.date_valid_until),
		"client_name": client.name,
		"client_email": client.email or "",
		"client_phone": client.phone or "",
		"client_abn": client.abn or "",
		"business_name": business_details.get("name", ""),
		"business_abn": business_details.get("abn", ""),
		"business_email": business_details.get("email", ""),
		"business_phone": business_details.get("phone", ""),
		"business_address": business_details.get("address", ""),
		"line_items": line_items,
		"subtotal": format_currency(quote.subtotal),
		"gst_amount": format_currency(quote.gst_amount),
		"total": format_currency(quote.total),
		"notes": quote.notes,
		"terms_and_conditions": quote.terms_and_conditions,
	}


def render_invoice_context(
	invoice: Invoice,
	client: Client,
	business_details: dict[str, str],
) -> dict:
	"""Render template context for an invoice.

	Args:
		invoice: Invoice to render
		client: Client information
		business_details: Business information dict

	Returns:
		Context dictionary for template rendering
	"""
	# Format line items
	line_items = []
	for item in invoice.line_items:
		line_items.append(
			{
				"description": item.description,
				"quantity": format_currency(item.quantity),
				"unit_price": format_currency(item.unit_price),
				"subtotal": format_currency(item.subtotal),
			}
		)

	context = {
		"invoice_id": invoice.invoice_id,
		"date_issued": format_date(invoice.date_issued),
		"date_due": format_date(invoice.date_due),
		"client_name": client.name,
		"client_email": client.email or "",
		"client_phone": client.phone or "",
		"client_abn": client.abn or "",
		"business_name": business_details.get("name", ""),
		"business_abn": business_details.get("abn", ""),
		"business_email": business_details.get("email", ""),
		"business_phone": business_details.get("phone", ""),
		"business_address": business_details.get("address", ""),
		"line_items": line_items,
		"subtotal": format_currency(invoice.subtotal),
		"gst_amount": format_currency(invoice.gst_amount),
		"total": format_currency(invoice.total),
		"notes": invoice.notes,
	}

	# Add payment information if paid
	if invoice.payment_date:
		context["payment_date"] = format_date(invoice.payment_date)
	if invoice.payment_amount:
		context["payment_amount"] = format_currency(invoice.payment_amount)
	if invoice.payment_reference:
		context["payment_reference"] = invoice.payment_reference

	return context
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/documents/test_templates.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/documents/ tests/documents/
git commit -m "feat: add document template context rendering

Implement context rendering for quotes and invoices with
formatted currency, dates, and line items ready for Jinja2
template population.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Word Document Generator

NOTE: 🚨CRITICAL! This section is ALL WRONG. generation of quotes and invoices should not create new documents from scratch using Document(). `generate_quote_document` and `generate_invoice_document` should both accept a template.docx containing Jinja2 template strings. the function should simply using Jinja2 to replace the template strings with the corresponding values from the Quote Client and Invoice objects. 

```python
def generate_invoice_document(
	invoice: Invoice,
	output_path: Path,
) -> None:
	# NOTE generate_invoice_document() should nnot generate a whole word document, it should accept invoice_template.docx and Invoice. The function should use Jinja to fill in the pregenerated word_template.docx and save as a new file. Client details should be retrieved from the client list using the client_id field in the invoice. bussiness_details should all be stored within the Client object. DO NOT USE `doc.add**` use Jinja2 to add the required details. Include in the docstring a list of all the Jinja template fields that are expected in the invoice_template.docx so that the user can create the invoice_template.docx
```

Update `src/small_business/documents/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/documents/test_generator.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/documents/generator.py tests/documents/test_generator.py src/small_business/documents/__init__.py
git commit -m "feat: add Word document generator

Implement quote and invoice document generation using python-docx.
Creates formatted Word documents with tables, headings, and totals.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Calendar Event Generator (.ics)

**Files:**
- Create: `src/small_business/calendar/__init__.py`
- Create: `src/small_business/calendar/events.py`
- Test: `tests/calendar/test_events.py`

**Step 1: Write the failing test**

Create `tests/calendar/test_events.py`:

```python
"""Test calendar event generation."""

from datetime import date, datetime, timedelta
from pathlib import Path

from small_business.calendar.events import create_job_event, create_invoice_due_event, save_events
from small_business.models import Job, Invoice, LineItem, JobStatus
from decimal import Decimal


def test_create_job_event():
	"""Test creating calendar event for a job."""
	job = Job(
		job_id="J-20251116-001",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		scheduled_date=date(2025, 12, 1),
		status=JobStatus.SCHEDULED,
		notes="Client meeting",
	)

	event = create_job_event(job, "Acme Corp")

	assert event["summary"] == "Job: J-20251116-001 - Acme Corp"
	assert "Scheduled job" in event["description"]
	assert event["dtstart"] == date(2025, 12, 1)


def test_create_invoice_due_event():
	"""Test creating calendar event for invoice due date."""
	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="C-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	event = create_invoice_due_event(invoice, "Acme Corp")

	assert event["summary"] == "Invoice Due: INV-20251116-001 - Acme Corp"
	assert "$110.00" in event["description"]  # Including GST
	assert event["dtstart"] == date(2025, 12, 16)


def test_save_events(tmp_path):
	"""Test saving events to .ics file."""
	job = Job(
		job_id="J-001",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		scheduled_date=date(2025, 12, 1),
		status=JobStatus.SCHEDULED,
	)

	events = [create_job_event(job, "Test Client")]
	output_file = tmp_path / "calendar.ics"

	save_events(events, output_file)

	assert output_file.exists()
	content = output_file.read_text()
	assert "BEGIN:VCALENDAR" in content
	assert "BEGIN:VEVENT" in content
	assert "J-001" in content
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/calendar/test_events.py::test_create_job_event -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/calendar/__init__.py`:

```python
"""Calendar event generation."""

from .events import create_invoice_due_event, create_job_event, save_events

__all__ = ["create_job_event", "create_invoice_due_event", "save_events"]
```

Create `src/small_business/calendar/events.py`:

```python
"""Calendar event generation (.ics format)."""

from datetime import date, datetime, timedelta
from pathlib import Path

from icalendar import Calendar, Event

from small_business.models import Invoice, Job


def create_job_event(job: Job, client_name: str) -> dict:
	"""Create calendar event for a scheduled job.

	Args:
		job: Job to create event for
		client_name: Client name for event summary

	Returns:
		Event dict with summary, description, dtstart
	"""
	scheduled = job.scheduled_date or job.date_accepted

	description = f"Scheduled job for {client_name}"
	if job.notes:
		description += f"\n\nNotes: {job.notes}"

	return {
		"summary": f"Job: {job.job_id} - {client_name}",
		"description": description,
		"dtstart": scheduled,
		"uid": job.job_id,
	}


def create_invoice_due_event(invoice: Invoice, client_name: str) -> dict:
	"""Create calendar event for invoice due date.

	Args:
		invoice: Invoice to create event for
		client_name: Client name for event summary

	Returns:
		Event dict with summary, description, dtstart
	"""
	description = f"Invoice due for {client_name}\nAmount: ${invoice.total}"

	return {
		"summary": f"Invoice Due: {invoice.invoice_id} - {client_name}",
		"description": description,
		"dtstart": invoice.date_due,
		"uid": invoice.invoice_id,
	}


def save_events(events: list[dict], output_file: Path) -> None:
	"""Save events to .ics file.

	Args:
		events: List of event dictionaries
		output_file: Path to save .ics file
	"""
	cal = Calendar()
	cal.add("prodid", "-//Small Business Management//EN")
	cal.add("version", "2.0")

	for event_data in events:
		event = Event()
		event.add("summary", event_data["summary"])
		event.add("description", event_data["description"])
		event.add("dtstart", event_data["dtstart"])
		event.add("uid", event_data["uid"])
		event.add("dtstamp", datetime.now())

		cal.add_component(event)

	# Save to file
	output_file.parent.mkdir(parents=True, exist_ok=True)
	with open(output_file, "wb") as f:
		f.write(cal.to_ical())
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/calendar/test_events.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/calendar/ tests/calendar/
git commit -m "feat: add calendar event generation

Implement .ics calendar event generation for scheduled jobs
and invoice due dates using icalendar library.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Workflow Orchestration

**Files:**
- Create: `src/small_business/workflow/__init__.py`
- Create: `src/small_business/workflow/income.py`
- Test: `tests/workflow/test_income.py`

**Step 1: Write the failing test**

Create `tests/workflow/test_income.py`:

```python
"""Test income workflow orchestration."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import Client, Job, JobStatus, LineItem, Quote, QuoteStatus
from small_business.storage.client_store import save_client
from small_business.storage.job_store import save_job
from small_business.storage.quote_store import save_quote
from small_business.workflow.income import (
	create_job_from_quote,
	create_invoice_from_job,
	get_accepted_quotes,
	get_completed_jobs,
)


def test_create_job_from_quote(tmp_path):
	"""Test creating a job from an accepted quote."""
	data_dir = tmp_path / "data"

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.ACCEPTED,
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	job = create_job_from_quote(quote, scheduled_date=date(2025, 12, 1))

	assert job.quote_id == "Q-20251116-001"
	assert job.client_id == "C-001"
	assert job.scheduled_date == date(2025, 12, 1)
	assert job.status == JobStatus.SCHEDULED


def test_create_invoice_from_job(tmp_path):
	"""Test creating an invoice from a completed job."""
	data_dir = tmp_path / "data"

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)
	save_quote(quote, data_dir)

	job = Job(
		job_id="J-20251116-001",
		quote_id="Q-20251116-001",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		status=JobStatus.COMPLETED,
	)

	invoice = create_invoice_from_job(job, quote, date_due=date(2025, 12, 31))

	assert invoice.job_id == "J-20251116-001"
	assert invoice.client_id == "C-001"
	assert invoice.date_due == date(2025, 12, 31)
	assert len(invoice.line_items) == 1
	assert invoice.line_items[0].description == "Service"


def test_get_accepted_quotes(tmp_path):
	"""Test getting all accepted quotes without jobs."""
	data_dir = tmp_path / "data"

	# Save accepted quote
	quote1 = Quote(
		quote_id="Q-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.ACCEPTED,
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	save_quote(quote1, data_dir)

	# Save draft quote (should not be returned)
	quote2 = Quote(
		quote_id="Q-002",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	save_quote(quote2, data_dir)

	# Get accepted quotes
	accepted = get_accepted_quotes(data_dir, date(2025, 11, 16))
	assert len(accepted) == 1
	assert accepted[0].quote_id == "Q-001"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/workflow/test_income.py::test_create_job_from_quote -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/workflow/__init__.py`:

```python
"""Workflow orchestration."""

from .income import (
	create_invoice_from_job,
	create_job_from_quote,
	get_accepted_quotes,
	get_completed_jobs,
)

__all__ = [
	"create_job_from_quote",
	"create_invoice_from_job",
	"get_accepted_quotes",
	"get_completed_jobs",
]
```

Create `src/small_business/workflow/income.py`:

```python
"""Income workflow orchestration."""

from datetime import date
from pathlib import Path

from small_business.models import Invoice, Job, JobStatus, Quote, QuoteStatus, InvoiceStatus
from small_business.storage.job_store import load_jobs
from small_business.storage.quote_store import load_quotes


def create_job_from_quote(quote: Quote, scheduled_date: date | None = None) -> Job:
	"""Create a job from an accepted quote.

	Args:
		quote: Accepted quote
		scheduled_date: When the job is scheduled

	Returns:
		New Job instance
	"""
	return Job(
		quote_id=quote.quote_id,
		client_id=quote.client_id,
		date_accepted=date.today(),
		scheduled_date=scheduled_date,
		status=JobStatus.SCHEDULED,
	)


def create_invoice_from_job(job: Job, quote: Quote, date_due: date) -> Invoice:
	"""Create an invoice from a completed job.

	Args:
		job: Completed job
		quote: Original quote (for line items)
		date_due: Invoice due date

	Returns:
		New Invoice instance
	"""
	return Invoice(
		job_id=job.job_id,
		client_id=job.client_id,
		date_issued=date.today(),
		date_due=date_due,
		status=InvoiceStatus.DRAFT,
		line_items=quote.line_items.copy(),  # Copy line items from quote
	)


def get_accepted_quotes(data_dir: Path, txn_date: date) -> list[Quote]:
	"""Get all accepted quotes that don't have jobs yet.

	Args:
		data_dir: Data directory
		txn_date: Date for financial year

	Returns:
		List of accepted quotes without jobs
	"""
	quotes = load_quotes(data_dir, txn_date)
	jobs = load_jobs(data_dir, txn_date)

	# Get quote IDs that already have jobs
	quote_ids_with_jobs = {job.quote_id for job in jobs if job.quote_id}

	# Filter for accepted quotes without jobs
	accepted_without_jobs = [
		q
		for q in quotes
		if q.status == QuoteStatus.ACCEPTED and q.quote_id not in quote_ids_with_jobs
	]

	return accepted_without_jobs


def get_completed_jobs(data_dir: Path, txn_date: date) -> list[Job]:
	"""Get all completed jobs that don't have invoices yet.

	Args:
		data_dir: Data directory
		txn_date: Date for financial year

	Returns:
		List of completed jobs without invoices
	"""
	from small_business.storage.invoice_store import load_invoices

	jobs = load_jobs(data_dir, txn_date)
	invoices = load_invoices(data_dir, txn_date)

	# Get job IDs that already have invoices
	job_ids_with_invoices = {inv.job_id for inv in invoices if inv.job_id}

	# Filter for completed jobs without invoices
	completed_without_invoices = [
		j
		for j in jobs
		if j.status == JobStatus.COMPLETED and j.job_id not in job_ids_with_invoices
	]

	return completed_without_invoices
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/workflow/test_income.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/workflow/ tests/workflow/
git commit -m "feat: add income workflow orchestration

Implement quote → job → invoice workflow helpers including
creation functions and gap detection (accepted quotes without
jobs, completed jobs without invoices).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Integration Test

**Files:**
- Create: `tests/integration/test_income_workflow_integration.py`

**Step 1: Write integration test**

Create `tests/integration/test_income_workflow_integration.py`:

```python
"""End-to-end integration test for income workflow."""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from small_business.calendar.events import create_invoice_due_event, create_job_event, save_events
from small_business.documents.generator import generate_invoice_document, generate_quote_document
from small_business.models import Client, JobStatus, LineItem, Quote, QuoteStatus
from small_business.storage.client_store import save_client
from small_business.storage.invoice_store import save_invoice
from small_business.storage.job_store import save_job
from small_business.storage.quote_store import save_quote
from small_business.workflow.income import (
	create_invoice_from_job,
	create_job_from_quote,
	get_accepted_quotes,
	get_completed_jobs,
)


def test_complete_income_workflow(tmp_path):
	"""Test complete workflow from quote to invoice with documents."""
	data_dir = tmp_path / "data"
	docs_dir = tmp_path / "documents"
	calendar_file = tmp_path / "calendar.ics"

	business_details = {
		"name": "Test Business",
		"abn": "12 345 678 901",
		"email": "info@test.com",
		"phone": "0400 000 000",
		"address": "123 Test St",
	}

	# Step 1: Save client
	# NOTE: all business_details should be stored in the Client object. client_id should be the "name" which must be unique. generate_quote_document() should only require: quote, client, quote_doc_path
	client = Client(
		client_id="C-20251116-001",
		name="Acme Corp",
		email="contact@acme.com",
		phone="0400 123 456",
	)
	save_client(client, data_dir)

	# Step 2: Create and save quote
	# NOTE: When in use, quote_id should be auto generated. not user specified. This may be fine for testing purposes. I dont understand exactly how this will be used, so it could be fine as is. 
	quote = Quote(
		quote_id="Q-20251116-001",
		client_id=client.client_id,
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			),
			LineItem(
				description="Training workshop",
				quantity=Decimal("1.0"),
				unit_price=Decimal("500.00"),
				gst_inclusive=False,
			),
		],
		terms_and_conditions="Payment due within 30 days",
	)
	# NOTE: Should save_quote be a method of Quote?
	save_quote(quote, data_dir)

	# Generate quote document
	quote_doc_path = docs_dir / "quotes" / f"{quote.quote_id}_v1.docx"
	quote_doc_path.parent.mkdir(parents=True, exist_ok=True)

	
	# NOTE: generate_quote_document() should lookup the client using the client_id field in the Quote object. user should not have to 
	generate_quote_document(quote, client, business_details, quote_doc_path)
	assert quote_doc_path.exists()

	# Step 3: Accept quote
	quote.status = QuoteStatus.ACCEPTED
	save_quote(quote, data_dir)

	# Step 4: Create job from accepted quote
	accepted_quotes = get_accepted_quotes(data_dir, date(2025, 11, 16))
	assert len(accepted_quotes) == 1

	job = create_job_from_quote(
		quote=accepted_quotes[0],
		scheduled_date=date(2025, 12, 1),
	)
	save_job(job, data_dir)

	# Create job calendar event
	job_event = create_job_event(job, client.name)
	events = [job_event]

	# Step 5: Complete job
	job.status = JobStatus.COMPLETED
	save_job(job, data_dir)

	# Step 6: Create invoice from completed job
	completed_jobs = get_completed_jobs(data_dir, date(2025, 11, 16))
	assert len(completed_jobs) == 1

	invoice = create_invoice_from_job(
		job=completed_jobs[0],
		quote=quote,
		date_due=date(2025, 12, 31),
	)
	save_invoice(invoice, data_dir)

	# Generate invoice document
	invoice_doc_path = docs_dir / "invoices" / f"{invoice.invoice_id}_v1.docx"
	invoice_doc_path.parent.mkdir(parents=True, exist_ok=True)
	generate_invoice_document(invoice, client, business_details, invoice_doc_path)
	assert invoice_doc_path.exists()

	# Create invoice due event
	invoice_event = create_invoice_due_event(invoice, client.name)
	events.append(invoice_event)

	# Save calendar events
	save_events(events, calendar_file)
	assert calendar_file.exists()

	# Step 7: Verify no gaps in workflow
	# No accepted quotes without jobs
	accepted_without_jobs = get_accepted_quotes(data_dir, date(2025, 11, 16))
	assert len(accepted_without_jobs) == 0

	# No completed jobs without invoices
	completed_without_invoices = get_completed_jobs(data_dir, date(2025, 11, 16))
	assert len(completed_without_invoices) == 0

	# Step 8: Verify totals
	assert invoice.total == quote.total
	assert len(invoice.line_items) == len(quote.line_items)
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_income_workflow_integration.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_income_workflow_integration.py
git commit -m "test: add income workflow integration tests

Add end-to-end test covering complete quote → job → invoice
workflow with document generation and calendar events.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

Phase 4 implementation delivers:

✅ **Quote storage** - JSON storage with versioning
✅ **Job storage** - JSON storage in financial year directories
✅ **Invoice storage** - JSON storage with versioning like quotes
✅ **Client storage** - JSONL storage with update capability
✅ **Template context rendering** - Format data for document generation
✅ **Word document generator** - Create formatted .docx files
✅ **Calendar events** - Generate .ics files for jobs and invoices
✅ **Workflow orchestration** - Quote → Job → Invoice helpers with gap detection
✅ **Integration tests** - End-to-end workflow validation

**Next Phase:** Phase 5 will implement reporting and BAS/GST compliance.

---

## Verification Checklist

Before marking Phase 4 complete, verify:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality: `uv run ruff check .`
- [ ] Formatting: `uv run ruff format .`
- [ ] Documentation builds: `mkdocs build`
- [ ] Manual test: Create quote, convert to job, create invoice
- [ ] Verify Word documents generate correctly
- [ ] Check calendar events import into calendar app
- [ ] Verify workflow enforcement (gaps detected)
