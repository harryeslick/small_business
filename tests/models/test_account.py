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
		code="EXP-TRV",
		name="Travel",
		account_type=AccountType.EXPENSE,
		description="Travel expenses",
	)
	assert account.code == "EXP-TRV"
	assert account.name == "Travel"
	assert account.account_type == AccountType.EXPENSE
	assert account.parent_code is None


def test_account_with_parent():
	"""Test creating a child account."""
	account = Account(
		code="EXP-TRV-FLT",
		name="Flights",
		account_type=AccountType.EXPENSE,
		parent_code="EXP-TRV",
	)
	assert account.parent_code == "EXP-TRV"


def test_chart_of_accounts_creation():
	"""Test creating a chart of accounts."""
	chart = ChartOfAccounts(
		accounts=[
			Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
			Account(
				code="EXP-TRV",
				name="Travel",
				account_type=AccountType.EXPENSE,
				parent_code="EXP",
			),
			Account(code="INC", name="Income", account_type=AccountType.INCOME),
		]
	)
	assert len(chart.accounts) == 3


def test_chart_get_account():
	"""Test retrieving account by code."""
	chart = ChartOfAccounts(
		accounts=[
			Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
			Account(code="INC", name="Income", account_type=AccountType.INCOME),
		]
	)
	account = chart.get_account("EXP")
	assert account.name == "Expenses"


def test_chart_get_account_not_found():
	"""Test getting account that doesn't exist."""
	chart = ChartOfAccounts(
		accounts=[Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE)]
	)
	with pytest.raises(KeyError):
		chart.get_account("NOTFOUND")


def test_chart_get_children():
	"""Test getting child accounts."""
	chart = ChartOfAccounts(
		accounts=[
			Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
			Account(
				code="EXP-TRV",
				name="Travel",
				account_type=AccountType.EXPENSE,
				parent_code="EXP",
			),
			Account(
				code="EXP-MAT",
				name="Materials",
				account_type=AccountType.EXPENSE,
				parent_code="EXP",
			),
		]
	)
	children = chart.get_children("EXP")
	assert len(children) == 2
	assert {c.code for c in children} == {"EXP-TRV", "EXP-MAT"}


def test_chart_get_root_accounts():
	"""Test getting top-level accounts."""
	chart = ChartOfAccounts(
		accounts=[
			Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
			Account(
				code="EXP-TRV",
				name="Travel",
				account_type=AccountType.EXPENSE,
				parent_code="EXP",
			),
			Account(code="INC", name="Income", account_type=AccountType.INCOME),
		]
	)
	roots = chart.get_root_accounts()
	assert len(roots) == 2
	assert {r.code for r in roots} == {"EXP", "INC"}


def test_chart_validates_parent_exists():
	"""Test that chart validates parent account exists."""
	with pytest.raises(ValidationError) as exc_info:
		ChartOfAccounts(
			accounts=[
				Account(
					code="EXP-TRV",
					name="Travel",
					account_type=AccountType.EXPENSE,
					parent_code="NOTEXIST",
				)
			]
		)
	assert "Parent" in str(exc_info.value)


def test_chart_validates_max_two_levels():
	"""Test that chart enforces max 2-level hierarchy."""
	with pytest.raises(ValidationError) as exc_info:
		ChartOfAccounts(
			accounts=[
				Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
				Account(
					code="EXP-TRV",
					name="Travel",
					account_type=AccountType.EXPENSE,
					parent_code="EXP",
				),
				Account(
					code="EXP-TRV-FLT",
					name="Flights",
					account_type=AccountType.EXPENSE,
					parent_code="EXP-TRV",
				),
			]
		)
	assert "2-level" in str(exc_info.value)


def test_chart_save(tmp_path):
	"""Test saving chart of accounts to YAML with nested structure."""
	chart = ChartOfAccounts(
		accounts=[
			Account(code="EXP", name="Expenses", account_type=AccountType.EXPENSE),
			Account(
				code="EXP-TRV",
				name="Travel",
				account_type=AccountType.EXPENSE,
				parent_code="EXP",
				description="Travel expenses",
			),
			Account(code="INC", name="Income", account_type=AccountType.INCOME),
		]
	)

	file_path = tmp_path / "chart_of_accounts.yaml"
	chart.save(file_path)

	# Verify file was created
	assert file_path.exists()

	# Verify YAML content has nested structure
	with open(file_path) as f:
		data = yaml.safe_load(f)

	# Should only have root accounts at top level
	assert len(data) == 2  # EXP and INC

	# Find EXP account
	exp_account = next(acc for acc in data if acc["code"] == "EXP")
	assert exp_account["name"] == "Expenses"
	assert exp_account["account_type"] == "expense"  # Root has account_type
	assert "sub_accounts" in exp_account
	assert len(exp_account["sub_accounts"]) == 1
	assert exp_account["sub_accounts"][0]["code"] == "EXP-TRV"
	assert exp_account["sub_accounts"][0]["description"] == "Travel expenses"
	assert "account_type" not in exp_account["sub_accounts"][0]  # Child doesn't have account_type

	# Find INC account
	inc_account = next(acc for acc in data if acc["code"] == "INC")
	assert inc_account["name"] == "Income"
	assert "sub_accounts" not in inc_account or len(inc_account.get("sub_accounts", [])) == 0


def test_chart_load(tmp_path):
	"""Test loading chart of accounts from YAML with account_type inherited from parent."""
	yaml_content = """
- code: EXP
  name: Expenses
  account_type: expense
  description: ""
  sub_accounts:
    - code: EXP-TRV
      name: Travel
      description: Travel expenses
- code: INC
  name: Income
  account_type: income
  description: ""
"""

	file_path = tmp_path / "chart_of_accounts.yaml"
	file_path.write_text(yaml_content)

	chart = ChartOfAccounts.load(file_path)

	assert len(chart.accounts) == 3
	assert chart.get_account("EXP").name == "Expenses"
	assert chart.get_account("EXP").account_type == AccountType.EXPENSE
	assert chart.get_account("EXP-TRV").parent_code == "EXP"
	assert chart.get_account("EXP-TRV").account_type == AccountType.EXPENSE  # Inherited
	assert chart.get_account("INC").account_type == AccountType.INCOME


def test_chart_load_file_not_found():
	"""Test loading from non-existent file raises error."""
	with pytest.raises(FileNotFoundError):
		ChartOfAccounts.load(Path("/nonexistent/file.yaml"))
