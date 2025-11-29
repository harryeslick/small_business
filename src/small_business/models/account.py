"""Account and ChartOfAccounts models."""

from pathlib import Path

import yaml
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

	def save(self, file_path: Path) -> None:
		"""Save chart of accounts to YAML file with nested structure.

		Args:
			file_path: Path to save the YAML file
		"""
		# Ensure parent directory exists
		file_path.parent.mkdir(parents=True, exist_ok=True)

		# Build nested structure with sub_accounts
		def build_account_dict(account: Account, is_root: bool = True) -> dict:
			"""Convert account to dict with sub_accounts instead of parent_code."""
			account_dict = {
				"code": account.code,
				"name": account.name,
			}

			# Only include account_type for root accounts (children inherit from parent)
			if is_root:
				account_dict["account_type"] = account.account_type.value

			account_dict["description"] = account.description

			# Find children and add as sub_accounts (not root)
			children = self.get_children(account.code)
			if children:
				account_dict["sub_accounts"] = [
					build_account_dict(child, is_root=False) for child in children
				]

			return account_dict

		# Get root accounts and build nested structure
		root_accounts = self.get_root_accounts()
		nested_data = [build_account_dict(acc, is_root=True) for acc in root_accounts]

		# Write to YAML
		with open(file_path, "w") as f:
			yaml.safe_dump(nested_data, f, default_flow_style=False, sort_keys=False)

	@classmethod
	def load(cls, file_path: Path) -> "ChartOfAccounts":
		"""Load chart of accounts from YAML file with nested structure.

		Args:
			file_path: Path to the YAML file

		Returns:
			Loaded ChartOfAccounts instance

		Raises:
			FileNotFoundError: If file doesn't exist
		"""
		if not file_path.exists():
			raise FileNotFoundError(f"Chart of accounts file not found: {file_path}")

		with open(file_path) as f:
			data = yaml.safe_load(f)

		# Flatten nested structure into list of accounts
		def flatten_accounts(
			account_dict: dict,
			parent_code: str | None = None,
			parent_account_type: str | None = None,
		) -> list[Account]:
			"""Recursively flatten nested account structure.

			Args:
				account_dict: Account data from YAML
				parent_code: Parent account code (None for root accounts)
				parent_account_type: Parent's account type (inherited by children)
			"""
			accounts = []

			# Get account_type: from dict for root accounts, inherited from parent for children
			account_type = account_dict.get("account_type", parent_account_type)

			# Create the account (without sub_accounts field)
			account_data = {
				"code": account_dict["code"],
				"name": account_dict["name"],
				"account_type": account_type,
				"description": account_dict.get("description", ""),
				"parent_code": parent_code,
			}
			accounts.append(Account(**account_data))

			# Process sub_accounts recursively (inherit account_type)
			if "sub_accounts" in account_dict:
				for sub_account in account_dict["sub_accounts"]:
					accounts.extend(
						flatten_accounts(sub_account, account_dict["code"], account_type)
					)

			return accounts

		# Flatten all root accounts
		all_accounts = []
		for root_account in data:
			all_accounts.extend(flatten_accounts(root_account))

		return cls(accounts=all_accounts)
