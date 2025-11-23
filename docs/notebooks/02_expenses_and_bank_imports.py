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
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

# Import models
from small_business.models import (
	AccountType,
	Account,
	ChartOfAccounts,
)
from small_business.bank import (
	parse_bank_csv,
	convert_to_transaction,
	detect_duplicates,
)
from small_business.classification import (
	create_rule,
	apply_rules,
	classify_transaction,
	learn_from_classification,
	list_unclassified_transactions,
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

# %%
# Create chart of accounts (same as workflow example)
accounts = [
	# Assets
	Account(code="BANK", name="Bank Account", account_type=AccountType.ASSET),
	Account(code="AR", name="Accounts Receivable", account_type=AccountType.ASSET),
	Account(code="INV", name="Inventory", account_type=AccountType.ASSET),
	# Liabilities
	Account(code="AP", name="Accounts Payable", account_type=AccountType.LIABILITY),
	Account(code="GST", name="GST Collected", account_type=AccountType.LIABILITY),
	Account(code="GST-PAID", name="GST Paid", account_type=AccountType.LIABILITY),
	# Equity
	Account(code="EQUITY", name="Owner's Equity", account_type=AccountType.EQUITY),
	# Income
	Account(code="INC", name="Income", account_type=AccountType.INCOME),
	Account(
		code="INC-CLASSES", name="Class Fees", account_type=AccountType.INCOME, parent_code="INC"
	),
	Account(
		code="INC-COMMISSIONS",
		name="Commission Work",
		account_type=AccountType.INCOME,
		parent_code="INC",
	),
	Account(
		code="INC-SALES", name="Product Sales", account_type=AccountType.INCOME, parent_code="INC"
	),
	# Expenses
	Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
	Account(
		code="EXP-MATERIALS",
		name="Materials & Supplies",
		account_type=AccountType.EXPENSE,
		parent_code="EXP",
	),
	Account(
		code="EXP-STUDIO", name="Studio Rent", account_type=AccountType.EXPENSE, parent_code="EXP"
	),
	Account(
		code="EXP-UTILITIES", name="Utilities", account_type=AccountType.EXPENSE, parent_code="EXP"
	),
	Account(
		code="EXP-MARKETING", name="Marketing", account_type=AccountType.EXPENSE, parent_code="EXP"
	),
	Account(
		code="EXP-INSURANCE", name="Insurance", account_type=AccountType.EXPENSE, parent_code="EXP"
	),
	Account(
		code="EXP-SOFTWARE",
		name="Software Subscriptions",
		account_type=AccountType.EXPENSE,
		parent_code="EXP",
	),
]

chart = ChartOfAccounts(accounts=accounts)
print("✅ Chart of accounts created")
print(
	f"   Expense accounts: {len([a for a in chart.accounts if a.account_type == AccountType.EXPENSE])}"
)

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
# Import and parse the bank CSV file.

# %%
# Parse bank CSV
bank_transactions = parse_bank_csv(csv_path)
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
	if bank_txn.credit:
		# Income: Debit BANK, Credit income account
		# For this example, we'll classify all income as general income
		txn = convert_to_transaction(
			bank_txn,
			debit_account="BANK",
			credit_account="INC",
			description=f"Income: {bank_txn.description}",
		)
	elif bank_txn.debit:
		# Expense: Debit expense account, Credit BANK
		# For now, use generic expense account (we'll classify later)
		txn = convert_to_transaction(
			bank_txn,
			debit_account="EXP",
			credit_account="BANK",
			description=f"Expense: {bank_txn.description}",
		)
	else:
		continue  # Skip opening balance

	transactions.append(txn)

print(f"✅ Converted {len(transactions)} bank transactions to accounting transactions")

# %% [markdown]
# ## 5. Duplicate Detection
#
# Check for duplicate transactions before importing.

# %%
# Simulate existing transactions in storage
existing_txn_ids = []

# Import new transactions, checking for duplicates
duplicates = detect_duplicates(transactions, existing_txn_ids)

if duplicates:
	print(f"⚠️  Found {len(duplicates)} duplicate transactions (skipped)")
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
# Create classification rules
rules = [
	# Materials and supplies
	create_rule(
		description_pattern="CLAY SUPPLIES",
		account_code="EXP-MATERIALS",
		rule_name="Clay supplier",
	),
	create_rule(
		description_pattern="POTTER'S WAREHOUSE",
		account_code="EXP-MATERIALS",
		rule_name="Pottery supplier",
	),
	create_rule(
		description_pattern="WALKER CERAMICS",
		account_code="EXP-MATERIALS",
		rule_name="Ceramics supplier",
	),
	# Studio rent
	create_rule(
		description_pattern="STUDIO RENT",
		account_code="EXP-STUDIO",
		rule_name="Monthly rent",
	),
	# Utilities
	create_rule(
		description_pattern="AGL ENERGY",
		account_code="EXP-UTILITIES",
		rule_name="Electricity",
	),
	# Marketing
	create_rule(
		description_pattern="INSTAGRAM ADS",
		account_code="EXP-MARKETING",
		rule_name="Social media advertising",
	),
	create_rule(
		description_pattern="CANVA",
		account_code="EXP-SOFTWARE",
		rule_name="Design software",
	),
	# Income classification
	create_rule(
		description_pattern="PAYPAL \\*GALLERY27",
		account_code="INC-COMMISSIONS",
		rule_name="Gallery commission payment",
	),
	create_rule(
		description_pattern="PAYPAL \\*PRIVATECLIENT",
		account_code="INC-CLASSES",
		rule_name="Private class payment",
	),
]

print(f"✅ Created {len(rules)} classification rules")

# Display rules
print("\n📋 Classification Rules:")
for rule in rules:
	print(f"   '{rule.description_pattern}' → {rule.account_code} ({rule.rule_name})")

# %% [markdown]
# ## 7. Apply Classification Rules
#
# Automatically classify transactions using the rules.

# %%
# Apply rules to all transactions
classified_count = 0
for txn in transactions:
	matched_rule = apply_rules(txn, rules, chart)
	if matched_rule:
		classified_count += 1
		print(f"✅ Classified: {txn.description[:50]} → {matched_rule.account_code}")

print(f"\n✅ Classified {classified_count}/{len(transactions)} transactions")

# %% [markdown]
# ## 8. Manual Classification
#
# For transactions that don't match any rules, classify them manually.

# %%
# Find unclassified transactions
unclassified = list_unclassified_transactions(transactions)
print(f"📋 Unclassified transactions: {len(unclassified)}")

# Manually classify one transaction
if unclassified:
	example_txn = unclassified[0]
	print(f"\n📝 Manually classifying: {example_txn.description}")

	# Classify as general materials expense (Bunnings purchase)
	classified_txn = classify_transaction(
		example_txn,
		account_code="EXP-MATERIALS",
		chart=chart,
	)

	print("✅ Classified to: EXP-MATERIALS")

	# Learn from this classification to create a new rule
	new_rule = learn_from_classification(
		example_txn,
		"EXP-MATERIALS",
		rule_name="Hardware store - materials",
	)
	rules.append(new_rule)
	print(f"✅ Created new rule: '{new_rule.description_pattern}' → {new_rule.account_code}")

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
		if entry.account_code == "EXP-MATERIALS" and entry.debit > 0:
			job_expenses.append(txn.transaction_id)
			print(f"💼 Linked to job {job_id}: {txn.description} (${entry.debit:.2f})")

# Calculate total job costs
total_job_costs = sum(
	entry.debit
	for txn in transactions
	if txn.transaction_id in job_expenses
	for entry in txn.entries
	if entry.account_code == "EXP-MATERIALS"
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
final_unclassified = list_unclassified_transactions(transactions)

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
