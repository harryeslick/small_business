"""Bank import workflow orchestration."""

from pathlib import Path

from small_business.bank.converter import convert_to_transaction
from small_business.bank.duplicate import is_duplicate
from small_business.bank.models import ImportedBankStatement
from small_business.bank.parser import parse_csv
from small_business.models.config import BankFormat
from small_business.storage.transaction_store import load_transactions, save_transaction


def import_bank_statement(
	csv_path: Path,
	bank_format: BankFormat,
	bank_name: str,
	account_name: str,
	bank_account_code: str,
	data_dir: Path,
	expense_account_code: str = "EXP-UNCLASSIFIED",
	income_account_code: str = "INC-UNCLASSIFIED",
) -> dict[str, int]:
	"""Import bank statement CSV to accounting transactions.

	Workflow:
	1. Parse CSV using bank format
	2. Check for duplicates
	3. Convert to accounting transactions
	4. Save to storage

	Args:
		csv_path: Path to CSV file
		bank_format: Bank format configuration
		bank_name: Name of the bank
		account_name: Name of the account
		bank_account_code: Account code for bank account
		data_dir: Data directory for storage
		expense_account_code: Default account for expenses
		income_account_code: Default account for income

	Returns:
		Dictionary with import statistics:
		- imported: Number of new transactions imported
		- duplicates: Number of duplicates skipped
	"""
	# Parse CSV
	statement = parse_csv(csv_path, bank_format, bank_name, account_name)

	# Load existing transactions to check duplicates
	# Get all transactions from the financial year(s) covered by this statement
	existing_statements: list[ImportedBankStatement] = []
	if statement.transactions:
		# We'll check duplicates by loading all transactions from relevant financial years
		# For simplicity, load from the first transaction's date
		first_date = statement.transactions[0].date
		existing_txns = load_transactions(data_dir, first_date)

		# Convert to ImportedBankStatement format for duplicate checking
		if existing_txns:
			# Group by date for statement format (simplified)
			from small_business.bank.models import BankTransaction
			from decimal import Decimal

			bank_txns = []
			for txn in existing_txns:
				# Reconstruct approximate bank transaction from accounting transaction
				# This is simplified - just need for duplicate detection
				# Determine if it's a debit or credit by checking which account is the bank account
				# Bank account debit = money in, Bank account credit = money out
				bank_entry = next(
					(e for e in txn.entries if e.account_code == bank_account_code), None
				)

				if bank_entry:
					if bank_entry.debit > 0:
						# Money into bank (income/credit)
						debit = Decimal("0")
						credit = bank_entry.debit
					else:
						# Money out of bank (expense/debit)
						debit = bank_entry.credit
						credit = Decimal("0")
				else:
					# Fallback if bank account not found
					debit = Decimal("0")
					credit = Decimal("0")

				bank_txn = BankTransaction(
					date=txn.date,
					description=txn.description,
					debit=debit,
					credit=credit,
				)
				bank_txns.append(bank_txn)

			existing_statements.append(
				ImportedBankStatement(
					bank_name=bank_name,
					account_name=account_name,
					transactions=bank_txns,
				)
			)

	# Import transactions
	imported = 0
	duplicates = 0

	for bank_txn in statement.transactions:
		# Check duplicate
		if is_duplicate(bank_txn, existing_statements):
			duplicates += 1
			continue

		# Convert to accounting transaction
		accounting_txn = convert_to_transaction(
			bank_txn,
			bank_account_code=bank_account_code,
			expense_account_code=expense_account_code,
			income_account_code=income_account_code,
		)

		# Save transaction
		save_transaction(accounting_txn, data_dir)
		imported += 1

	return {"imported": imported, "duplicates": duplicates}
