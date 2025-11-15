"""Convert bank transactions to accounting transactions."""

from decimal import Decimal

from small_business.bank.models import BankTransaction
from small_business.models.transaction import JournalEntry, Transaction


def convert_to_transaction(
	bank_txn: BankTransaction,
	bank_account_code: str,
	expense_account_code: str = "EXP-UNCLASSIFIED",
	income_account_code: str = "INC-UNCLASSIFIED",
) -> Transaction:
	"""Convert bank transaction to accounting transaction.

	Args:
		bank_txn: Bank transaction to convert
		bank_account_code: Account code for the bank account
		expense_account_code: Default account code for expenses (debits)
		income_account_code: Default account code for income (credits)

	Returns:
		Transaction with double-entry journal entries
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

	return Transaction(
		date=bank_txn.date,
		description=bank_txn.description,
		entries=entries,
	)
