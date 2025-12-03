# %% [markdown]
# # Financial Reporting & BAS Compliance
#
# This notebook demonstrates the **Phase 5 reporting functionality** for generating financial
# statements and Australian BAS/GST reports. We'll use an arts business example to show:
#
# - **Profit & Loss (P&L) reports** - Income and expenses over a period
# - **Balance Sheet reports** - Assets, liabilities, and equity at a point in time
# - **BAS/GST reports** - Australian tax compliance reporting
# - **CSV export** - Export reports for spreadsheet analysis
#
# **Example Business: "Creative Canvas Studio"**
# - Sole trader visual arts business
# - Sells original artwork and provides commission work
# - Tracks studio rent, art supplies, and exhibition costs

# %% [markdown]
# ## Setup
#
# Import required modules and create a temporary data directory for this example.

# %%
from datetime import date
from decimal import Decimal
from pathlib import Path
import shutil
import tempfile
from importlib.resources import files

# Import models
from small_business.models import (
	Account,
	AccountType,
	ChartOfAccounts,
	JournalEntry,
	Transaction,
)

# Import reporting functions
from small_business.reports import (
	generate_profit_loss_report,
	generate_balance_sheet,
	generate_bas_report,
	export_profit_loss_csv,
	export_balance_sheet_csv,
	export_bas_csv,
)

# Import storage
from small_business.storage import StorageRegistry

# Create temporary data directory
data_dir = Path(tempfile.mkdtemp(prefix="creative_canvas_"))
reports_dir = data_dir / "reports"
reports_dir.mkdir()

print("🎨 Creative Canvas Studio - Financial Reporting Demo")
print(f"📁 Data directory: {data_dir}")

# Initialize storage registry
storage = StorageRegistry(data_dir)

# %% [markdown]
# ## Chart of Accounts
#
# Load the default chart of accounts from the package data.
# This includes standard accounts for Australian small businesses.

# %%
# Load default chart of accounts from package data
default_coa_path = str(files("small_business.data").joinpath("default_chart_of_accounts.yaml"))
chart = ChartOfAccounts.from_yaml(default_coa_path)

print(f"✅ Chart of Accounts loaded with {len(chart.accounts)} accounts")
print("\nAccount Summary:")
print(f"   Assets: {sum(1 for a in chart.accounts if a.account_type == AccountType.ASSET)}")
print(f"   Income: {sum(1 for a in chart.accounts if a.account_type == AccountType.INCOME)}")
print(f"   Expenses: {sum(1 for a in chart.accounts if a.account_type == AccountType.EXPENSE)}")
print(f"   Liabilities: {sum(1 for a in chart.accounts if a.account_type == AccountType.LIABILITY)}")
print(f"   Equity: {sum(1 for a in chart.accounts if a.account_type == AccountType.EQUITY)}")

# %% [markdown]
# ## November 2025 Transactions
#
# Record a month of business activity for Creative Canvas Studio. This includes:
# - Opening balance
# - Income from artwork sales, commissions, and workshops
# - Expenses for rent, supplies, exhibitions, marketing
# - Equipment purchases and loan transactions

# %%
# Opening balance - November 1
txn_opening = Transaction(
	date=date(2025, 11, 1),
	description="Opening balance - November 2025",
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("15000.00"), credit=Decimal("0")),
		JournalEntry(account_code="Owner's Equity", debit=Decimal("0"), credit=Decimal("15000.00")),
	],
)

# Income: Artwork sale - November 5
txn_sale1 = Transaction(
	date=date(2025, 11, 5),
	description="Sale: Abstract landscape painting",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("2200.00"), credit=Decimal("0")),
		JournalEntry(account_code="Sales", debit=Decimal("0"), credit=Decimal("2200.00")),
	],
)

# Expense: Studio rent - November 6
txn_rent = Transaction(
	date=date(2025, 11, 6),
	description="Monthly studio rent - November",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Studio Rent", debit=Decimal("1650.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("1650.00")),
	],
)

# Income: Commission work - November 10
txn_commission = Transaction(
	date=date(2025, 11, 10),
	description="Commission: Custom portrait",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("3300.00"), credit=Decimal("0")),
		JournalEntry(account_code="Commission Work", debit=Decimal("0"), credit=Decimal("3300.00")),
	],
)

# Expense: Art supplies - November 12
txn_supplies1 = Transaction(
	date=date(2025, 11, 12),
	description="Canvas, paints, brushes",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Materials & Supplies", debit=Decimal("550.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("550.00")),
	],
)

# Income: Workshop fees - November 15
txn_workshop = Transaction(
	date=date(2025, 11, 15),
	description="Watercolor painting workshop",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("880.00"), credit=Decimal("0")),
		JournalEntry(account_code="Class Fees", debit=Decimal("0"), credit=Decimal("880.00")),
	],
)

# Expense: Exhibition costs - November 18
txn_exhibition = Transaction(
	date=date(2025, 11, 18),
	description="Gallery exhibition fees",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Miscellaneous Expenses", debit=Decimal("440.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("440.00")),
	],
)

# Income: Another artwork sale - November 20
txn_sale2 = Transaction(
	date=date(2025, 11, 20),
	description="Sale: Sculpture series (3 pieces)",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("4400.00"), credit=Decimal("0")),
		JournalEntry(account_code="Sales", debit=Decimal("0"), credit=Decimal("4400.00")),
	],
)

# Expense: Marketing - November 22
txn_marketing = Transaction(
	date=date(2025, 11, 22),
	description="Social media advertising",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Marketing & Advertising", debit=Decimal("330.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("330.00")),
	],
)

# Asset purchase: Equipment - November 25
txn_equipment = Transaction(
	date=date(2025, 11, 25),
	description="Professional camera for artwork documentation",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Equipment", debit=Decimal("2200.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("2200.00")),
	],
)

# Liability: Equipment loan - November 26
txn_loan = Transaction(
	date=date(2025, 11, 26),
	description="Equipment loan received",
	entries=[
		JournalEntry(account_code="Bank Account", debit=Decimal("2000.00"), credit=Decimal("0")),
		JournalEntry(account_code="Loans Payable", debit=Decimal("0"), credit=Decimal("2000.00")),
	],
)

# Expense: Insurance - November 28
txn_insurance = Transaction(
	date=date(2025, 11, 28),
	description="Studio and artwork insurance",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Insurance", debit=Decimal("220.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("220.00")),
	],
)

# Expense: More art supplies - November 29
txn_supplies2 = Transaction(
	date=date(2025, 11, 29),
	description="Specialty pigments and mediums",
	gst_inclusive=True,
	entries=[
		JournalEntry(account_code="Materials & Supplies", debit=Decimal("385.00"), credit=Decimal("0")),
		JournalEntry(account_code="Bank Account", debit=Decimal("0"), credit=Decimal("385.00")),
	],
)

# Save all transactions
transactions = [
	txn_opening,
	txn_sale1,
	txn_rent,
	txn_commission,
	txn_supplies1,
	txn_workshop,
	txn_exhibition,
	txn_sale2,
	txn_marketing,
	txn_equipment,
	txn_loan,
	txn_insurance,
	txn_supplies2,
]

for txn in transactions:
	storage.save_transaction(txn)

print(f"✅ Saved {len(transactions)} transactions for November 2025")
print("\nTransaction Summary:")
print("   Income transactions: 4")
print("   Expense transactions: 7")
print("   Asset transactions: 1")
print("   Liability transactions: 1")
print("   Opening balance: 1")

# %% [markdown]
# ## Profit & Loss Report
#
# Generate a Profit & Loss (P&L) statement showing income, expenses, and net profit
# for the month of November 2025.

# %%
pl_report = generate_profit_loss_report(
	chart=chart,
	data_dir=data_dir,
	start_date=date(2025, 11, 1),
	end_date=date(2025, 11, 30),
)

print("📊 PROFIT & LOSS STATEMENT")
print("Creative Canvas Studio")
print(f"Period: {pl_report['start_date']} to {pl_report['end_date']}")
print("=" * 60)

print("\nINCOME")
print("-" * 60)
for code, data in pl_report["income"].items():
	print(f"  {data['name']:<40} ${data['balance']:>12,.2f}")
print("-" * 60)
print(f"  {'TOTAL INCOME':<40} ${pl_report['total_income']:>12,.2f}")

print("\n\nEXPENSES")
print("-" * 60)
for code, data in pl_report["expenses"].items():
	print(f"  {data['name']:<40} ${data['balance']:>12,.2f}")
print("-" * 60)
print(f"  {'TOTAL EXPENSES':<40} ${pl_report['total_expenses']:>12,.2f}")

print("\n" + "=" * 60)
print(f"  {'NET PROFIT':<40} ${pl_report['net_profit']:>12,.2f}")
print("=" * 60)

# Export to CSV
pl_csv = reports_dir / "profit_loss_nov2025.csv"
export_profit_loss_csv(pl_report, pl_csv)
print(f"\n💾 Exported to: {pl_csv}")

# %% [markdown]
# ## Balance Sheet Report
#
# Generate a Balance Sheet showing the financial position of Creative Canvas Studio
# as of November 30, 2025. This includes assets, liabilities, and equity.

# %%
bs_report = generate_balance_sheet(
	chart=chart,
	data_dir=data_dir,
	as_of_date=date(2025, 11, 30),
)

print("📊 BALANCE SHEET")
print("Creative Canvas Studio")
print(f"As of: {bs_report['as_of_date']}")
print("=" * 60)

print("\nASSETS")
print("-" * 60)
for code, data in bs_report["assets"].items():
	print(f"  {data['name']:<40} ${data['balance']:>12,.2f}")
print("-" * 60)
print(f"  {'TOTAL ASSETS':<40} ${bs_report['total_assets']:>12,.2f}")

print("\n\nLIABILITIES")
print("-" * 60)
if bs_report["liabilities"]:
	for code, data in bs_report["liabilities"].items():
		print(f"  {data['name']:<40} ${data['balance']:>12,.2f}")
else:
	print(f"  {'No liabilities':<40} ${'0.00':>12}")
print("-" * 60)
print(f"  {'TOTAL LIABILITIES':<40} ${bs_report['total_liabilities']:>12,.2f}")

print("\n\nEQUITY")
print("-" * 60)
for code, data in bs_report["equity"].items():
	print(f"  {data['name']:<40} ${data['balance']:>12,.2f}")
print("-" * 60)
print(f"  {'TOTAL EQUITY':<40} ${bs_report['total_equity']:>12,.2f}")

print("\n" + "=" * 60)
print(f"  {'TOTAL LIABILITIES + EQUITY':<40} ${bs_report['total_liabilities'] + bs_report['total_equity']:>12,.2f}")
print("=" * 60)

# Verify accounting equation
print("\n✅ Accounting Equation Check:")
print(f"   Assets: ${bs_report['total_assets']:,.2f}")
print(f"   Liabilities + Equity: ${bs_report['total_liabilities'] + bs_report['total_equity']:,.2f}")

# Note: The difference is the net profit for the period
difference = bs_report['total_assets'] - (bs_report['total_liabilities'] + bs_report['total_equity'])
print(f"   Difference: ${difference:,.2f}")

if difference == pl_report['net_profit']:
	print(f"   ✓ Difference equals Net Profit (${pl_report['net_profit']:,.2f})")
	print("   Note: Profit will be closed to Retained Earnings at year-end")
else:
	print("   ✗ Unexpected difference - Check transactions!")

# Export to CSV
bs_csv = reports_dir / "balance_sheet_nov2025.csv"
export_balance_sheet_csv(bs_report, bs_csv)
print(f"\n💾 Exported to: {bs_csv}")

# %% [markdown]
# ## BAS/GST Report
#
# Generate a Business Activity Statement (BAS) report for Australian tax compliance.
# This calculates GST collected on sales and GST paid on purchases.
#
# **Note:** In Australia, GST is calculated using the **1/11 formula** for GST-inclusive amounts:
# - GST-inclusive amount of $110 contains $10 GST ($110 × 1/11)

# %%
bas_report = generate_bas_report(
	data_dir=data_dir,
	start_date=date(2025, 11, 1),
	end_date=date(2025, 11, 30),
)

print("📊 BAS/GST REPORT")
print("Creative Canvas Studio")
print(f"Period: {bas_report['start_date']} to {bas_report['end_date']}")
print("=" * 60)

print("\nGST COLLECTED (on sales)")
print("-" * 60)
print(f"  Total Sales (GST inclusive)              ${bas_report['total_sales']:>12,.2f}")
print(f"  GST on Sales (1/11 of sales)             ${bas_report['gst_on_sales']:>12,.2f}")

print("\n\nGST PAID (on purchases)")
print("-" * 60)
print(f"  Total Purchases (GST inclusive)          ${bas_report['total_purchases']:>12,.2f}")
print(f"  GST on Purchases (1/11 of purchases)     ${bas_report['gst_on_purchases']:>12,.2f}")

print("\n" + "=" * 60)
print(f"  NET GST (owed to ATO)                    ${bas_report['net_gst']:>12,.2f}")
print("=" * 60)

if bas_report['net_gst'] > 0:
	print(f"\n💰 Amount to pay to ATO: ${bas_report['net_gst']:,.2f}")
else:
	print(f"\n💵 Refund from ATO: ${abs(bas_report['net_gst']):,.2f}")

# Export to CSV
bas_csv = reports_dir / "bas_report_nov2025.csv"
export_bas_csv(bas_report, bas_csv)
print(f"\n💾 Exported to: {bas_csv}")

# %% [markdown]
# ## Summary & Key Insights
#
# Let's summarize the financial position of Creative Canvas Studio.

# %%
print("🎨 CREATIVE CANVAS STUDIO - NOVEMBER 2025 SUMMARY")
print("=" * 60)

print("\n📈 PROFITABILITY")
print(f"   Total Income:        ${pl_report['total_income']:>10,.2f}")
print(f"   Total Expenses:      ${pl_report['total_expenses']:>10,.2f}")
print(f"   Net Profit:          ${pl_report['net_profit']:>10,.2f}")
profit_margin = (pl_report['net_profit'] / pl_report['total_income'] * 100) if pl_report['total_income'] > 0 else 0
print(f"   Profit Margin:       {profit_margin:>10.1f}%")

print("\n💼 FINANCIAL POSITION")
print(f"   Total Assets:        ${bs_report['total_assets']:>10,.2f}")
print(f"   Total Liabilities:   ${bs_report['total_liabilities']:>10,.2f}")
print(f"   Total Equity:        ${bs_report['total_equity']:>10,.2f}")

print("\n🏦 CASH POSITION")
bank_balance = sum(
	data['balance']
	for code, data in bs_report['assets'].items()
	if 'Bank' in code
)
print(f"   Bank Accounts:       ${bank_balance:>10,.2f}")

print("\n📊 INCOME BREAKDOWN")
for code, data in pl_report["income"].items():
	percentage = (data['balance'] / pl_report['total_income'] * 100) if pl_report['total_income'] > 0 else 0
	print(f"   {data['name']:<25} ${data['balance']:>8,.2f} ({percentage:>5.1f}%)")

print("\n💸 EXPENSE BREAKDOWN")
for code, data in pl_report["expenses"].items():
	percentage = (data['balance'] / pl_report['total_expenses'] * 100) if pl_report['total_expenses'] > 0 else 0
	print(f"   {data['name']:<25} ${data['balance']:>8,.2f} ({percentage:>5.1f}%)")

print("\n🧾 TAX COMPLIANCE")
print(f"   GST Collected:       ${bas_report['gst_on_sales']:>10,.2f}")
print(f"   GST Paid:            ${bas_report['gst_on_purchases']:>10,.2f}")
print(f"   Net GST Owed:        ${bas_report['net_gst']:>10,.2f}")

print("\n📁 REPORTS GENERATED")
print(f"   Profit & Loss:       {pl_csv.name}")
print(f"   Balance Sheet:       {bs_csv.name}")
print(f"   BAS/GST Report:      {bas_csv.name}")

print("\n" + "=" * 60)

# %% [markdown]
# ## Key Insights
#
# **Strong Performance:**
# - Healthy profit margin showing sustainable operations
# - Diverse income streams (sales, commissions, workshops)
# - Strong cash position in bank accounts
#
# **Expense Management:**
# - Largest expense is studio rent (expected for creative business)
# - Art supplies second largest expense (cost of goods sold)
# - Marketing investment shows commitment to growth
#
# **Tax Compliance:**
# - Net GST position calculated for quarterly BAS submission
# - All transactions properly tracked with GST status
#
# **Financial Health:**
# - Assets exceed liabilities (positive equity)
# - Equipment investment funded partially by loan
# - Balance sheet equation verified and balanced

# %% [markdown]
# ## Cleanup
#
# Remove the temporary data directory.

# %%
shutil.rmtree(data_dir)
print("🗑️  Cleaned up temporary data directory")
print("\n✅ Financial reporting demonstration complete!")
