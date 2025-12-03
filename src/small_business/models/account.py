"""Account and ChartOfAccounts models."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from .enums import AccountType


class Account(BaseModel):
	"""Individual account in the chart of accounts."""

	name: str = Field(min_length=1)
	account_type: AccountType
	description: str = ""


class ChartOfAccounts(BaseModel):
	"""Complete chart of accounts with hierarchy utilities."""

	accounts: list[Account]

	@model_validator(mode="after")
	def validate_structure(self):
		"""Validate account structure rules."""
		# Check for duplicate account names
		names = [acc.name for acc in self.accounts]
		duplicates = [name for name in names if names.count(name) > 1]
		if duplicates:
			raise ValueError(f"Duplicate account names found: {set(duplicates)}")

		return self

	def get_account(self, name: str) -> Account:
		"""Get account by name."""
		for account in self.accounts:
			if account.name == name:
				return account
		raise KeyError(f"Account not found: {name}")

	def get_accounts_by_type(self, account_type: AccountType) -> list[Account]:
		"""Get all accounts of a specific type."""
		return [acc for acc in self.accounts if acc.account_type == account_type]

	@classmethod
	def from_yaml(cls, yaml_path: Path | str) -> "ChartOfAccounts":
		"""Load chart of accounts from YAML file.

		Args:
			yaml_path: Path to YAML file containing account structure

		Returns:
			ChartOfAccounts instance

		Raises:
			FileNotFoundError: If yaml_path does not exist
			yaml.YAMLError: If YAML syntax is invalid
			ValidationError: If account structure is invalid
		"""
		with open(yaml_path) as f:
			data = yaml.safe_load(f)

		accounts = []
		for account_type_block in data:
			account_type = AccountType(account_type_block["name"])
			for account_data in account_type_block.get("accounts", []):
				accounts.append(
					Account(
						name=account_data["name"],
						account_type=account_type,
						description=account_data.get("description", ""),
					)
				)

		return cls(accounts=accounts)
