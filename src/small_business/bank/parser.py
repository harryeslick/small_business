"""CSV parsing for bank statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from small_business.bank.models import BankTransaction, ImportedBankStatement
from small_business.models.config import BankFormat


def parse_csv(
	csv_path: Path,
	bank_format: BankFormat,
	bank_name: str,
	account_name: str,
) -> ImportedBankStatement:
	"""Parse bank CSV file using provided format configuration.

	Args:
		csv_path: Path to CSV file
		bank_format: Bank format configuration
		bank_name: Name of the bank
		account_name: Name of the account

	Returns:
		ImportedBankStatement with parsed transactions
	"""
	# Read CSV
	df = pd.read_csv(csv_path)

	# Parse transactions
	transactions = []
	for _, row in df.iterrows():
		# Parse date
		date_str = str(row[bank_format.date_column])
		txn_date = datetime.strptime(date_str, bank_format.date_format).date()

		# Parse description
		description = str(row[bank_format.description_column])

		# Parse amounts
		if bank_format.amount_column:
			# Single amount column (positive = credit, negative = debit)
			amount_str = str(row[bank_format.amount_column])
			if amount_str in ("", "nan"):
				amount = Decimal("0")
			else:
				amount = Decimal(amount_str)

			if amount >= 0:
				debit = Decimal("0")
				credit = amount
			else:
				debit = -amount
				credit = Decimal("0")
		else:
			# Separate debit/credit columns
			debit_str = str(row[bank_format.debit_column]) if bank_format.debit_column else ""
			credit_str = str(row[bank_format.credit_column]) if bank_format.credit_column else ""

			debit = Decimal("0") if debit_str in ("", "nan") else Decimal(debit_str)
			credit = Decimal("0") if credit_str in ("", "nan") else Decimal(credit_str)

		# Parse balance (optional)
		balance = None
		if bank_format.balance_column:
			balance_str = str(row[bank_format.balance_column])
			balance = None if balance_str in ("", "nan") else Decimal(balance_str)

		# Create transaction
		txn = BankTransaction(
			date=txn_date,
			description=description,
			debit=debit,
			credit=credit,
			balance=balance,
		)
		transactions.append(txn)

	return ImportedBankStatement(
		bank_name=bank_name,
		account_name=account_name,
		transactions=transactions,
	)
