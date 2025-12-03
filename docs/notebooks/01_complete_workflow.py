# %% [markdown]
# # Complete Workflow: Arts Business Example
#
# This notebook demonstrates the complete business workflow using the `small_business` package,
# following a realistic arts business scenario.
#
# **Business**: Earthworks Studio - a ceramics studio offering classes and selling finished pieces
#
# **Workflow**:
# 1. Initial setup (business settings, chart of accounts)
# 2. Client management
# 3. Creating and sending quotes
# 4. Job tracking and management
# 5. Invoicing and payment recording
#
# This example shows both service-based (pottery classes, commissions) and product-based
# (selling finished pieces) transactions, demonstrating GST-inclusive and GST-exclusive pricing.

# %% [markdown]
# ## Setup and Imports

# %%
import shutil
from datetime import date, timedelta
from decimal import Decimal
from importlib.resources import files
from pathlib import Path

# Import models
from small_business.models import (
	Account,
	AccountType,
	ChartOfAccounts,
	Client,
	Invoice,
	Job,
	LineItem,
	Quote,
	Settings,
)

# Import storage
from small_business.storage import StorageRegistry

# Create a temporary data directory for this example
data_dir = Path("./temp_small_business_data")
data_dir.mkdir(exist_ok=True)
print(f"📁 Data directory: {data_dir}")

# Initialize storage registry (loads all data into memory)
storage = StorageRegistry(data_dir)

# %% [markdown]
# ## 1. Initial Setup
#
# First, we'll configure the business settings including contact details, ABN, and file paths.

# %%
# Create business settings
settings = Settings(
	gst_rate=Decimal("0.10"),
	financial_year_start_month=7,  # July (Australian financial year)
	currency="AUD",
	business_name="Earthworks Studio",
	business_abn="51 824 753 556",
	business_email="contact@earthworksstudio.com.au",
	business_phone="(03) 9555 1234",
	business_address="42 Clay Street, Fitzroy VIC 3065",
	data_directory=str(data_dir),
)

# Save settings
storage.save_settings(settings)
print("✅ Business settings configured")
print(f"   Business: {settings.business_name}")
print(f"   ABN: {settings.business_abn}")
print("   Financial Year: July-June")

# %% [markdown]
# ### Chart of Accounts
#
# Set up a basic chart of accounts for the arts business using a flat structure
# with human-readable account names.

# %%
# Define chart of accounts
accounts = [
	# Assets
	Account(name="Bank Account", account_type=AccountType.ASSET),
	Account(name="Accounts Receivable", account_type=AccountType.ASSET),
	Account(name="Inventory", account_type=AccountType.ASSET),
	# Liabilities
	Account(name="Accounts Payable", account_type=AccountType.LIABILITY),
	Account(name="GST Collected", account_type=AccountType.LIABILITY),
	Account(name="GST Paid", account_type=AccountType.LIABILITY),
	# Equity
	Account(name="Owner's Equity", account_type=AccountType.EQUITY),
	# Income
	Account(name="Class Fees", account_type=AccountType.INCOME),
	Account(name="Commission Work", account_type=AccountType.INCOME),
	Account(name="Product Sales", account_type=AccountType.INCOME),
	# Expenses
	Account(name="Materials & Supplies", account_type=AccountType.EXPENSE),
	Account(name="Studio Rent", account_type=AccountType.EXPENSE),
	Account(name="Utilities", account_type=AccountType.EXPENSE),
	Account(name="Marketing", account_type=AccountType.EXPENSE),
]

chart = ChartOfAccounts(accounts=accounts)
print("✅ Chart of accounts created")
print(f"   Total accounts: {len(chart.accounts)}")
print(
	f"   Income accounts: {len([a for a in chart.accounts if a.account_type == AccountType.INCOME])}"
)
print(
	f"   Expense accounts: {len([a for a in chart.accounts if a.account_type == AccountType.EXPENSE])}"
)

# %% [markdown]
# ### Alternative: Load from YAML
#
# For easier maintenance, you can define your chart of accounts in a YAML file and load it.
# This is the recommended approach for production use.
#
# The package includes a comprehensive default chart of accounts suitable for Australian
# small businesses. You can use it as-is or customize it for your needs.

# %%
# Load default chart of accounts from package data
default_coa_path = str(files("small_business.data").joinpath("default_chart_of_accounts.yaml"))
chart_from_yaml = ChartOfAccounts.from_yaml(default_coa_path)

print("✅ Chart of accounts loaded from default YAML")
print(f"   Total accounts: {len(chart_from_yaml.accounts)}")
print(f"   Asset accounts: {len([a for a in chart_from_yaml.accounts if a.account_type == AccountType.ASSET])}")
print(f"   Liability accounts: {len([a for a in chart_from_yaml.accounts if a.account_type == AccountType.LIABILITY])}")
print(f"   Equity accounts: {len([a for a in chart_from_yaml.accounts if a.account_type == AccountType.EQUITY])}")
print(f"   Income accounts: {len([a for a in chart_from_yaml.accounts if a.account_type == AccountType.INCOME])}")
print(f"   Expense accounts: {len([a for a in chart_from_yaml.accounts if a.account_type == AccountType.EXPENSE])}")
print("\n   Sample accounts:")
print(f"   - {chart_from_yaml.get_account('Bank Account').name}")
print(f"   - {chart_from_yaml.get_account('GST Collected').name}")
print(f"   - {chart_from_yaml.get_account('Class Fees').name}")

# %% [markdown]
# ## 2. Client Management
#
# Create a client record for a local art gallery that wants to commission custom pieces.

# %%
# Create client
gallery_client = Client(
	client_id="Gallery 27",  # Human-readable ID (business name)
	name="Gallery 27",
	email="curator@gallery27.com.au",
	phone="(03) 9555 7777",
	contact_person="Sarah Chen",
	abn="72 456 789 012",
	street_address="27 Brunswick Street",
	suburb="Fitzroy",
	state="VIC",
	postcode="3065",
	formatted_address="27 Brunswick Street, Fitzroy VIC 3065",
	notes="Contemporary art gallery, regular client for exhibitions",
)

# Save client
storage.save_client(gallery_client)
print("✅ Client created")
print(f"   Client ID: {gallery_client.client_id}")
print(f"   Contact: {gallery_client.contact_person}")
print(f"   Email: {gallery_client.email}")

# %% [markdown]
# ### Client Lookup
#
# Demonstrate case-insensitive client lookup (handles "gallery 27", "Gallery 27", "GALLERY 27").

# %%
# Load client (case-insensitive)
loaded_client = storage.get_client("gallery 27")  # Note: lowercase
print(f"✅ Client loaded (case-insensitive): {loaded_client.client_id}")

# List all clients
all_clients = storage.get_all_clients()
print(f"📋 Total clients: {len(all_clients)}")
for client in all_clients:
	print(f"   - {client.client_id}: {client.email}")

# %% [markdown]
# ## 3. Creating a Quote
#
# Gallery 27 wants a custom ceramic installation for their next exhibition, plus some
# handmade bowls for their gift shop. We'll create a quote with mixed line items.

# %%
# Create quote
quote = Quote(
	client_id=gallery_client.client_id,
	date_created=date.today(),
	date_valid_until=date.today() + timedelta(days=30),
	line_items=[
		# Service: Custom commission work (GST-exclusive hourly rate)
		LineItem(
			description="Custom ceramic wall installation - design and creation (40 hours)",
			quantity=Decimal("40.00"),
			unit_price=Decimal("85.00"),  # $85/hour
			gst_inclusive=False,
		),
		LineItem(
			description="Installation and mounting (8 hours)",
			quantity=Decimal("8.00"),
			unit_price=Decimal("95.00"),  # $95/hour for installation
			gst_inclusive=False,
		),
		# Product: Finished pieces (GST-inclusive retail)
		LineItem(
			description="Handmade ceramic bowls - set of 6 (glazed earthenware)",
			quantity=Decimal("2.00"),  # 2 sets
			unit_price=Decimal("330.00"),  # $330 per set (GST-inclusive)
			gst_inclusive=True,
		),
	],
	terms_and_conditions=(
		"Payment terms: 50% deposit on acceptance, balance due on completion.\n"
		"Custom work will be completed within 6 weeks of deposit.\n"
		"Installation to be scheduled separately."
	),
	notes="Exhibition opening: late February. Aim to complete by mid-Feb.",
)

# Save quote
storage.save_quote(quote)
print("✅ Quote created and saved")
print(f"   Quote ID: {quote.quote_id}")
print(f"   Client: {quote.client_id}")
print(f"   Valid until: {quote.date_valid_until}")
print(f"   Status: {quote.status.value}")

# %% [markdown]
# ### Quote Calculations
#
# The Quote model automatically calculates subtotals, GST, and totals from line items.
# Let's examine the breakdown:

# %%
print("💰 Quote Breakdown:")
print(f"   Subtotal: ${quote.subtotal:,.2f}")
print(f"   GST: ${quote.gst_amount:,.2f}")
print(f"   Total: ${quote.total:,.2f}")
print(f"   Financial Year: {quote.financial_year}")

print("\n📋 Line Items:")
for i, item in enumerate(quote.line_items, 1):
	print(f"\n   {i}. {item.description}")
	print(f"      Qty: {item.quantity} × ${item.unit_price}")
	print(f"      Subtotal: ${item.subtotal:,.2f}")
	print(
		f"      GST ({('inclusive' if item.gst_inclusive else 'exclusive')}): ${item.gst_amount:,.2f}"
	)
	print(f"      Total: ${item.total:,.2f}")

# %% [markdown]
# ### Update Quote Status
#
# After client reviews and accepts the quote, we update the status by setting date fields.
# Status is automatically derived from these dates.

# %%
# Update quote to SENT by setting date_sent
quote.date_sent = date.today()
storage.save_quote(quote)
print(f"✅ Quote status updated to: {quote.status.value}")

# Simulate client acceptance by setting date_accepted
quote.date_accepted = date.today() + timedelta(days=2)
storage.save_quote(quote)
print(f"✅ Quote accepted by client: {quote.status.value}")

# %% [markdown]
# ## 4. Job Tracking
#
# Once the quote is accepted, we create a job to track the work.

# %%
# Create job from accepted quote
job = Job(
	quote_id=quote.quote_id,
	client_id=quote.client_id,
	date_accepted=date.today(),
	scheduled_date=date.today() + timedelta(days=7),  # Start in 1 week
	notes="Client prefers warm earth tones. Reference images sent via email.",
)

print("✅ Job created from quote")
print(f"   Job ID: {job.job_id}")
print(f"   Quote ID: {job.quote_id}")
print(f"   Client: {job.client_id}")
print(f"   Scheduled: {job.scheduled_date}")
print(f"   Status: {job.status.value}")
print(f"   Financial Year: {job.financial_year}")

# %% [markdown]
# ### Job Status Updates
#
# Track the job through its lifecycle by setting date fields.
# Status is automatically derived from these dates.

# %%
# Start work by setting date_started
job.date_started = date.today() + timedelta(days=7)
print(f"🔨 Job status: {job.status.value}")

# Complete work by setting date_completed
job.date_completed = date.today() + timedelta(days=45)
print(f"✅ Job status: {job.status.value}")
print(f"   Duration: {job.duration_days} days")

# %% [markdown]
# ### Track Job Costs (Example)
#
# In a real scenario, you'd link transaction IDs for materials purchased for this job.
# This helps calculate actual profitability.

# %%
# Example: tracking actual costs (transaction IDs would come from expense tracking)
job.actual_costs = [
	"TXN-20251123-001",  # Clay and glazes purchase
	"TXN-20251123-002",  # Additional materials
]
job.notes += "\n\nMaterials cost tracked in transactions."
print(f"📊 Job costs tracked: {len(job.actual_costs)} transactions linked")

# %% [markdown]
# ## 5. Invoicing
#
# After job completion, create an invoice. Line items typically match the quote.

# %%
# Create invoice from completed job
invoice = Invoice(
	job_id=job.job_id,
	client_id=job.client_id,
	date_due=date.today() + timedelta(days=14),  # Net 14 days
	line_items=quote.line_items,  # Copy line items from quote
	notes="Thank you for your business! 50% deposit already received.",
)

# Save invoice
storage.save_invoice(invoice)
print("✅ Invoice created and saved")
print(f"   Invoice ID: {invoice.invoice_id}")
print(f"   Job ID: {invoice.job_id}")
print(f"   Client: {invoice.client_id}")
print(f"   Due date: {invoice.date_due}")
print(f"   Status: {invoice.status.value}")

# %% [markdown]
# ### Invoice Calculations

# %%
print("💰 Invoice Breakdown:")
print(f"   Subtotal: ${invoice.subtotal:,.2f}")
print(f"   GST: ${invoice.gst_amount:,.2f}")
print(f"   Total: ${invoice.total:,.2f}")
print(f"   Financial Year: {invoice.financial_year}")

# %% [markdown]
# ### Send Invoice and Record Payment

# %%
# Send invoice to client by setting date_issued
invoice.date_issued = date.today() + timedelta(days=45)
storage.save_invoice(invoice)
print(f"📧 Invoice sent to client: {invoice.status.value}")
print(f"   Days outstanding: {invoice.days_outstanding}")

# Record payment by setting date_paid
invoice.date_paid = date.today() + timedelta(days=52)
invoice.payment_amount = invoice.total
invoice.payment_reference = "Bank transfer - Ref: GAL27-INV"
storage.save_invoice(invoice)

print("✅ Payment recorded")
print(f"   Amount: ${invoice.payment_amount:,.2f}")
print(f"   Date: {invoice.date_paid}")
print(f"   Reference: {invoice.payment_reference}")
print(f"   Status: {invoice.status.value}")

# Update job status to invoiced by setting date_invoiced
job.date_invoiced = date.today() + timedelta(days=45)
print(f"✅ Job status updated to: {job.status.value}")

# %% [markdown]
# ## 6. Workflow Summary
#
# Let's verify the complete workflow by reloading data from storage.

# %%
# Reload quote
reloaded_quote = storage.get_quote(quote.quote_id, quote.date_created)
print(f"📄 Quote {reloaded_quote.quote_id}:")
print(f"   Status: {reloaded_quote.status.value}")
print(f"   Total: ${reloaded_quote.total:,.2f}")

# Reload invoice
reloaded_invoice = storage.get_invoice(
	invoice.invoice_id, invoice.date_issued or invoice.date_created
)
print(f"\n📄 Invoice {reloaded_invoice.invoice_id}:")
print(f"   Status: {reloaded_invoice.status.value}")
print(f"   Total: ${reloaded_invoice.total:,.2f}")
print(f"   Paid: ${reloaded_invoice.payment_amount:,.2f} on {reloaded_invoice.date_paid}")

# Workflow summary
print("\n✅ Complete Workflow Summary:")
print(f"   1. Client created: {gallery_client.client_id}")
print(f"   2. Quote created: {quote.quote_id} (${quote.total:,.2f})")
print(f"   3. Quote accepted: {quote.status.value}")
print(f"   4. Job created: {job.job_id}")
print(f"   5. Job completed: {job.status.value}")
print(f"   6. Invoice created: {invoice.invoice_id}")
print(f"   7. Invoice paid: {invoice.status.value}")
print(f"\n   Total revenue: ${invoice.total:,.2f}")
print(f"   GST collected: ${invoice.gst_amount:,.2f}")

# %% [markdown]
# ## Key Insights
#
# **★ Insight ─────────────────────────────────────**
#
# 1. **Automatic Calculations**: Quote and Invoice models automatically calculate
#    subtotals, GST, and totals from line items. This eliminates manual calculation
#    errors and handles mixed GST-inclusive/exclusive items correctly.
#
# 2. **Human-Readable IDs**: Both Client IDs and Account names use business-meaningful
#    identifiers ("Gallery 27", "Bank Account") for easy identification and debugging.
#    Quote/Job/Invoice IDs use generated codes for audit trails and uniqueness.
#
# 3. **YAML Configuration**: Chart of accounts can be loaded from YAML files,
#    separating configuration from code and enabling non-developers to modify
#    account structures without touching Python.
#
# 4. **Type-Safe Workflow**: Pydantic models provide validation at every step,
#    ensuring data integrity (e.g., duplicate account names prevented, valid dates,
#    positive quantities).
#
# **─────────────────────────────────────────────────**

# %% [markdown]
# ## Cleanup
#
# Remove the temporary data directory.

# %%
# Cleanup
shutil.rmtree(data_dir)
print("🗑️  Cleaned up temporary data directory")
