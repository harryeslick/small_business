"""Convert bank transactions to accounting transactions."""

import datetime
from decimal import Decimal

from small_business.bank.models import BankTransaction
from small_business.models.transaction import JournalEntry, Transaction


def convert_to_transaction(
	bank_txn: BankTransaction,
	bank_account_code: str,
	expense_account_code: str = "EXP-UNCLASSIFIED",
	income_account_code: str = "INC-UNCLASSIFIED",
	import_file: str | None = None,
	import_date: datetime.date | None = None,
) -> Transaction:
	"""Convert bank transaction to accounting transaction.

	Args:
		bank_txn: Bank transaction to convert
		bank_account_code: Account code for the bank account
		expense_account_code: Default account code for expenses (debits)
		income_account_code: Default account code for income (credits)
		import_file: CSV filename for traceability (optional)
		import_date: Date of import for traceability (optional)

	Returns:
		Transaction with double-entry journal entries and import metadata
	"""
	amount = abs(bank_txn.amount)

	# Skip zero-amount transactions (e.g., opening balance)
	if amount == 0:
		# For zero-amount transactions, create a minimal entry
		# This handles things like "Opening Balance" with no amount change
		entries = [
			JournalEntry(
				account_code=bank_account_code, debit=Decimal("0.01"), credit=Decimal("0")
			),
			JournalEntry(account_code="MEMO", debit=Decimal("0"), credit=Decimal("0.01")),
		]
	elif bank_txn.is_debit:
		# Money leaving bank (expense)
		# Debit expense account, Credit bank account
		entries = [
			JournalEntry(account_code=expense_account_code, debit=amount, credit=Decimal("0")),
			JournalEntry(account_code=bank_account_code, debit=Decimal("0"), credit=amount),
		]
	else:
		# Money entering bank (income)
		# Debit bank account, Credit income account
		entries = [
			JournalEntry(account_code=bank_account_code, debit=amount, credit=Decimal("0")),
			JournalEntry(account_code=income_account_code, debit=Decimal("0"), credit=amount),
		]

	# Build import metadata if provided
	import_metadata = {}
	if import_file is not None or import_date is not None:
		import_metadata = {
			"import_source": "bank_import",
			"import_file": import_file,
			"import_date": import_date,
			"import_line_number": bank_txn.line_number,
			# Composite key for duplicate detection (transparent, not hashed - 4 fields)
			"import_match_date": bank_txn.date,
			"import_match_description": bank_txn.description,
			"import_match_amount": bank_txn.amount,
			"import_match_account": bank_account_code,
		}

	return Transaction(
		date=bank_txn.date,
		description=bank_txn.description,
		entries=entries,
		**import_metadata,
	)
