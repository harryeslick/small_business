# Small Business Management System

This package is designed to be a simple tool for assisting with management of invoicing and account management for a sole trader small business in Australia. The package is designed for a simple sole trader small business, with low account complexity. The software should be easy to manage and make business management simpler, not more complex.

## Design Philosophy

The package should be simple and lightweight and portable. The software is designed to run locally on a single machine.

**Core Principles:**
- All datafiles stored as plain text formats: CSV for data,
- UNIX style plain text configuration
- Software is stateless, with account state stored in plain text and loaded at startup
- Written in Python 3.13+ using a terminal TUI user interface
- Prioritize simplicity and usability over feature complexity

## Architecture & Technical Stack

### Recommended Technologies

**TUI Framework:**
- **Textual**: Modern Python TUI framework with rich widgets and good documentation (recommended)
- **Rich**: For styled terminal output (can be used alongside Textual)

**Data Processing:**
- **Pandas**: CSV handling, data manipulation, reporting
- **Pydantic**: Data validation and settings management
- **dataclasses**: Built-in structured data

**Document Generation:**
- **Jinja2**: Template engine for Word documents
- **python-docx**: Word document manipulation
- **ReportLab** or **WeasyPrint**: Optional PDF generation

**Configuration & Data:**
- **PyYAML** or **ruamel.yaml**: YAML parsing
- **icalendar**: .ics file generation and parsing

## Accounting Features

### Chart of Accounts Structure

Full double-entry accounting system with the following account hierarchy:

```
Assets:
  - Current Assets (Bank accounts, Cash)
  - Fixed Assets (Equipment, Vehicles)

Income:
  - Service Income
  - Product Sales
  - Other Income

Expenses:
  - Travel
    - Flights
    - Vehicle
    - Accommodation
  - Materials
    - Stationery
    - Supplies
  - Utilities
    - Internet
    - Phone
    - Electricity
  - Professional Services
    - Accounting
    - Legal
  - Marketing & Advertising
  - Insurance
  - Depreciation

Liabilities:
  - Accounts Payable
  - Tax Liabilities (GST, Income Tax)

Equity:
  - Owner's Equity
  - Retained Earnings
```

**Account Rules:**
- Two-level hierarchy maximum
- Accounts stored in user-modifiable JSON file
- Default chart of accounts provided on initial setup

### Double Entry System

- Every transaction creates two entries (debit and credit)
- Bank imports create: Debit/Credit Bank Account + Credit/Debit corresponding account
- Transaction journal table stores all entries
- Ledger view shows account balances
- Ensure accounting equation always balances: Assets = Liabilities + Equity

### Australian BAS (Business Activity Statement) Compliance

**GST Tracking:**
- Track GST collected (on sales/invoices)
- Track GST paid (on expenses)
- GST calculation: 1/11th of GST-inclusive amounts
- Quarterly or monthly reporting capability
- Track GST registration status per invoice/expense

### Reports Required

- Profit & Loss Statement
- Balance Sheet
- Cash Flow Statement
- GST/BAS Report
- Expense by Category
- Income by Client/Job
- Tax summary reports

### Bank Statement Import

**Import Workflow:**
1. User selects CSV file(s) from one or more bank accounts
2. System maps columns (Date, Description, Amount, Balance)
3. Handle different bank CSV formats via configuration file
4. Detect and skip duplicate transactions
5. Show preview before finalizing import
6. Support multiple bank account imports

**Bank Format Configuration (YAML):**
```yaml
bank_formats:
  commonwealth:
    date_column: "Date"
    description_column: "Description"
    debit_column: "Debit"
    credit_column: "Credit"
    balance_column: "Balance"
    date_format: "%d/%m/%Y"
```

## Expense Tracking

### Classification System

**Semi-Autonomous Classification:**
- Rule-based matching using regex on transaction descriptions
- Machine learning suggestions based on historical classifications
- Confidence scoring for auto-suggestions:
  - **Medium confidence (>60%)**: Suggested, requires explicit confirmation
  - **Low confidence (<60%)**: Requires manual entry
- All software-generated classifications must be accepted by the user before being saved

**Classification Rules Format (YAML):**
```yaml
rules:
  - pattern: "WOOLWORTHS|COLES"
    account: "Expenses:Materials:Supplies"
    description: "Groceries/Supplies"
    gst_inclusive: true
  - pattern: "QANTAS|VIRGIN|JETSTAR"
    account: "Expenses:Travel:Flights"
    gst_inclusive: true
  - pattern: "TELSTRA|OPTUS"
    account: "Expenses:Utilities:Phone"
    gst_inclusive: true
```

**Rule Building:**
- System learns from user-accepted classifications
- User can manually add/edit rules
- Rules stored in separate editable file
- Priority system for conflicting rules

### Receipt Management

**Receipt Workflow:**
1. User attaches receipt file to transaction line item
2. System saves receipt to standard folder structure
3. File renamed using convention: `YYYY-MM-DD_AccountCode_VendorName_Amount.pdf`
4. Folder structure: `receipts/YYYY-YY/` YYYY-YY => finacial year eg 2025-26
5. Receipt filename linked to transaction ID in database

**Receipt Features:**
- Support PDF, JPG, PNG formats
- Optional OCR extraction (future enhancement)
- Reconciliation tracking: all expenses should have matching receipts
- Flag unreconciled expenses in reports

## Income Management

### Quote, Job, and Invoice Workflow

**Data Models:**

```
Quote:
  - quote_id (auto-generated: Q-YYYYMMDD-001)
  - client_id (links to client database)
  - date_created
  - date_valid_until
  - status (draft, sent, accepted, rejected, expired)
  - line_items[]
  - subtotal
  - gst_amount
  - total
  - terms_and_conditions
  - version (for modifications)
  - notes

Job:
  - job_id (auto-generated: J-YYYYMMDD-001)
  - quote_id (parent quote reference)
  - client_id
  - date_accepted
  - scheduled_date
  - status (scheduled, in_progress, completed, invoiced)
  - actual_costs[]
  - notes
  - calendar_event_id (link to .ics event)

Invoice:
  - invoice_id (auto-generated: INV-YYYYMMDD-001)
  - job_id (parent job reference)
  - client_id
  - date_issued
  - date_due
  - status (draft, sent, paid, overdue, cancelled)
  - payment_date
  - payment_amount
  - payment_reference
  - line_items[]
  - subtotal
  - gst_amount
  - total
  - version
  - notes
```

### Document Generation

**Word Document Templates (Jinja2):**
```
templates/
  - quote_template.docx
  - invoice_template.docx
  - statement_template.docx

Template Variables:
  - {{ business_details }}
  - {{ client_details }}
  - {{ quote_id / invoice_id }}
  - {{ date_issued }}
  - {{ line_items }}
  - {{ subtotal }}
  - {{ gst_amount }}
  - {{ total }}
  - {{ payment_terms }}
  - {{ notes }}
```

**Generation Process:**
1. User completes quote/invoice form in TUI
2. System validates data (GST calculation, totals, etc.)
3. plain text record saved for internal use and recording. 
4. Jinja2 populates Word template
5. Generated document saved to output folder
6. Optional PDF conversion

### Versioning System

**Modification Tracking:**
- Each modification creates new version
- File naming: `QuoteID_v1.json`, `QuoteID_v2.json`
- Track changes between versions (change log)
- Always reference latest version in active workflow
- Historical versions maintained for audit trail

**external modification handling**
- all records and files are stored as plain text, user may wish to make manual  changes which could have unintended errors.
- system should maintain a internal backup system using git.
- all changes made during a session should be written out to the plain text record database, then committed to the git tracking system.
- This is tracked for emergency use only, any other git functionality will be done manually, eg roll back to previous commit is not required as a function in this package. 

### Income Tracking

**Workflow Enforcement:**
- Ensure all accepted quotes become jobs
- Ensure all completed jobs get invoiced
- Track invoice payment status
- Alert on overdue invoices
- Prevent gaps in workflow (e.g., invoicing without a job)

### Calendar Integration

**ICS File Generation:**
- Create calendar events for:
  - Scheduled job dates
  - Invoice due dates
- Export to .ics format for import into calendar systems
- Support recurring reminders
- Include job details in event description

## Data Storage Structure

### Directory Layout

```
data/
  accounts/
    - chart_of_accounts.json          # Account hierarchy
    - classification_rules.yaml        # Transaction classification rules

  transactions/
    - journal_YYYY.csv                 # All transactions (double-entry)
    - ledger_YYYY.csv                  # Account balances

  bank_imports/
    - raw/                             # Original bank CSV files
      - account1_YYYY-MM-DD.csv
      - account2_YYYY-MM-DD.csv
    - processed/                       # Files moved after successful import

  receipts/
    - YYYY-YY/
        - YYYY-MM-DD_ExpTravel_Qantas_450.00.pdf

  quotes/
    - YYYY-YY/
      - Q-YYYYMMDD-001_v1.json
      - Q-YYYYMMDD-001_v2.json

  jobs/
    - YYYY-YY/
      - J-YYYYMMDD-001.json

  invoices/
    - YYYY-YY/
      - INV-YYYYMMDD-001_v1.json
      - generated/
        - INV-YYYYMMDD-001_v1.docx
        - INV-YYYYMMDD-001_v1.pdf

  clients/
    - clients.csv                      # Client database

  config/
    - settings.yaml                    # Application settings
    - bank_formats.yaml                # Bank CSV format definitions
    - user_config.yaml                 # Business details

  calendar/
    - events.ics                       # Calendar export file

  backups/                             # Optional backup location
    - YYYY-MM-DD/
``.git/                                # git repo for backup backup

### Data Validation

**Pydantic Models:**
- Define schemas for all data structures
- Validate GST calculations (eg. 10% in Australia, set in config) 
- Date range validation
- Required field enforcement
- Duplicate detection
- Data type enforcement

## TUI Interface Design

### Main Menu Structure

1. **Dashboard**
   - Summary of key metrics (income, expenses, profit)
   - Pending actions (overdue invoices, unclassified expenses)
   - Recent activity
   - Quick stats

2. **Accounting**
   - Bank import wizard
   - Expense classification
   - Receipt attachment
   - View/edit transactions
   - Account reconciliation

3. **Quotes & Jobs**
   - Create new quote
   - View/edit existing quotes
   - Convert quote to job
   - Manage job schedule
   - Job status tracking

4. **Invoices**
   - Create invoice from job
   - View/edit invoices
   - Record payments
   - Track overdue invoices
   - Send reminders

5. **Reports**
   - Profit & Loss
   - Balance Sheet
   - Cash Flow
   - GST/BAS Report
   - Expense by Category
   - Income by Client
   - Custom date ranges

6. **Settings**
   - Chart of accounts management
   - Classification rules editor
   - Bank format configuration
   - Business details
   - Template customization
   - Backup/export data

### Key Workflows

**Quick Expense Entry:**
- Fast path for manual expense entry
- Auto-suggest classification based on description
- Attach receipt inline
- Immediate validation

**Bank Import Wizard:**
- Step-by-step import process
- Column mapping interface
- Duplicate detection
- Preview before commit
- Batch classification

**Quote Creation Wizard:**
- Client selection/creation
- Line item builder
- GST auto-calculation
- Template preview
- Generate and save

**Invoice from Job:**
- Select completed job
- Pre-fill from job details
- Edit as needed
- Generate document
- Record in system

**BAS Report Generation:**
- Select date range (quarter/month)
- Calculate GST collected/paid
- Preview report
- Export to CSV/PDF
- Save for records

## Implementation Roadmap

### Phase 1: Foundation
- Set up project structure
- Define Pydantic models for core entities
- Implement chart of accounts system
- Configuration file management

### Phase 2: Accounting Core
- Bank CSV import functionality
- Transaction journal and ledger
- Double-entry accounting logic
- Basic classification system
- Receipt file management

### Phase 3: Expense Management
- Classification rules engine
- User acceptance workflow
- Rule learning system
- Receipt reconciliation
- Expense reports

### Phase 4: Income Management
- Quote creation and management
- Job tracking system
- Invoice generation
- Jinja2 template system
- Document export (Word/PDF)

### Phase 5: Reporting & Compliance
- P&L and Balance Sheet generation
- BAS/GST reporting
- Cash flow reports
- Calendar integration (.ics)
- Export functionality

### Phase 6: Polish & Enhancement
- Data validation improvements
- Backup and restore
- Performance optimization
- User documentation

### Phase 7: TUI interface

- Create basic TUI framework with Textual
- Advanced TUI features

## Future Enhancements

**Potential Features:**
- Employee/contractor payment tracking
- Inventory management
- OCR for receipt data extraction
- Advanced analytics and forecasting
- Multi-year comparative reports

## Data Backup & Export

**Backup Strategy:**
- All data is plain text (CSV/JSON/YAML) - easy to backup
- Manual backup: copy entire `data/` directory
- Version control backup using Git)

**Export Capabilities:**
- Export reports to CSV, PDF
- Export transaction data for external analysis
- Year-end archiving process
- Import/export for data migration

## Technical Considerations

**Error Handling:**
- Validate all user inputs
- Handle malformed CSV files gracefully
- Prevent data corruption with atomic writes
- Log errors for debugging
- User-friendly error messages in TUI

**Testing:**
- Unit tests for accounting logic (GST calculations, double-entry)
- Integration tests for workflows (quote → job → invoice)
- Test with real bank CSV samples
- Validate document generation
- Test data validation rules

**Security:**
- No sensitive data encryption (local machine only)
- File permission checks
- Input sanitization to prevent path traversal
- Secure template rendering (prevent code injection)

## Success Criteria

The system will be considered successful if it:
- Simplifies sole trader business management
- Reduces time spent on accounting tasks
- eliminates errors in missed or double-booked job appointmetns and late invoicing
- Ensures Australian tax compliance (BAS/GST)
- Maintains data integrity (double-entry balancing)
- Provides clear, actionable reports
- Remains simple and intuitive to use
- Stores all data in portable, readable formats
