"""Tests for Account and ChartOfAccounts models."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from small_business.models.account import Account, ChartOfAccounts
from small_business.models.enums import AccountType


def test_account_creation():
	"""Test creating an account."""
	account = Account(
		name="Travel",
		account_type=AccountType.EXPENSE,
		description="Travel expenses",
	)
	assert account.name == "Travel"
	assert account.account_type == AccountType.EXPENSE
	assert account.description == "Travel expenses"


def test_account_default_description():
	"""Test that description defaults to empty string."""
	account = Account(
		name="Cash",
		account_type=AccountType.ASSET,
	)
	assert account.description == ""


def test_chart_of_accounts_creation():
	"""Test creating a chart of accounts."""
	chart = ChartOfAccounts(
		accounts=[
			Account(name="Expenses", account_type=AccountType.EXPENSE),
			Account(name="Travel", account_type=AccountType.EXPENSE),
			Account(name="Income", account_type=AccountType.INCOME),
		]
	)
	assert len(chart.accounts) == 3


def test_chart_get_account():
	"""Test retrieving account by name."""
	chart = ChartOfAccounts(
		accounts=[
			Account(name="Expenses", account_type=AccountType.EXPENSE),
			Account(name="Income", account_type=AccountType.INCOME),
		]
	)
	account = chart.get_account("Expenses")
	assert account.name == "Expenses"


def test_chart_get_account_not_found():
	"""Test getting account that doesn't exist."""
	chart = ChartOfAccounts(accounts=[Account(name="Expenses", account_type=AccountType.EXPENSE)])
	with pytest.raises(KeyError):
		chart.get_account("NOTFOUND")


def test_chart_get_accounts_by_type():
	"""Test getting accounts by type."""
	chart = ChartOfAccounts(
		accounts=[
			Account(name="Cash", account_type=AccountType.ASSET),
			Account(name="Accounts Receivable", account_type=AccountType.ASSET),
			Account(name="Sales", account_type=AccountType.INCOME),
		]
	)
	assets = chart.get_accounts_by_type(AccountType.ASSET)
	assert len(assets) == 2
	assert {a.name for a in assets} == {"Cash", "Accounts Receivable"}


def test_chart_validates_duplicate_names():
	"""Test that chart validates duplicate account names."""
	with pytest.raises(ValidationError) as exc_info:
		ChartOfAccounts(
			accounts=[
				Account(name="Cash", account_type=AccountType.ASSET),
				Account(name="Cash", account_type=AccountType.ASSET),
			]
		)
	assert "Duplicate account names" in str(exc_info.value)


def test_from_yaml_valid_file():
	"""Test loading chart of accounts from valid YAML file."""
	fixture_path = Path(__file__).parent.parent / "fixtures" / "chart_of_accounts.yaml"
	chart = ChartOfAccounts.from_yaml(fixture_path)

	assert len(chart.accounts) == 6
	assert chart.get_account("Cash").account_type == AccountType.ASSET
	assert chart.get_account("Sales").account_type == AccountType.INCOME
	assert chart.get_account("Supplies").account_type == AccountType.EXPENSE


def test_from_yaml_invalid_account_type():
	"""Test that invalid account type raises error."""
	invalid_yaml = """
- name: invalid_type
  accounts:
    - name: Test Account
"""
	tmp_file = Path("/tmp/test_invalid_type.yaml")
	tmp_file.write_text(invalid_yaml)

	with pytest.raises(ValueError):
		ChartOfAccounts.from_yaml(tmp_file)


def test_from_yaml_duplicate_names():
	"""Test that duplicate account names are detected."""
	duplicate_yaml = """
- name: asset
  accounts:
    - name: Cash
    - name: Cash
"""
	tmp_file = Path("/tmp/test_duplicate.yaml")
	tmp_file.write_text(duplicate_yaml)

	with pytest.raises(ValidationError) as exc_info:
		ChartOfAccounts.from_yaml(tmp_file)
	assert "Duplicate account names" in str(exc_info.value)


def test_from_yaml_missing_name():
	"""Test that missing account name raises error."""
	missing_name_yaml = """
- name: asset
  accounts:
    - description: This account has no name
"""
	tmp_file = Path("/tmp/test_missing_name.yaml")
	tmp_file.write_text(missing_name_yaml)

	with pytest.raises(Exception):  # Could be KeyError or ValidationError
		ChartOfAccounts.from_yaml(tmp_file)


def test_from_yaml_description_defaults():
	"""Test that description defaults to empty string when omitted."""
	no_description_yaml = """
- name: asset
  accounts:
    - name: Cash
"""
	tmp_file = Path("/tmp/test_no_description.yaml")
	tmp_file.write_text(no_description_yaml)

	chart = ChartOfAccounts.from_yaml(tmp_file)
	assert chart.get_account("Cash").description == ""


def test_from_yaml_file_not_found():
	"""Test that FileNotFoundError is raised for missing files."""
	with pytest.raises(FileNotFoundError):
		ChartOfAccounts.from_yaml("/tmp/does_not_exist.yaml")


def test_from_yaml_malformed_yaml():
	"""Test that YAML parsing errors are raised."""
	malformed_yaml = """
- name: asset
  accounts:
    - name: Cash
	  invalid indentation here
"""
	tmp_file = Path("/tmp/test_malformed.yaml")
	tmp_file.write_text(malformed_yaml)

	with pytest.raises(yaml.YAMLError):
		ChartOfAccounts.from_yaml(tmp_file)
