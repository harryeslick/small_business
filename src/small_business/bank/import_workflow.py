"""Bank import workflow orchestration."""

import datetime
from pathlib import Path

from small_business.bank.converter import convert_to_transaction
from small_business.bank.duplicate import is_duplicate
from small_business.bank.models import ImportedBankStatement
from small_business.bank.parser import parse_csv
from small_business.models import get_financial_year
from small_business.models.config import BankFormat
from small_business.storage import StorageRegistry


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
	storage = StorageRegistry(data_dir)
	existing_statements: list[ImportedBankStatement] = []
	if statement.transactions:
		# We'll check duplicates by loading all transactions from relevant financial years
		# For simplicity, load from the first transaction's date
		first_date = statement.transactions[0].date
		fy = get_financial_year(first_date)
		existing_txns = storage.get_all_transactions(financial_year=fy)

		# Convert to ImportedBankStatement format for duplicate checking
		# ONLY include transactions for the current bank account being imported
		if existing_txns:
			from small_business.bank.models import BankTransaction
			from decimal import Decimal

			bank_txns = []
			for txn in existing_txns:
				# Only check duplicates against transactions from THIS specific account
				# Check if this transaction involves the current bank account
				# using the composite key match field
				if txn.import_match_account != bank_account_code:
					continue  # Skip transactions from other accounts

				# Reconstruct approximate bank transaction from accounting transaction
				# Determine if it's a debit or credit by checking which account is the bank account
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
					# Skip if bank account not found in entries
					continue

				bank_txn = BankTransaction(
					date=txn.date,
					description=txn.description,
					debit=debit,
					credit=credit,
				)
				bank_txns.append(bank_txn)

			if bank_txns:  # Only add statement if we found matching transactions
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
	import_date = datetime.date.today()
	csv_filename = csv_path.name

	for bank_txn in statement.transactions:
		# Check duplicate
		if is_duplicate(bank_txn, existing_statements):
			duplicates += 1
			continue

		# Convert to accounting transaction with traceability metadata
		accounting_txn = convert_to_transaction(
			bank_txn,
			bank_account_code=bank_account_code,
			expense_account_code=expense_account_code,
			income_account_code=income_account_code,
			import_file=csv_filename,
			import_date=import_date,
		)

		# Save transaction
		storage.save_transaction(accounting_txn)
		imported += 1

	return {"imported": imported, "duplicates": duplicates}
