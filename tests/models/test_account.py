"""Tests for Account and ChartOfAccounts models."""

import pytest
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
