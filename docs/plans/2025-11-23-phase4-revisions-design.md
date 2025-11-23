# Phase 4 Revisions: API Simplification and Template-Based Documents

**Date:** 2025-11-23
**Status:** Design Complete
**Phase:** 4 (Income Management)

## Overview

This design document captures architectural improvements identified during Phase 4 planning review. These changes simplify the API surface, improve data model accuracy, and shift document generation from programmatic creation to template-based rendering.

## Core Design Principles

### 1. Auto-Lookup Dependencies
High-level functions should automatically load required dependencies using `data_dir` rather than requiring callers to pass everything explicitly.

**Before:**
```python
client = load_client(quote.client_id, data_dir)
settings = load_settings(data_dir)
generate_quote_document(quote, client, settings, output_path)
```

**After:**
```python
generate_quote_document(quote, output_path, data_dir)  # Auto-loads client & settings
```

### 2. Sensible Defaults for Optional Parameters
Optional parameters should default to the most common use case.

**Example:** Loading latest version is more common than loading specific versions:
```python
load_quote(quote_id, data_dir, version=None)  # Defaults to latest
load_quote(quote_id, data_dir, version=1)     # Explicit version when needed
```

### 3. Human-Readable Identifiers Where Appropriate
Use business-meaningful identifiers for entities that have natural unique keys.

**Client IDs:** Business name (e.g., "Woolworths") instead of generated codes ("C-20251116-001")
**Quote/Job/Invoice IDs:** Keep sequential generation for audit trail and uniqueness

### 4. Template-Based Document Generation
Use Jinja2 templates for Word documents rather than programmatic document assembly. This separates presentation from logic and enables non-developers to modify document layouts.

### 5. Settings-Based Configuration
Store configurable paths and business details in Settings model rather than hard-coding or passing as arguments.

---

## Design Changes

### 1. Client Model Restructure

**Current state:**
```python
class Client(BaseModel):
    client_id: str = Field(default_factory=generate_client_id)  # "C-YYYYMMDD-###"
    name: str
    email: EmailStr | None
    phone: str | None
    abn: str | None
    notes: str = ""
```

**New design:**
```python
class Client(BaseModel):
    """Client/customer business information."""

    # Identity - business name is the unique identifier
    client_id: str = Field(min_length=1)  # e.g., "Woolworths", "Acme Corp"
    name: str = Field(min_length=1)  # Display name (usually same as client_id)

    # Contact information
    email: EmailStr | None = None
    phone: str | None = None
    contact_person: str | None = None

    # Business information
    abn: str | None = None

    # Structured address fields (for validation/formatting)
    street_address: str | None = None
    suburb: str | None = None
    state: str | None = None
    postcode: str | None = None

    # Formatted address for display/documents
    formatted_address: str | None = None

    # Billing address (if different from physical)
    billing_street_address: str | None = None
    billing_suburb: str | None = None
    billing_state: str | None = None
    billing_postcode: str | None = None
    billing_formatted_address: str | None = None

    # Additional
    notes: str = ""
```

**Rationale:**
- Business name is naturally unique and more meaningful than generated IDs
- Structured address fields enable validation while formatted fields provide display flexibility
- Separate billing address supports common business scenarios
- Contact person helps identify who to communicate with at larger organizations

**Breaking changes:**
- `generate_client_id()` utility removed
- Existing client records need manual migration to business-name IDs
- All test fixtures need updating

---

### 2. Settings Model Extensions

**Add template configuration:**
```python
class Settings(BaseModel):
    """Application settings and constants."""

    # ... existing fields ...

    # Template paths
    quote_template_path: str = "templates/quote_template.docx"
    invoice_template_path: str = "templates/invoice_template.docx"
```

**Rationale:**
- Centralizes configuration
- Allows template customization without code changes
- Enables different templates for different use cases (e.g., detailed vs. summary invoices)

---

### 3. Storage Layer Improvements

#### 3.1 Case-Insensitive Client Lookups

**Implementation:**
```python
def save_client(client: Client, data_dir: Path) -> None:
    """Save or update client with case-insensitive ID uniqueness.

    Raises:
        ValueError: If a different client exists with same name (different case)
    """
    existing_clients = load_clients(data_dir)
    normalized_id = client.client_id.lower()

    # Find existing client with same normalized ID
    for i, existing in enumerate(existing_clients):
        if existing.client_id.lower() == normalized_id:
            # Update existing record
            existing_clients[i] = client
            break
    else:
        # New client
        existing_clients.append(client)

    # Rewrite file
    clients_file = data_dir / "clients" / "clients.jsonl"
    clients_file.parent.mkdir(parents=True, exist_ok=True)
    with open(clients_file, "w") as f:
        for c in existing_clients:
            f.write(c.model_dump_json() + "\n")


def load_client(client_id: str, data_dir: Path) -> Client:
    """Load client by ID (case-insensitive lookup).

    Args:
        client_id: Client business name
        data_dir: Base data directory

    Returns:
        Client matching the ID (case-insensitive)

    Raises:
        KeyError: If client not found
    """
    clients = load_clients(data_dir)
    normalized_id = client_id.lower()

    for client in clients:
        if client.client_id.lower() == normalized_id:
            return client

    raise KeyError(f"Client not found: {client_id}")
```

**Rationale:**
- Prevents duplicate clients due to case differences ("Woolworths" vs. "woolworths")
- More forgiving for user input
- Maintains canonical case in storage

#### 3.2 Optional Version Parameters

**Current:**
```python
load_quote(quote_id: str, version: int, data_dir: Path) -> Quote
load_invoice(invoice_id: str, version: int, data_dir: Path) -> Invoice
```

**New:**
```python
def load_quote(quote_id: str, data_dir: Path, version: int | None = None) -> Quote:
    """Load a quote, defaulting to latest version if not specified.

    Args:
        quote_id: Quote identifier
        data_dir: Base data directory
        version: Specific version to load, or None for latest

    Returns:
        Quote instance

    Raises:
        FileNotFoundError: If quote not found
    """
    if version is None:
        return _load_latest_quote(quote_id, data_dir)
    else:
        return _load_quote_version(quote_id, version, data_dir)


def _load_latest_quote(quote_id: str, data_dir: Path) -> Quote:
    """Load the latest version of a quote."""
    quotes_base = data_dir / "quotes"
    if not quotes_base.exists():
        raise FileNotFoundError(f"Quote not found: {quote_id}")

    # Find all versions of this quote
    versions = []
    for fy_dir in quotes_base.iterdir():
        if fy_dir.is_dir():
            for quote_file in fy_dir.glob(f"{quote_id}_v*.json"):
                # Extract version number from filename
                version_str = quote_file.stem.split('_v')[1]
                versions.append((int(version_str), quote_file))

    if not versions:
        raise FileNotFoundError(f"Quote not found: {quote_id}")

    # Load highest version
    _, latest_file = max(versions, key=lambda x: x[0])
    with open(latest_file) as f:
        data = json.load(f)
        return Quote.model_validate(data)


def _load_quote_version(quote_id: str, version: int, data_dir: Path) -> Quote:
    """Load a specific version of a quote."""
    # ... existing implementation ...
```

**Apply same pattern to `load_invoice()`.**

**Rationale:**
- Most operations work with latest version
- Reduces boilerplate in calling code
- Explicit version still available for audit/history access

---

### 4. Document Generation Overhaul

#### 4.1 Jinja2 Template System

**New dependency:** `python-docxtpl` (Jinja2 templating for Word documents)

**Template rendering:**
```python
def render_quote_context(
    quote: Quote,
    client: Client,
    settings: Settings,  # Changed from dict[str, str]
) -> dict:
    """Render template context for a quote.

    Args:
        quote: Quote to render
        client: Client information
        settings: Application settings (for business details)

    Returns:
        Context dictionary for Jinja2 template rendering
    """
    # Format line items
    line_items = []
    for item in quote.line_items:
        line_items.append({
            "description": item.description,
            "quantity": format_currency(item.quantity),
            "unit_price": format_currency(item.unit_price),
            "subtotal": format_currency(item.subtotal),
            "gst_inclusive": "Yes" if item.gst_inclusive else "No",
        })

    return {
        # Quote details
        "quote_id": quote.quote_id,
        "date_created": format_date(quote.date_created),
        "date_valid_until": format_date(quote.date_valid_until),
        "status": quote.status.value,
        "version": quote.version,

        # Client details
        "client_name": client.name,
        "client_email": client.email or "",
        "client_phone": client.phone or "",
        "client_abn": client.abn or "",
        "client_address": client.formatted_address or "",
        "client_contact_person": client.contact_person or "",

        # Our business details (from Settings)
        "business_name": settings.business_name,
        "business_abn": settings.business_abn,
        "business_email": settings.business_email,
        "business_phone": settings.business_phone,
        "business_address": settings.business_address,

        # Line items and totals
        "line_items": line_items,
        "subtotal": format_currency(quote.subtotal),
        "gst_amount": format_currency(quote.gst_amount),
        "total": format_currency(quote.total),

        # Additional
        "notes": quote.notes,
        "terms_and_conditions": quote.terms_and_conditions,
    }
```

**Apply same pattern to `render_invoice_context()`.**

#### 4.2 Simplified Document Generation

**Current (wrong):**
```python
def generate_quote_document(
    quote: Quote,
    client: Client,
    business_details: dict,
    output_path: Path,
) -> None:
    """Generate quote using Document().add_*() methods."""
    doc = Document()
    doc.add_heading(f"Quote {quote.quote_id}")
    # ... many lines of doc.add_* calls ...
```

**New (correct):**
```python
def generate_quote_document(
    quote: Quote,
    output_path: Path,
    data_dir: Path,
) -> None:
    """Generate quote document from Jinja2 Word template.

    Auto-loads client and settings. Template is configured in Settings.

    Template variables available (see render_quote_context for full list):
    - Quote: quote_id, date_created, date_valid_until, status, version
    - Client: client_name, client_email, client_phone, client_abn, client_address
    - Business: business_name, business_abn, business_email, business_phone, business_address
    - Items: line_items[] (description, quantity, unit_price, subtotal)
    - Totals: subtotal, gst_amount, total
    - Notes: notes, terms_and_conditions

    Args:
        quote: Quote to generate document for
        output_path: Where to save the .docx file
        data_dir: Base data directory (for loading client/settings)

    Raises:
        KeyError: If client not found
        FileNotFoundError: If template not found
    """
    from docxtpl import DocxTemplate

    # Auto-load dependencies
    settings = load_settings(data_dir)
    client = load_client(quote.client_id, data_dir)
    template_path = Path(settings.quote_template_path)

    # Render context
    context = render_quote_context(quote, client, settings)

    # Load template and render
    doc = DocxTemplate(template_path)
    doc.render(context)

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
```

**Apply same pattern to `generate_invoice_document()`.**

**Rationale:**
- Separates document layout (in template) from data/logic (in code)
- Non-developers can modify document appearance
- Simpler API - just quote, output path, and data_dir
- Easier to test - mock the template rendering

---

### 5. Calendar Events Auto-Lookup

**Current:**
```python
def create_job_event(job: Job, client_name: str) -> dict:
    """Requires caller to provide client name."""
    pass
```

**New:**
```python
def create_job_event(job: Job, data_dir: Path) -> dict:
    """Create calendar event for a scheduled job.

    Auto-looks up client name from job.client_id.

    Args:
        job: Job to create event for
        data_dir: Base data directory (for client lookup)

    Returns:
        Event dict with summary, description, dtstart, uid
    """
    # Auto-lookup client
    client = load_client(job.client_id, data_dir)

    scheduled = job.scheduled_date or job.date_accepted

    description = f"Scheduled job for {client.name}"
    if job.notes:
        description += f"\n\nNotes: {job.notes}"

    return {
        "summary": f"Job: {job.job_id} - {client.name}",
        "description": description,
        "dtstart": scheduled,
        "uid": job.job_id,
    }
```

**Apply same pattern to `create_invoice_due_event()`.**

---

### 6. Workflow Function Updates

**Update signatures to accept data_dir where needed:**

```python
def create_job_from_quote(
    quote: Quote,
    scheduled_date: date | None = None,
) -> Job:
    """Create a job from an accepted quote.

    Note: No data_dir needed - just copies data from quote.
    """
    return Job(
        quote_id=quote.quote_id,
        client_id=quote.client_id,  # Business name flows through
        date_accepted=date.today(),
        scheduled_date=scheduled_date,
        status=JobStatus.SCHEDULED,
    )
```

No changes needed here - client_id is already in the quote.

---

## Migration Plan

### Breaking Changes

1. **Client IDs** - Existing "C-YYYYMMDD-###" format must be manually converted to business names
2. **Document generation signatures** - All calls need updating to new parameters
3. **Template rendering** - Functions take Settings instead of dict
4. **Calendar events** - Take data_dir instead of client_name string

### Implementation Order

1. **Update models** (Client, Settings) - Foundation changes
2. **Update storage layer** - Case-insensitive lookups, optional versions
3. **Update document generation** - Jinja2 templates, auto-lookup
4. **Update calendar events** - Auto-lookup client names
5. **Update workflow functions** - Propagate data_dir parameter
6. **Update all tests** - New client_id format, new signatures
7. **Create template examples** - Sample quote_template.docx and invoice_template.docx

### Testing Strategy

- Unit tests for case-insensitive client lookups
- Unit tests for version defaulting logic
- Integration tests for document generation (with test templates)
- Integration tests for complete workflow with new signatures
- Verify backward compatibility where possible (e.g., explicit version still works)

---

## Files Requiring Updates

### Models
- `src/small_business/models/client.py` - Add fields, remove auto-ID
- `src/small_business/models/config.py` - Add template paths
- `src/small_business/models/utils.py` - Remove `generate_client_id()`
- `tests/models/test_client.py` - Update for new structure

### Storage
- `src/small_business/storage/client_store.py` - Case-insensitive lookups
- `src/small_business/storage/quote_store.py` - Optional version param
- `src/small_business/storage/invoice_store.py` - Optional version param
- `tests/storage/test_client_store.py` - Case-insensitive tests
- `tests/storage/test_quote_store.py` - Version defaulting tests
- `tests/storage/test_invoice_store.py` - Version defaulting tests

### Documents
- `src/small_business/documents/templates.py` - Settings instead of dict
- `src/small_business/documents/generator.py` - Jinja2 templates, auto-lookup
- `tests/documents/test_templates.py` - Update for Settings
- `tests/documents/test_generator.py` - Complete rewrite for Jinja2

### Calendar
- `src/small_business/calendar/events.py` - Auto-lookup client names
- `tests/calendar/test_events.py` - Update signatures

### Integration Tests
- `tests/integration/test_income_workflow_integration.py` - Update all signatures

### Templates (NEW)
- `templates/quote_template.docx` - Sample Jinja2 template
- `templates/invoice_template.docx` - Sample Jinja2 template

---

## Dependencies

**Add:**
- `python-docxtpl` - Jinja2 templating for Word documents

**Remove:**
- None (python-docx may still be used by docxtpl)

---

## Verification Checklist

Before marking complete, verify:

- [ ] All tests pass with new client_id format
- [ ] Case-insensitive client lookups work correctly
- [ ] Load quote/invoice without version returns latest
- [ ] Document generation uses Jinja2 templates
- [ ] Template examples render correctly in Word
- [ ] Calendar events auto-lookup client names
- [ ] Integration test passes with new signatures
- [ ] Settings model includes template paths
- [ ] CLAUDE.md updated with architectural principles

---

## Future Enhancements

1. **Template validation** - Verify required Jinja2 variables exist in template
2. **Address formatting** - Auto-format structured address fields into formatted_address
3. **Multiple template support** - Different templates for different scenarios
4. **Client import** - Bulk import clients from CSV with business name as ID
5. **Client merge** - Handle duplicate clients with different names
