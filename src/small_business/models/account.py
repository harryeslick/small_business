"""Account and ChartOfAccounts models."""

from pydantic import BaseModel, Field, model_validator

from .enums import AccountType


class Account(BaseModel):
	"""Individual account in the chart of accounts."""

	code: str = Field(pattern=r"^[A-Z0-9\-]+$")
	name: str = Field(min_length=1)
	account_type: AccountType
	parent_code: str | None = None
	description: str = ""


class ChartOfAccounts(BaseModel):
	"""Complete chart of accounts with hierarchy utilities."""

	accounts: list[Account]

	@model_validator(mode="after")
	def validate_structure(self):
		"""Validate account hierarchy rules."""
		codes = {acc.code for acc in self.accounts}

		# Check all parent_codes exist
		for account in self.accounts:
			if account.parent_code and account.parent_code not in codes:
				raise ValueError(f"Parent '{account.parent_code}' not found for '{account.code}'")

		# Check max 2-level hierarchy
		for account in self.accounts:
			if account.parent_code:
				parent = self.get_account(account.parent_code)
				if parent.parent_code is not None:
					raise ValueError(f"Max 2-level hierarchy exceeded: '{account.code}'")

		return self

	def get_account(self, code: str) -> Account:
		"""Get account by code."""
		for account in self.accounts:
			if account.code == code:
				return account
		raise KeyError(f"Account not found: {code}")

	def get_children(self, parent_code: str) -> list[Account]:
		"""Get all child accounts of a parent."""
		return [acc for acc in self.accounts if acc.parent_code == parent_code]

	def get_root_accounts(self) -> list[Account]:
		"""Get all top-level accounts (no parent)."""
		return [acc for acc in self.accounts if acc.parent_code is None]
