# UI Architecture Analysis for Small Business Package

**Date:** 2025-12-20
**Status:** Analysis & Recommendation
**Author:** AI-assisted architecture review

## Executive Summary

This document analyzes potential UI/frontend architectures for the small_business Python package, providing probability-weighted recommendations based on the existing codebase characteristics, user workflows, and architectural constraints.

**Recommended Approach:** FastAPI + HTMX + Jinja2 Templates (85% probability of success)

---

## Context & Requirements

### Current System Characteristics

- **Backend:** Python 3.13+ with Pydantic models
- **Storage:** Local-first, in-memory + disk (JSONL/JSON)
- **Scale:** Small business (single user or small team)
- **Data:** Sensitive financial information (requires security, backup, audit)
- **Workflows:** 5 main user journeys:
  1. Initialize business (one-time setup)
  2. Import bank statements (recurring)
  3. Classify transactions (interactive/batch)
  4. Generate reports (on-demand)
  5. Create documents (on-demand)

### UI Requirements

- **Forms-heavy:** Bank imports, client data, classification decisions
- **Tables:** Transaction lists, account balances, reports
- **File operations:** CSV upload, DOCX/PDF download
- **Interactive classification:** Accept/reject suggestions, manual classification
- **Batch operations:** Process multiple transactions
- **Long-running tasks:** Bank imports (30+ seconds)
- **Data visualization:** Balance sheet, P&L, charts (future)

---

## Architecture Options Analysis

### Option 1: FastAPI + HTMX + Jinja2 Templates ⭐️

**Probability of Correctness: 85%**

#### Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Browser (HTMX for partial updates)     │
│  ├─ Minimal JavaScript (~14KB)          │
│  └─ Progressive enhancement             │
└────────────┬────────────────────────────┘
             │ HTTP/HTML fragments
┌────────────▼────────────────────────────┐
│  FastAPI (Server-side rendering)        │
│  ├─ Jinja2 templates                    │
│  ├─ Session management                  │
│  └─ Direct access to StorageRegistry    │
└────────────┬────────────────────────────┘
             │ Direct function calls
┌────────────▼────────────────────────────┐
│  Existing Python Package                │
│  (bank, classification, reports, etc.)  │
└─────────────────────────────────────────┘
```

#### Strengths

- ✅ **Single language ecosystem** - Python + minimal JS via HTMX
- ✅ **Simple deployment** - Single process (uvicorn), runs locally or cloud
- ✅ **Perfect for form-heavy workflows** - Server-side rendering excels at CRUD
- ✅ **Progressive enhancement** - Works without JS, enhanced with it
- ✅ **Fast development** - Jinja2 templates + FastAPI = rapid iteration
- ✅ **Direct data access** - No serialization overhead, use StorageRegistry directly
- ✅ **Easy testing** - Playwright for E2E, pytest for API
- ✅ **Mature ecosystem** - FastAPI is production-ready, well-documented

#### Weaknesses

- ⚠️ **Less "app-like"** than SPA - But good enough for business CRUD
- ⚠️ **Requires running server** - Even locally (uvicorn process)
- ⚠️ **Page flashes** on full navigation - HTMX mitigates with partial updates

#### Technology Stack

```python
# Backend
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-multipart==0.0.6  # File uploads
python-jose[cryptography]  # JWT for auth
passlib[bcrypt]  # Password hashing

# Frontend (CDN - no build step)
htmx.org@1.9.10  # ~14KB
alpine.js@3.13.3  # Optional, for client-side state
```

#### Sample Implementation

```python
from fastapi import FastAPI, Request, UploadFile
from fastapi.templating import Jinja2Templates
from small_business.bank import import_bank_statement
from small_business.storage import StorageRegistry

app = FastAPI()
templates = Jinja2Templates(directory="templates")
storage = StorageRegistry(Path("~/business_data"))

@app.get("/import")
async def import_page(request: Request):
    return templates.TemplateResponse("import.html", {
        "request": request
    })

@app.post("/import")
async def import_csv(request: Request, file: UploadFile):
    # Call existing function directly
    results = import_bank_statement(
        file.file,
        bank_format,
        bank_name,
        account_name,
        bank_account_code,
        data_dir
    )
    # Return HTML fragment (HTMX pattern)
    return templates.TemplateResponse("import_results.html", {
        "request": request,
        "results": results
    })
```

#### Project Structure

```
small_business/
├── src/small_business/        # Existing package
├── web/                        # NEW: Web UI
│   ├── main.py                 # FastAPI app
│   ├── dependencies.py         # Shared dependencies
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── import_routes.py
│   │   ├── classify_routes.py
│   │   ├── report_routes.py
│   │   └── document_routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── import/
│   │   │   ├── upload.html
│   │   │   └── results.html
│   │   ├── classify/
│   │   │   ├── review.html
│   │   │   └── batch.html
│   │   └── reports/
│   │       └── generate.html
│   └── static/
│       ├── htmx.min.js
│       ├── alpine.min.js
│       ├── styles.css
│       └── app.js
├── tests/
│   └── web/
│       ├── test_routes.py
│       └── test_ui.py  # Playwright tests
└── docs/
```

---

### Option 2: Streamlit (Pure Python)

**Probability of Correctness: 75%**

#### Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Browser (Streamlit auto-generated UI)  │
└────────────┬────────────────────────────┘
             │ WebSocket + HTTP
┌────────────▼────────────────────────────┐
│  Streamlit Server                       │
│  └─ Python script reruns on interaction │
└────────────┬────────────────────────────┘
             │ Direct function calls
┌────────────▼────────────────────────────┐
│  Existing Python Package                │
└─────────────────────────────────────────┘
```

#### Strengths

- ✅ **Fastest MVP** - UI auto-generated from Python code
- ✅ **Pure Python** - No HTML/CSS/JS required
- ✅ **Excellent for data apps** - Charts, tables, forms built-in
- ✅ **Built-in widgets** - File upload, date picker, selectbox, etc.
- ✅ **Session state management** - Included
- ✅ **Zero build step** - `streamlit run app.py`

#### Weaknesses

- ⚠️ **Limited customization** - Hard to match specific designs
- ⚠️ **Script rerun model** - Entire script reruns on interaction (can be slow)
- ⚠️ **Not suitable for complex UX** - Multi-step wizards are tricky
- ⚠️ **Vendor lock-in** - Hard to migrate away later
- ⚠️ **Less professional appearance** - Looks like "data science tool"

#### Best Use Case

- Rapid MVP/prototype (weeks 1-2)
- Internal tools for technical users
- Proof of concept before committing to full web app

#### Sample Implementation

```python
import streamlit as st
from small_business.bank import import_bank_statement
from small_business.models import BankFormat

st.title("Bank Statement Import")

# File upload
uploaded_file = st.file_uploader("Choose CSV file", type="csv")

# Form inputs
bank_name = st.selectbox("Bank", ["ANZ", "Commonwealth", "Westpac"])
account_name = st.text_input("Account Name")

# Import button
if st.button("Import"):
    if uploaded_file:
        with st.spinner("Importing..."):
            results = import_bank_statement(
                uploaded_file,
                bank_format,
                bank_name,
                account_name,
                bank_account_code,
                data_dir
            )
        st.success(f"✅ Imported {results['imported']} transactions")
        st.info(f"ℹ️ Skipped {results['duplicates']} duplicates")
```

---

### Option 3: Desktop GUI (PySide6/Qt)

**Probability of Correctness: 70%**

#### Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Native Desktop Application (Qt)        │
│  ├─ QMainWindow, QWidgets               │
│  ├─ Qt Model/View for tables            │
│  └─ Qt Signals/Slots for events         │
└────────────┬────────────────────────────┘
             │ Direct function calls
┌────────────▼────────────────────────────┐
│  Existing Python Package                │
└─────────────────────────────────────────┘
```

#### Strengths

- ✅ **Fully offline** - No server required
- ✅ **Native performance** - Fast, responsive
- ✅ **Single executable** - PyInstaller for distribution
- ✅ **Rich widgets** - Tables, charts, file dialogs
- ✅ **Professional appearance** - Looks like "real" software
- ✅ **Cross-platform** - Windows, Mac, Linux

#### Weaknesses

- ⚠️ **Steeper learning curve** - Qt is complex
- ⚠️ **More code** - Verbose compared to web frameworks
- ⚠️ **Distribution complexity** - Packaging, updates, code signing
- ⚠️ **UI design requires** Qt Designer or hand-coding layouts
- ⚠️ **Not accessible remotely** - Must be installed locally

#### Best Use Case

- Desktop-first requirement
- Fully offline operation required
- Professional desktop app aesthetic needed

---

### Option 4: Modern SPA (FastAPI + React/Vue)

**Probability of Correctness: 60%**

#### Strengths

- ✅ **Modern UX** - Smooth, app-like experience
- ✅ **Rich interactivity** - Real-time updates, complex UI
- ✅ **Mobile-friendly** - Responsive design
- ✅ **Clear separation** - API + frontend decoupled

#### Weaknesses

- ⚠️ **Two tech stacks** - Python + JavaScript ecosystem
- ⚠️ **Complex build process** - npm, webpack/vite, bundling
- ⚠️ **Over-engineered** for CRUD operations
- ⚠️ **Serialization overhead** - Pydantic → JSON → JS objects
- ⚠️ **Longer development time** - 2-3x FastAPI+HTMX
- ⚠️ **More testing complexity** - Backend tests + frontend tests

#### Best Use Case

- Complex interactive UX required
- Mobile app needed
- Team has strong JavaScript experience

---

### Option 5: Terminal UI (Textual)

**Probability of Correctness: 50%**

#### Strengths

- ✅ **Terminal-native** - Keyboard-driven, fast for power users
- ✅ **Lightweight** - No browser required
- ✅ **Pure Python** - Textual framework

#### Weaknesses

- ⚠️ **Not for non-technical users** - Terminal intimidates business owners
- ⚠️ **Limited visual richness** - No charts, limited colors
- ⚠️ **Poor for documents** - Can't preview DOCX/PDF
- ⚠️ **CSV handling awkward** - File uploads/downloads unnatural

#### Best Use Case

- Developer tools only
- Power user CLI enhancement

---

### Option 6: Progressive Web App (PWA)

**Probability of Correctness: 65%**

#### Strengths

- ✅ **Offline-capable** - Service workers cache data
- ✅ **Installable** - Works like native app
- ✅ **Cross-platform** - One codebase
- ✅ **No app store** required

#### Weaknesses

- ⚠️ **Complex offline sync** - IndexedDB, conflict resolution
- ⚠️ **Still needs server** for initial load
- ⚠️ **Storage limits** - Browser quotas (50MB-1GB)
- ⚠️ **Complex state management** - Online/offline mode switching

#### Best Use Case

- Mobile + desktop required
- Online/offline hybrid workflows

---

## Critical Architecture Considerations

### 1. State Management Architecture

**Question:** Where does "current business context" live?

```python
# Option A: Session-based (web apps)
@app.get("/dashboard")
def dashboard(session: Session):
    business_id = session.get("current_business")
    storage = StorageRegistry(get_data_dir(business_id))
    # Load data for this session

# Option B: Singleton (desktop apps)
class AppState:
    _instance = None

    def __init__(self):
        self.storage = None
        self.current_business = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

**Recommendation:** Session-based for web, singleton for desktop

---

### 2. Multi-User & Concurrency

**Current State:** Single-user, file-based storage

**Critical Questions:**
- Will accountant + business owner access same data simultaneously?
- Are concurrent edits possible?
- Do we need row-level locking?

**Options:**

| Approach | Complexity | Concurrency Support | Migration Effort |
|----------|-----------|---------------------|------------------|
| File locking | Low | One writer at a time | Minimal |
| SQLite + WAL mode | Medium | Concurrent reads, single writer | Medium |
| PostgreSQL | High | Full ACID, row-level locks | High |

**Recommendation:**
1. **Phase 1:** Single-user with file locking (detect concurrent access)
2. **Phase 2:** SQLite with WAL mode if multi-user needed
3. **Phase 3:** PostgreSQL only if 10+ concurrent users

```python
# File locking example
import fcntl

class StorageRegistry:
    def __init__(self, data_dir: Path):
        self.lock_file = data_dir / ".lock"
        self.lock_fd = None

    def acquire_lock(self):
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise RuntimeError("Another instance is already running")
```

---

### 3. Authentication & Authorization

**Current State:** No authentication (file system = security boundary)

**Web App Requirements:**

```python
# Basic auth for localhost-only
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "secret")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401)
    return credentials.username
```

**Options:**

| Approach | Complexity | Security Level | Use Case |
|----------|-----------|----------------|----------|
| No auth | None | File system only | Localhost-only |
| HTTP Basic Auth | Low | Medium | LAN deployment |
| JWT tokens | Medium | High | Cloud deployment |
| OAuth2 | High | Very High | Enterprise SSO |

**Recommendation:**
- **Localhost:** No auth (default to 127.0.0.1)
- **LAN:** HTTP Basic Auth with HTTPS
- **Cloud:** JWT tokens + password reset flow

---

### 4. Data Migration & Schema Versioning

**Critical for Financial Software!**

```python
# Version all persisted data
{
    "schema_version": "2.1.0",
    "data": {
        "transaction_id": "...",
        # fields
    }
}

# Migration framework
class Migration:
    from_version: str
    to_version: str

    def migrate(self, data: dict) -> dict:
        raise NotImplementedError

class MigrationV1toV2(Migration):
    from_version = "1.0.0"
    to_version = "2.0.0"

    def migrate(self, data: dict) -> dict:
        # Add new field with default
        data['merchant_name'] = extract_merchant(data['description'])
        return data

# Registry of migrations
MIGRATIONS = [
    MigrationV1toV2(),
    MigrationV2toV3(),
]

def migrate_to_latest(data: dict, current_version: str) -> dict:
    for migration in MIGRATIONS:
        if migration.from_version == current_version:
            data = migration.migrate(data)
            current_version = migration.to_version
    return data
```

**Recommendation:**
1. Add `schema_version` field to ALL saved files immediately
2. Build migration framework before v1.0 release
3. Test migrations with real data regularly
4. Keep old data files for rollback

---

### 5. Backup & Disaster Recovery

**Financial Data = Must Not Lose**

```python
# Strategy 1: Automatic timestamped backups
from datetime import datetime
import shutil

def auto_backup(data_dir: Path):
    backup_dir = data_dir.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copytree(data_dir, backup_dir / timestamp)

    # Keep last 30 days only
    cleanup_old_backups(backup_dir, days=30)

# Strategy 2: Git-based versioning
def git_backup(data_dir: Path):
    subprocess.run(["git", "add", "."], cwd=data_dir)
    subprocess.run(
        ["git", "commit", "-m", f"Auto-backup {datetime.now()}"],
        cwd=data_dir
    )

# Strategy 3: Cloud sync
# Use Dropbox/OneDrive folder as data_dir
```

**Recommendations (Defense in Depth):**
1. ✅ **Local snapshots** - Daily timestamped copies
2. ✅ **Git versioning** - Commit after every mutation
3. ✅ **Cloud sync** - Dropbox/OneDrive/Google Drive
4. ✅ **Export backups** - Weekly full export to ZIP

**Backup Schedule:**
- **After every write:** Git commit
- **Daily:** Timestamped snapshot
- **Weekly:** Full export to ZIP
- **Continuous:** Cloud sync (if configured)

---

### 6. Audit Trail & Compliance

**Who Changed What When?**

```python
# Add audit fields to all models
from datetime import datetime
from pydantic import BaseModel, Field

class AuditMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str
    updated_at: datetime | None = None
    updated_by: str | None = None
    revision_history: list[dict] | None = None

class Transaction(AuditMixin):
    transaction_id: str
    description: str
    # ... existing fields

# Track all changes
def save_transaction(txn: Transaction, user: str):
    if txn.updated_at:
        # Existing transaction - record change
        if txn.revision_history is None:
            txn.revision_history = []

        txn.revision_history.append({
            "timestamp": datetime.now(),
            "user": user,
            "changes": diff(old_txn, txn)
        })

    txn.updated_at = datetime.now()
    txn.updated_by = user
    storage.save_transaction(txn)
```

**Compliance Requirements:**
- **GST/Tax:** Immutable transaction history (keep all versions)
- **Audit:** Who approved what classification when
- **Legal:** Ability to produce change log for any record

**Recommendation:** Implement before v1.0 (hard to add retroactively)

---

### 7. Long-Running Operations

**Bank imports, report generation can take 30+ seconds**

```python
# Problem: User waits, browser times out
results = import_bank_statement(...)  # Blocks UI!

# Solution 1: Background tasks (simple)
from fastapi import BackgroundTasks
from uuid import uuid4

tasks = {}  # In-memory task tracking

@app.post("/import")
async def import_csv(background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    tasks[task_id] = {"status": "processing", "progress": 0}

    background_tasks.add_task(run_import, task_id)

    return {"task_id": task_id, "status": "processing"}

@app.get("/import/status/{task_id}")
def check_status(task_id: str):
    return tasks.get(task_id, {"status": "not_found"})

def run_import(task_id: str):
    try:
        results = import_bank_statement(...)
        tasks[task_id] = {"status": "complete", "results": results}
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}

# Solution 2: WebSocket for real-time progress
from fastapi import WebSocket

@app.websocket("/ws/import")
async def import_websocket(websocket: WebSocket):
    await websocket.accept()

    for progress in import_with_progress(...):
        await websocket.send_json({
            "progress": progress.percent,
            "message": progress.current_step
        })

    await websocket.send_json({"status": "complete"})
```

**Recommendation:**
- **Phase 1:** Background tasks with polling
- **Phase 2:** WebSocket for real-time progress (if UX demands)

---

### 8. API Design Philosophy

**RESTful vs RPC Style?**

```python
# RESTful (resource-oriented)
GET    /transactions                    # List
POST   /transactions                    # Create
GET    /transactions/{id}               # Read
PATCH  /transactions/{id}               # Update
DELETE /transactions/{id}               # Delete

# RPC (action-oriented) - better for complex workflows
POST /workflows/import-bank-statement   # Action
POST /workflows/classify-transaction    # Action
POST /workflows/generate-balance-sheet  # Action

# Hybrid (recommended for this app)
# Resources for entities
GET  /clients
POST /clients
GET  /clients/{id}

# Workflows for business operations
POST /workflows/bank-import
POST /workflows/classify-batch
POST /workflows/generate-report
```

**Recommendation:** Hybrid approach
- **RESTful** for CRUD operations (clients, transactions)
- **RPC-style workflows** for multi-step business logic
- Keep existing Python functions as-is, thin API layer

---

### 9. Testing Strategy

```python
# Layer 1: Unit tests (existing)
def test_parse_csv():
    result = parse_csv(sample_csv, bank_format)
    assert len(result.transactions) == 10

# Layer 2: Integration tests (API)
from fastapi.testclient import TestClient

def test_import_endpoint():
    client = TestClient(app)
    response = client.post("/import", files={"file": open("test.csv")})
    assert response.status_code == 200
    assert response.json()["imported"] > 0

# Layer 3: E2E tests (Playwright)
from playwright.sync_api import sync_playwright

def test_import_workflow():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8000/import")
        page.set_input_files("#csv-upload", "test.csv")
        page.click("button:has-text('Import')")
        page.wait_for_selector(".success-message")
        assert "imported" in page.text_content(".results")

# Layer 4: Property-based tests (robustness)
from hypothesis import given, strategies as st

@given(csv_content=st.text())
def test_parse_never_crashes(csv_content):
    # Should handle any input gracefully
    try:
        parse_csv(csv_content, bank_format)
    except ValueError:
        pass  # Expected for invalid data
    # Should never raise unexpected exceptions
```

**Coverage Targets:**
- Unit tests: >90%
- Integration tests: All API endpoints
- E2E tests: Critical user paths (import, classify, report)
- Property tests: All parsers and validators

---

### 10. Deployment Architecture Options

```
┌─────────────────────────────────────────────────────┐
│ Option A: Localhost-Only (Simplest)                 │
├─────────────────────────────────────────────────────┤
│  User's Computer                                    │
│  ├─ Browser (http://localhost:8000)                 │
│  └─ FastAPI server (uvicorn)                        │
│     └─ Data files (~/business_data)                 │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Option B: LAN Deployment (Small Office)             │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐         ┌──────────────────┐      │
│  │ Client PC   │◄───────►│  Office Server   │      │
│  │ (browser)   │   LAN   │  ├─ FastAPI      │      │
│  └─────────────┘         │  └─ Data files   │      │
│                          └──────────────────┘      │
│  Network: 192.168.1.0/24                           │
│  Security: HTTP Basic Auth, HTTPS (self-signed)    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Option C: Cloud Deployment (Anywhere Access)        │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐         ┌──────────────────┐      │
│  │ Any device  │◄───────►│  Cloud VM        │      │
│  │ (browser)   │  HTTPS  │  ├─ FastAPI      │      │
│  └─────────────┘         │  ├─ PostgreSQL   │      │
│                          │  └─ Backups (S3) │      │
│                          └──────────────────┘      │
│  Security: JWT auth, SSL cert, encrypted backups   │
│  Cost: $10-30/month (DigitalOcean/Hetzner)        │
└─────────────────────────────────────────────────────┘
```

**Recommendation:** Design for Option A, enable Option B

- Default to localhost (127.0.0.1 only)
- Add `--host` flag for LAN deployment
- Document cloud deployment separately (advanced users)

---

## Recommended Phased Approach

### Phase 1: MVP with Streamlit (Weeks 1-2)

**Goal:** Validate workflows and gather user feedback

```python
# Single file: streamlit_app.py
import streamlit as st
from small_business.bank import import_bank_statement
from small_business.classification import classify_and_review
from small_business.reports import generate_balance_sheet

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Dashboard",
    "Import Bank Statement",
    "Classify Transactions",
    "Generate Reports"
])

if page == "Import Bank Statement":
    st.title("Import Bank Statement")
    # File upload UI
    # Call import_bank_statement()
    # Show results

# ... other pages
```

**Deliverable:** Working prototype with all 5 workflows (300-500 LOC)

---

### Phase 2: Production with FastAPI + HTMX (Weeks 3-6)

**Goal:** Production-ready web application

**Week 3:** Core infrastructure
- FastAPI app structure
- Jinja2 templates (base layout)
- Session management
- File upload/download

**Week 4:** Main workflows
- Bank import UI
- Transaction classification UI
- Report generation

**Week 5:** Polish & features
- Dashboard with stats
- Document generation
- Search/filter transactions

**Week 6:** Testing & deployment
- Playwright E2E tests
- Documentation
- Deployment script

**Deliverable:** Production web app (1000-1500 LOC Python + templates)

---

### Phase 3: Enhancement (Ongoing)

**Add as needed:**
- Charts and visualizations (Plotly/Chart.js)
- PDF preview in browser
- Keyboard shortcuts (AlpineJS)
- Dark mode
- Mobile-responsive design
- Export to Excel
- Email reports (scheduled)

---

## Technology Decision Matrix

| Requirement | FastAPI+HTMX | Streamlit | Desktop (Qt) | SPA (React) |
|-------------|--------------|-----------|--------------|-------------|
| **Fast MVP** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Production-ready** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Forms/CRUD** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Python-first** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Deployment simplicity** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Customization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Offline-first** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Modern UX** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Learning curve** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Mobile support** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

**Legend:** ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Adequate | ⭐⭐ Poor | ⭐ Not Suitable

---

## Final Recommendation

### Primary: FastAPI + HTMX + Jinja2

**Why this combination wins:**

1. **Leverages existing expertise** - Pure Python backend, minimal JS
2. **Perfect fit for use case** - Form-heavy CRUD operations
3. **Production-ready** - FastAPI is mature, well-tested, performant
4. **Simple deployment** - Single process, works locally or cloud
5. **Progressive enhancement** - Can add SPA features incrementally
6. **Fast development** - Jinja2 templates are quick to iterate
7. **Easy testing** - pytest for API, Playwright for E2E
8. **Flexible** - Can enhance with AlpineJS, WebSockets as needed

### Fallback: Streamlit for Rapid Prototyping

Use Streamlit to:
- Build quick MVP in week 1
- Validate workflows with users
- Prototype new features before adding to FastAPI app
- Create internal admin tools

### Not Recommended (Yet)

- **Desktop GUI** - Unless offline requirement is strict
- **SPA (React/Vue)** - Overkill for current requirements
- **Terminal UI** - Wrong audience (business owners, not developers)

---

## Next Steps

### Immediate Actions

1. **Create web/ directory structure**
   ```bash
   mkdir -p web/{routes,templates,static}
   touch web/main.py
   ```

2. **Install dependencies**
   ```bash
   uv add fastapi uvicorn jinja2 python-multipart
   ```

3. **Create base template**
   - `web/templates/base.html` with navigation
   - `web/static/styles.css` for basic styling

4. **Implement dashboard**
   - Show transaction count
   - Recent imports
   - Unclassified transaction count

5. **Build first workflow (bank import)**
   - File upload form
   - Call `import_bank_statement()`
   - Display results

### Success Metrics

- ✅ All 5 workflows implemented
- ✅ <2 seconds response time for forms
- ✅ <30 seconds for bank import (acceptable with progress indicator)
- ✅ >90% test coverage
- ✅ Works on Chrome, Firefox, Safari
- ✅ Responsive design (desktop + tablet)

---

## Appendix: Alternative Architectures Considered

### A. Jupyter Notebook Interface

**Rejected because:**
- Not suitable for non-technical users
- Poor for production workflows
- No authentication/multi-user

### B. Excel Add-in

**Rejected because:**
- Complex development (VBA or Office.js)
- Windows/Mac only
- Limited by Excel's capabilities

### C. Mobile App (React Native)

**Rejected because:**
- Mobile-first not required for accounting
- Desktop has better data entry UX
- Can use responsive web instead

### D. Electron Desktop App

**Rejected because:**
- Heavy runtime (~200MB)
- Still requires web development
- No advantage over web app for this use case

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [HTMX Documentation](https://htmx.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Playwright Testing](https://playwright.dev/python/)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-20
**Review Date:** After Phase 1 completion (target: 2026-01-15)
