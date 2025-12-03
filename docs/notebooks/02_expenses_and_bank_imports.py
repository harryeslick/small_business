# %% [markdown]
# # Bank Imports and Expense Tracking
#
# This notebook demonstrates expense management and bank statement import features:
#
# 1. Importing bank statements (CSV format)
# 2. Detecting and handling duplicate transactions
# 3. Classifying expenses with rules
# 4. Manual classification and rule learning
# 5. Linking expenses to jobs for profitability tracking
# 6. Basic expense reporting
#
# **Business Context**: Continuing with Earthworks Studio (ceramics business)

# %% [markdown]
# ## Setup and Imports

# %%
import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from importlib.resources import files
from pathlib import Path

# Import models
from small_business.models import (
	AccountType,
	ChartOfAccounts,
)
from small_business.bank import (
	convert_to_transaction,
	is_duplicate,
)
from small_business.bank.models import BankTransaction
from small_business.classification import (
	ClassificationRule,
	classify_transaction,
	learn_rule,
)
from small_business.storage import StorageRegistry

# Create temporary data directory
data_dir = Path(tempfile.mkdtemp(prefix="earthworks_expenses_"))
print(f"📁 Data directory: {data_dir}")

# Initialize storage registry
storage = StorageRegistry(data_dir)

# %% [markdown]
# ## 1. Setup Chart of Accounts
#
# First, we need the chart of accounts for expense classification.
# We'll use the default chart of accounts included with the package.

# %%
# Load default chart of accounts from package data
default_coa_path = str(files("small_business.data").joinpath("default_chart_of_accounts.yaml"))
chart = ChartOfAccounts.from_yaml(default_coa_path)

print(f"✅ Chart of accounts loaded with {len(chart.accounts)} accounts")
print(f"   Income accounts: {len(chart.get_accounts_by_type(AccountType.INCOME))}")
print(f"   Expense accounts: {len(chart.get_accounts_by_type(AccountType.EXPENSE))}")

# %% [markdown]
# ## 2. Sample Bank Statement
#
# Create a sample bank CSV with realistic transactions for an arts business.

# %%
# Create sample bank CSV data
bank_csv_data = """Date,Description,Debit,Credit,Balance
2025-11-01,OPENING BALANCE,,,5420.50
2025-11-03,PAYPAL *GALLERY27,,-3400.00,8820.50
2025-11-05,CLAY SUPPLIES PTY LTD,285.00,,8535.50
2025-11-07,BUNNINGS - FITZROY,127.50,,8408.00
2025-11-10,CANVA PRO SUBSCRIPTION,17.99,,8390.01
2025-11-12,AGL ENERGY,145.00,,8245.01
2025-11-15,POTTER'S WAREHOUSE,456.80,,7788.21
2025-11-18,PAYPAL *PRIVATECLIENT,,-850.00,8638.21
2025-11-20,STUDIO RENT - NOV,1200.00,,7438.21
2025-11-22,INSTAGRAM ADS,95.00,,7343.21
2025-11-25,WALKER CERAMICS,234.50,,7108.71
"""

# Save to temporary CSV file
csv_path = data_dir / "bank_statement_nov2025.csv"
csv_path.write_text(bank_csv_data)
print(f"✅ Sample bank statement created: {csv_path.name}")

# %% [markdown]
# ## 3. Parse Bank Statement
#
# Import and parse the bank CSV file. For this example, we'll manually parse
# the simple CSV format. In production, you'd use the bank.parse_csv() function
# with appropriate BankFormat configuration.

# %%
# For this example, we'll create transactions directly from the CSV data
# In production, you'd use: bank.parse_csv(csv_path, bank_format, bank_name, account_name)

# Simple manual parsing for demo purposes
bank_transactions = []
csv_lines = bank_csv_data.strip().split("\n")[1:]  # Skip header
for line in csv_lines:
	parts = line.split(",")
	date_str, description, debit_str, credit_str, balance_str = parts

	date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
	debit = Decimal(debit_str) if debit_str else Decimal("0")
	credit = Decimal(credit_str) if credit_str else Decimal("0")
	balance = Decimal(balance_str) if balance_str else None

	if debit > 0 or credit > 0:  # Skip opening balance line
		bank_transactions.append(
			BankTransaction(
				date=date_obj,
				description=description,
				debit=debit,
				credit=credit,
				balance=balance,
			)
		)

print(f"✅ Parsed {len(bank_transactions)} transactions from bank statement")

# Display sample transactions
print("\n📋 Sample Bank Transactions:")
for txn in bank_transactions[:5]:
	direction = "Credit" if txn.credit else "Debit"
	amount = txn.credit if txn.credit else txn.debit
	print(f"   {txn.date} | {direction:6} | ${amount:>8.2f} | {txn.description}")

# %% [markdown]
# ## 4. Convert to Accounting Transactions
#
# Convert bank transactions to double-entry accounting transactions.

# %%
# Convert bank transactions to accounting transactions
# Note: This is a simplified conversion. Real implementation would use
# classification rules to determine the correct expense accounts.

transactions = []
for bank_txn in bank_transactions:
	# Convert using the bank converter
	# For unclassified transactions, use placeholder accounts
	txn = convert_to_transaction(
		bank_txn,
		bank_account_code="Bank Account",
		expense_account_code="Miscellaneous Expenses",
		income_account_code="Other Income",
	)
	transactions.append(txn)

print(f"✅ Converted {len(transactions)} bank transactions to accounting transactions")

# %% [markdown]
# ## 5. Duplicate Detection
#
# Check for duplicate transactions before importing.
# The `is_duplicate` function checks if a bank transaction already exists.

# %%
# For this demo, we don't have existing bank statements
# In production, you'd load previous statements and check for duplicates

existing_statements = []  # Would load from storage in production

# Check for duplicates
duplicate_count = 0
for bank_txn in bank_transactions:
	if is_duplicate(bank_txn, existing_statements):
		duplicate_count += 1

if duplicate_count > 0:
	print(f"⚠️  Found {duplicate_count} duplicate transactions (would skip)")
else:
	print("✅ No duplicates found")

# Save transactions to storage
for txn in transactions:
	storage.save_transaction(txn)

print(f"✅ Saved {len(transactions)} transactions to storage")

# %% [markdown]
# ## 6. Expense Classification with Rules
#
# Create classification rules to automatically categorize expenses.

# %%
# Create classification rules using ClassificationRule model
# Note: account_code here refers to the account NAME from the chart of accounts
rules = [
	# Materials and supplies
	ClassificationRule(
		pattern="CLAY SUPPLIES",
		account_code="Materials & Supplies",
		description="Clay supplier",
		gst_inclusive=True,
	),
	ClassificationRule(
		pattern="POTTER'S WAREHOUSE",
		account_code="Materials & Supplies",
		description="Pottery supplier",
		gst_inclusive=True,
	),
	ClassificationRule(
		pattern="WALKER CERAMICS",
		account_code="Materials & Supplies",
		description="Ceramics supplier",
		gst_inclusive=True,
	),
	# Studio rent
	ClassificationRule(
		pattern="STUDIO RENT",
		account_code="Studio Rent",
		description="Monthly rent",
		gst_inclusive=False,  # Commercial rent is typically GST-free
	),
	# Utilities
	ClassificationRule(
		pattern="AGL ENERGY",
		account_code="Utilities",
		description="Electricity",
		gst_inclusive=True,
	),
	# Marketing
	ClassificationRule(
		pattern="INSTAGRAM ADS",
		account_code="Marketing & Advertising",
		description="Social media advertising",
		gst_inclusive=True,
	),
	ClassificationRule(
		pattern="CANVA",
		account_code="Software & Subscriptions",
		description="Design software",
		gst_inclusive=True,
	),
	# Income classification
	ClassificationRule(
		pattern="PAYPAL \\*GALLERY27",
		account_code="Commission Work",
		description="Gallery commission payment",
		gst_inclusive=True,
	),
	ClassificationRule(
		pattern="PAYPAL \\*PRIVATECLIENT",
		account_code="Class Fees",
		description="Private class payment",
		gst_inclusive=True,
	),
]

print(f"✅ Created {len(rules)} classification rules")

# Display rules
print("\n📋 Classification Rules:")
for rule in rules:
	print(f"   '{rule.pattern}' → {rule.account_code} ({rule.description})")

# %% [markdown]
# ## 7. Apply Classification Rules
#
# Automatically classify transactions using the rules.

# %%
# Apply rules to all transactions
classified_count = 0
for txn in transactions:
	# Try to find a matching rule
	rule_match = classify_transaction(txn, rules)
	if rule_match:
		classified_count += 1
		print(f"✅ Classified: {txn.description[:50]} → {rule_match.rule.account_code}")

print(f"\n✅ Classified {classified_count}/{len(transactions)} transactions")

# %% [markdown]
# ## 8. Manual Classification
#
# For transactions that don't match any rules, classify them manually.

# %%
# Find unclassified transactions by checking which ones didn't match any rule
unclassified = []
for txn in transactions:
	rule_match = classify_transaction(txn, rules)
	if not rule_match:
		unclassified.append(txn)

print(f"📋 Unclassified transactions: {len(unclassified)}")

# Manually classify one transaction
if unclassified:
	example_txn = unclassified[0]
	print(f"\n📝 Manually classifying: {example_txn.description}")

	# Learn from this manual classification to create a new rule
	# This extracts a pattern from the transaction description
	new_rule = learn_rule(
		example_txn,
		account_code="Materials & Supplies",
		description="Hardware store - materials",
		gst_inclusive=True,
	)
	rules.append(new_rule)
	print(f"✅ Created new rule: '{new_rule.pattern}' → {new_rule.account_code}")
	print(f"   Description: {new_rule.description}")

# %% [markdown]
# ## 9. Link Expenses to Jobs
#
# Track which expenses are related to specific jobs for profitability analysis.

# %%
# Example: Link material purchases to a job
job_id = "J-20251123-001"  # From the workflow example
job_expenses = []

# Find material expense transactions
for txn in transactions:
	# Check if transaction is a materials expense
	for entry in txn.entries:
		if entry.account_code == "Materials & Supplies" and entry.debit > 0:
			job_expenses.append(txn.transaction_id)
			print(f"💼 Linked to job {job_id}: {txn.description} (${entry.debit:.2f})")

# Calculate total job costs
total_job_costs = sum(
	entry.debit
	for txn in transactions
	if txn.transaction_id in job_expenses
	for entry in txn.entries
	if entry.account_code == "Materials & Supplies"
)

print(f"\n💰 Total job costs: ${total_job_costs:,.2f}")

# %% [markdown]
# ## 10. Expense Summary Report
#
# Generate a summary of expenses by category.

# %%
# Calculate expenses by account
expense_summary = {}
income_summary = {}

for txn in transactions:
	for entry in txn.entries:
		account = chart.get_account(entry.account_code)

		if account.account_type == AccountType.EXPENSE and entry.debit > 0:
			if entry.account_code not in expense_summary:
				expense_summary[entry.account_code] = {
					"name": account.name,
					"total": Decimal(0),
					"count": 0,
				}
			expense_summary[entry.account_code]["total"] += entry.debit
			expense_summary[entry.account_code]["count"] += 1

		elif account.account_type == AccountType.INCOME and entry.credit > 0:
			if entry.account_code not in income_summary:
				income_summary[entry.account_code] = {
					"name": account.name,
					"total": Decimal(0),
					"count": 0,
				}
			income_summary[entry.account_code]["total"] += entry.credit
			income_summary[entry.account_code]["count"] += 1

# Display expense summary
print("💸 Expense Summary:")
print(f"{'Account':<20} {'Category':<30} {'Count':>6} {'Total':>12}")
print("-" * 70)
total_expenses = Decimal(0)
for code, data in sorted(expense_summary.items()):
	print(f"{code:<20} {data['name']:<30} {data['count']:>6} ${data['total']:>10,.2f}")
	total_expenses += data["total"]
print("-" * 70)
print(f"{'TOTAL EXPENSES':<51} ${total_expenses:>10,.2f}")

# Display income summary
print("\n💰 Income Summary:")
print(f"{'Account':<20} {'Category':<30} {'Count':>6} {'Total':>12}")
print("-" * 70)
total_income = Decimal(0)
for code, data in sorted(income_summary.items()):
	print(f"{code:<20} {data['name']:<30} {data['count']:>6} ${data['total']:>10,.2f}")
	total_income += data["total"]
print("-" * 70)
print(f"{'TOTAL INCOME':<51} ${total_income:>10,.2f}")

print(f"\n📊 Net Position: ${(total_income - total_expenses):,.2f}")

# %% [markdown]
# ## 11. GST Summary
#
# Calculate GST paid on expenses (for BAS preparation).

# %%
# Calculate GST paid
total_gst_paid = Decimal(0)
gst_rate = Decimal("0.10")

print("💵 GST Summary:")
print(f"{'Transaction':<50} {'Amount':>12} {'GST':>12}")
print("-" * 75)

for txn in transactions:
	if txn.gst_inclusive:
		# Calculate GST component (1/11 of total for GST-inclusive)
		amount = txn.amount
		gst_amount = (amount / Decimal("11")).quantize(Decimal("0.01"))
		total_gst_paid += gst_amount
		print(f"{txn.description[:48]:<50} ${amount:>10,.2f} ${gst_amount:>10,.2f}")

print("-" * 75)
print(f"{'TOTAL GST PAID':<50} ${total_gst_paid:>10,.2f}")

# %% [markdown]
# ## 12. Unclassified Transactions Report
#
# Identify transactions that still need classification.

# %%
# Find remaining unclassified transactions
final_unclassified = []
for txn in transactions:
	rule_match = classify_transaction(txn, rules)
	if not rule_match:
		final_unclassified.append(txn)

print(f"⚠️  Unclassified Transactions: {len(final_unclassified)}")
if final_unclassified:
	print("\n📋 Transactions needing classification:")
	for txn in final_unclassified:
		print(f"   {txn.date} | {txn.description[:50]:<50} | ${txn.amount:>10,.2f}")
else:
	print("✅ All transactions classified!")

# %% [markdown]
# ## Key Insights
#
# **★ Insight ─────────────────────────────────────**
#
# 1. **Rule-Based Classification**: Classification rules use regex pattern matching
#    to automatically categorize transactions. Once created, rules eliminate manual
#    work for recurring expenses like rent, utilities, and regular suppliers.
#
# 2. **Learning from Manual Classification**: When you manually classify a
#    transaction, the system can suggest creating a rule for similar future
#    transactions. This builds your classification ruleset over time.
#
# 3. **Job Cost Tracking**: Linking expense transactions to specific jobs enables
#    accurate profitability analysis. You can compare actual costs against quoted
#    prices to understand your margins.
#
# **─────────────────────────────────────────────────**

# %% [markdown]
# ## Cleanup

# %%
# Cleanup temporary directory
shutil.rmtree(data_dir)
print("🗑️  Cleaned up temporary data directory")

# %%
