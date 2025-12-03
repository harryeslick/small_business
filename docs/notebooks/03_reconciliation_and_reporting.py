# %% [markdown]
# # Financial Reconciliation and Reporting
#
# This notebook demonstrates financial reporting and reconciliation features:
#
# 1. Chart of accounts review and account balances
# 2. Trial balance verification
# 3. Monthly reconciliation and period reports
# 4. Income statement (Profit & Loss)
# 5. Balance sheet
# 6. GST reconciliation for BAS
# 7. Financial year summary
#
# **Business Context**: Continuing with Earthworks Studio (ceramics business)

# %% [markdown]
# ## Setup and Imports

# %%
import shutil
import tempfile
from collections import defaultdict
from datetime import date
from decimal import Decimal
from importlib.resources import files
from pathlib import Path

# Import models
from small_business.models import (
	AccountType,
	ChartOfAccounts,
	JournalEntry,
	Transaction,
	get_financial_year,
)
from small_business.storage import StorageRegistry

# Create temporary data directory
data_dir = Path(tempfile.mkdtemp(prefix="earthworks_reports_"))
print(f"📁 Data directory: {data_dir}")

# Initialize storage registry
storage = StorageRegistry(data_dir)

# %% [markdown]
# ## 1. Setup Chart of Accounts

# %%
# Load default chart of accounts from package data
default_coa_path = str(files("small_business.data").joinpath("default_chart_of_accounts.yaml"))
chart = ChartOfAccounts.from_yaml(default_coa_path)

print("✅ Chart of accounts loaded")
print(f"   Total accounts: {len(chart.accounts)}")

# Display accounts by type
print("\n📊 Accounts by Type:")
for account_type in [
	AccountType.ASSET,
	AccountType.LIABILITY,
	AccountType.EQUITY,
	AccountType.INCOME,
	AccountType.EXPENSE,
]:
	accounts = chart.get_accounts_by_type(account_type)
	if accounts:
		print(f"\n{account_type.value.upper()}: {len(accounts)} accounts")
		for acc in accounts[:5]:  # Show first 5
			print(f"  • {acc.name}")
		if len(accounts) > 5:
			print(f"  ... and {len(accounts) - 5} more")

# %% [markdown]
# ## 2. Sample Transactions
#
# Create sample transactions for November 2025 to demonstrate reporting.

# %%
# Create sample transactions using account names from the chart
transactions = [
	# Opening balance
	Transaction(
		date=date(2025, 11, 1),
		description="Opening balance - November",
		entries=[
			JournalEntry(account_code="Bank Account", debit=Decimal("5420.50")),
			JournalEntry(account_code="Owner's Equity", credit=Decimal("5420.50")),
		],
	),
	# Income: Commission payment from Gallery 27
	Transaction(
		date=date(2025, 11, 3),
		description="Commission payment - Gallery 27 installation",
		entries=[
			JournalEntry(account_code="Bank Account", debit=Decimal("3400.00")),
			JournalEntry(account_code="Commission Work", credit=Decimal("3090.91")),
			JournalEntry(account_code="GST Collected", credit=Decimal("309.09")),
		],
		gst_inclusive=True,
	),
	# Expense: Materials
	Transaction(
		date=date(2025, 11, 5),
		description="Clay and glazes - Clay Supplies Pty Ltd",
		entries=[
			JournalEntry(account_code="Materials & Supplies", debit=Decimal("259.09")),
			JournalEntry(account_code="GST Paid", debit=Decimal("25.91")),
			JournalEntry(account_code="Bank Account", credit=Decimal("285.00")),
		],
		gst_inclusive=False,
	),
	# Expense: Studio rent
	Transaction(
		date=date(2025, 11, 20),
		description="Studio rent - November",
		entries=[
			JournalEntry(account_code="Studio Rent", debit=Decimal("1200.00")),
			JournalEntry(account_code="Bank Account", credit=Decimal("1200.00")),
		],
		gst_inclusive=False,  # Commercial rent is GST-free
	),
	# Expense: Utilities
	Transaction(
		date=date(2025, 11, 12),
		description="Electricity - AGL Energy",
		entries=[
			JournalEntry(account_code="Utilities", debit=Decimal("131.82")),
			JournalEntry(account_code="GST Paid", debit=Decimal("13.18")),
			JournalEntry(account_code="Bank Account", credit=Decimal("145.00")),
		],
		gst_inclusive=False,
	),
	# Expense: Materials
	Transaction(
		date=date(2025, 11, 15),
		description="Pottery tools - Potter's Warehouse",
		entries=[
			JournalEntry(account_code="Materials & Supplies", debit=Decimal("415.27")),
			JournalEntry(account_code="GST Paid", debit=Decimal("41.53")),
			JournalEntry(account_code="Bank Account", credit=Decimal("456.80")),
		],
		gst_inclusive=False,
	),
	# Income: Private class payment
	Transaction(
		date=date(2025, 11, 18),
		description="Private pottery class - 4 sessions",
		entries=[
			JournalEntry(account_code="Bank Account", debit=Decimal("850.00")),
			JournalEntry(account_code="Class Fees", credit=Decimal("772.73")),
			JournalEntry(account_code="GST Collected", credit=Decimal("77.27")),
		],
		gst_inclusive=True,
	),
	# Expense: Marketing
	Transaction(
		date=date(2025, 11, 22),
		description="Instagram advertising",
		entries=[
			JournalEntry(account_code="Marketing & Advertising", debit=Decimal("86.36")),
			JournalEntry(account_code="GST Paid", debit=Decimal("8.64")),
			JournalEntry(account_code="Bank Account", credit=Decimal("95.00")),
		],
		gst_inclusive=False,
	),
	# Income: Product sale
	Transaction(
		date=date(2025, 11, 25),
		description="Ceramic bowls - direct sale",
		entries=[
			JournalEntry(account_code="Bank Account", debit=Decimal("330.00")),
			JournalEntry(account_code="Product Sales", credit=Decimal("300.00")),
			JournalEntry(account_code="GST Collected", credit=Decimal("30.00")),
		],
		gst_inclusive=True,
	),
]

# Save transactions
for txn in transactions:
	storage.save_transaction(txn)

print(f"✅ Created {len(transactions)} sample transactions")
print("   Period: November 2025")

# %% [markdown]
# ## 3. Account Balances
#
# Calculate current balance for each account.


# %%
def calculate_account_balances(transactions, chart):
	"""Calculate account balances from transactions."""
	balances = defaultdict(lambda: {"debit": Decimal(0), "credit": Decimal(0)})

	for txn in transactions:
		for entry in txn.entries:
			balances[entry.account_code]["debit"] += entry.debit
			balances[entry.account_code]["credit"] += entry.credit

	# Calculate net balance based on account type
	account_balances = {}
	for code, amounts in balances.items():
		account = chart.get_account(code)
		if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
			# Debit balance accounts
			balance = amounts["debit"] - amounts["credit"]
		else:
			# Credit balance accounts (LIABILITY, EQUITY, INCOME)
			balance = amounts["credit"] - amounts["debit"]

		account_balances[code] = {
			"account": account,
			"balance": balance,
			"debit_total": amounts["debit"],
			"credit_total": amounts["credit"],
		}

	return account_balances


# Calculate balances
balances = calculate_account_balances(transactions, chart)

print("💰 Account Balances:")
print(f"{'Code':<20} {'Account Name':<30} {'Balance':>15}")
print("-" * 67)

for account_type in [
	AccountType.ASSET,
	AccountType.LIABILITY,
	AccountType.EQUITY,
	AccountType.INCOME,
	AccountType.EXPENSE,
]:
	type_accounts = [b for code, b in balances.items() if b["account"].account_type == account_type]
	if type_accounts:
		print(f"\n{account_type.value.upper()}")
		for item in type_accounts:
			account = item["account"]
			balance = item["balance"]
			print(f"{account.account_type.encode()} {account.name:<30} ${balance:>13,.2f}")

# %% [markdown]
# ## 4. Trial Balance
#
# Verify that total debits equal total credits (fundamental accounting equation).


# %%
def generate_trial_balance(transactions, chart):
	"""Generate trial balance report."""
	balances = calculate_account_balances(transactions, chart)

	total_debits = Decimal(0)
	total_credits = Decimal(0)

	print("📊 Trial Balance")
	print(f"{'Account':<20} {'Name':<30} {'Debit':>15} {'Credit':>15}")
	print("-" * 82)

	for code, item in sorted(balances.items()):
		account = item["account"]
		balance = item["balance"]

		if balance > 0:
			if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
				print(f"{code:<20} {account.name:<30} ${balance:>13,.2f} ${'':>13}")
				total_debits += balance
			else:
				print(f"{code:<20} {account.name:<30} ${'':>13} ${balance:>13,.2f}")
				total_credits += balance

	print("-" * 82)
	print(f"{'TOTALS':<51} ${total_debits:>13,.2f} ${total_credits:>13,.2f}")

	# Verify balance
	if total_debits == total_credits:
		print("\n✅ Trial balance is balanced!")
	else:
		print(f"\n⚠️  Trial balance out of balance by ${abs(total_debits - total_credits):,.2f}")

	return total_debits == total_credits


# Generate trial balance
is_balanced = generate_trial_balance(transactions, chart)

# %% [markdown]
# ## 5. Income Statement (Profit & Loss)
#
# Calculate income and expenses for the period.


# %%
def generate_income_statement(transactions, chart, start_date, end_date):
	"""Generate income statement for a period."""
	# Filter transactions by date
	period_txns = [t for t in transactions if start_date <= t.date <= end_date]

	# Calculate income and expenses
	income_by_account = defaultdict(Decimal)
	expense_by_account = defaultdict(Decimal)

	for txn in period_txns:
		for entry in txn.entries:
			account = chart.get_account(entry.account_code)
			if account.account_type == AccountType.INCOME:
				income_by_account[entry.account_code] += entry.credit
			elif account.account_type == AccountType.EXPENSE:
				expense_by_account[entry.account_code] += entry.debit

	# Display report
	print("📈 Income Statement")
	print(f"Period: {start_date} to {end_date}")
	print("=" * 60)

	# Income section
	print("\nINCOME")
	print("-" * 60)
	total_income = Decimal(0)
	for code in sorted(income_by_account.keys()):
		account = chart.get_account(code)
		amount = income_by_account[code]
		total_income += amount
		print(f"{account.name:<40} ${amount:>15,.2f}")
	print("-" * 60)
	print(f"{'TOTAL INCOME':<40} ${total_income:>15,.2f}")

	# Expenses section
	print("\nEXPENSES")
	print("-" * 60)
	total_expenses = Decimal(0)
	for code in sorted(expense_by_account.keys()):
		account = chart.get_account(code)
		amount = expense_by_account[code]
		total_expenses += amount
		print(f"{account.name:<40} ${amount:>15,.2f}")
	print("-" * 60)
	print(f"{'TOTAL EXPENSES':<40} ${total_expenses:>15,.2f}")

	# Net profit
	net_profit = total_income - total_expenses
	print("\n" + "=" * 60)
	print(f"{'NET PROFIT':<40} ${net_profit:>15,.2f}")
	print("=" * 60)

	return {
		"total_income": total_income,
		"total_expenses": total_expenses,
		"net_profit": net_profit,
	}


# Generate income statement for November
nov_start = date(2025, 11, 1)
nov_end = date(2025, 11, 30)
income_statement = generate_income_statement(transactions, chart, nov_start, nov_end)

# %% [markdown]
# ## 6. Balance Sheet
#
# Snapshot of assets, liabilities, and equity.


# %%
def generate_balance_sheet(transactions, chart, as_of_date):
	"""Generate balance sheet as of a specific date."""
	# Filter transactions up to date
	period_txns = [t for t in transactions if t.date <= as_of_date]
	balances = calculate_account_balances(period_txns, chart)

	print("💼 Balance Sheet")
	print(f"As of: {as_of_date}")
	print("=" * 60)

	# Assets
	print("\nASSETS")
	print("-" * 60)
	total_assets = Decimal(0)
	for code, item in sorted(balances.items()):
		if item["account"].account_type == AccountType.ASSET and item["balance"] > 0:
			print(f"{item['account'].name:<40} ${item['balance']:>15,.2f}")
			total_assets += item["balance"]
	print("-" * 60)
	print(f"{'TOTAL ASSETS':<40} ${total_assets:>15,.2f}")

	# Liabilities
	print("\nLIABILITIES")
	print("-" * 60)
	total_liabilities = Decimal(0)
	for code, item in sorted(balances.items()):
		if item["account"].account_type == AccountType.LIABILITY and item["balance"] > 0:
			print(f"{item['account'].name:<40} ${item['balance']:>15,.2f}")
			total_liabilities += item["balance"]
	print("-" * 60)
	print(f"{'TOTAL LIABILITIES':<40} ${total_liabilities:>15,.2f}")

	# Equity
	print("\nEQUITY")
	print("-" * 60)
	total_equity = Decimal(0)
	for code, item in sorted(balances.items()):
		if item["account"].account_type == AccountType.EQUITY and item["balance"] > 0:
			print(f"{item['account'].name:<40} ${item['balance']:>15,.2f}")
			total_equity += item["balance"]
	print("-" * 60)
	print(f"{'TOTAL EQUITY':<40} ${total_equity:>15,.2f}")

	# Verify accounting equation
	print("\n" + "=" * 60)
	print(f"{'TOTAL LIABILITIES + EQUITY':<40} ${(total_liabilities + total_equity):>15,.2f}")
	print("=" * 60)

	if total_assets == (total_liabilities + total_equity):
		print("\n✅ Balance sheet balances! (Assets = Liabilities + Equity)")
	else:
		diff = total_assets - (total_liabilities + total_equity)
		print(f"\n⚠️  Balance sheet out of balance by ${abs(diff):,.2f}")

	return {
		"total_assets": total_assets,
		"total_liabilities": total_liabilities,
		"total_equity": total_equity,
	}


# Generate balance sheet
balance_sheet = generate_balance_sheet(transactions, chart, date(2025, 11, 30))

# %% [markdown]
# ## 7. GST Reconciliation
#
# Calculate GST collected and GST paid for BAS lodgement.


# %%
def generate_gst_report(transactions, start_date, end_date):
	"""Generate GST reconciliation report."""
	period_txns = [t for t in transactions if start_date <= t.date <= end_date]

	gst_collected = Decimal(0)
	gst_paid = Decimal(0)

	print("💵 GST Reconciliation Report")
	print(f"Period: {start_date} to {end_date}")
	print("=" * 80)

	# GST Collected (from sales)
	print("\nGST COLLECTED (on sales)")
	print("-" * 80)
	print(f"{'Date':<12} {'Description':<45} {'GST':>15}")
	print("-" * 80)

	for txn in period_txns:
		for entry in txn.entries:
			if entry.account_code == "GST Collected" and entry.credit > 0:
				gst_collected += entry.credit
				print(f"{txn.date} {txn.description[:43]:<45} ${entry.credit:>13,.2f}")

	print("-" * 80)
	print(f"{'TOTAL GST COLLECTED':<58} ${gst_collected:>13,.2f}")

	# GST Paid (on purchases)
	print("\n\nGST PAID (on purchases)")
	print("-" * 80)
	print(f"{'Date':<12} {'Description':<45} {'GST':>15}")
	print("-" * 80)

	for txn in period_txns:
		for entry in txn.entries:
			if entry.account_code == "GST Paid" and entry.debit > 0:
				gst_paid += entry.debit
				print(f"{txn.date} {txn.description[:43]:<45} ${entry.debit:>13,.2f}")

	print("-" * 80)
	print(f"{'TOTAL GST PAID':<58} ${gst_paid:>13,.2f}")

	# Net GST
	net_gst = gst_collected - gst_paid
	print("\n" + "=" * 80)
	print(f"{'NET GST PAYABLE TO ATO':<58} ${net_gst:>13,.2f}")
	print("=" * 80)

	if net_gst > 0:
		print(f"\n📋 You owe the ATO: ${net_gst:,.2f}")
	else:
		print(f"\n📋 The ATO owes you a refund: ${abs(net_gst):,.2f}")

	return {
		"gst_collected": gst_collected,
		"gst_paid": gst_paid,
		"net_gst": net_gst,
	}


# Generate GST report
gst_report = generate_gst_report(transactions, nov_start, nov_end)

# %% [markdown]
# ## 8. Financial Year Summary
#
# Summary of key metrics for the financial year.


# %%
def generate_financial_year_summary(transactions, chart, financial_year):
	"""Generate summary for a financial year."""
	# Determine FY date range (July 1 to June 30)
	year_start = int(financial_year.split("-")[0])
	fy_start = date(year_start, 7, 1)
	fy_end = date(year_start + 1, 6, 30)

	# Filter transactions
	fy_txns = [t for t in transactions if fy_start <= t.date <= fy_end]

	print(f"📊 Financial Year Summary: {financial_year}")
	print(f"Period: {fy_start} to {fy_end}")
	print("=" * 60)

	# Calculate metrics
	income_stmt = generate_income_statement(fy_txns, chart, fy_start, fy_end)
	gst = generate_gst_report(fy_txns, fy_start, fy_end)

	# Summary metrics
	print("\n\n📈 KEY METRICS")
	print("=" * 60)
	print(f"Total Revenue:        ${income_stmt['total_income']:>15,.2f}")
	print(f"Total Expenses:       ${income_stmt['total_expenses']:>15,.2f}")
	print(f"Net Profit:           ${income_stmt['net_profit']:>15,.2f}")

	if income_stmt["total_income"] > 0:
		profit_margin = (income_stmt["net_profit"] / income_stmt["total_income"]) * 100
		print(f"Profit Margin:        {profit_margin:>15.1f}%")

	print(f"\nGST Collected:        ${gst['gst_collected']:>15,.2f}")
	print(f"GST Paid:             ${gst['gst_paid']:>15,.2f}")
	print(f"Net GST Payable:      ${gst['net_gst']:>15,.2f}")

	return income_stmt


# Get financial year for first transaction
sample_fy = get_financial_year(transactions[1].date)
fy_summary = generate_financial_year_summary(transactions, chart, sample_fy)

# %% [markdown]
# ## Key Insights
#
# **★ Insight ─────────────────────────────────────**
#
# 1. **Double-Entry Validation**: The trial balance verification ensures that
#    total debits equal total credits, which is fundamental to double-entry
#    accounting. If this doesn't balance, there's an error in the transactions.
#
# 2. **Financial Statements**: The income statement shows profitability over
#    a period (flow), while the balance sheet shows financial position at a
#    point in time (snapshot). Together they provide a complete picture of
#    business health.
#
# 3. **GST Reconciliation**: The GST report calculates your BAS obligations by
#    separating GST collected (on sales) from GST paid (on purchases). The net
#    amount is what you owe to (or are owed by) the ATO each quarter.
#
# **─────────────────────────────────────────────────**

# %% [markdown]
# ## Cleanup

# %%
# Cleanup temporary directory
shutil.rmtree(data_dir)
print("🗑️  Cleaned up temporary data directory")

# %%
