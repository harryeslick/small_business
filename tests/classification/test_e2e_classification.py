"""End-to-end integration test for classification system."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from small_business.classification import (
	AcceptanceDecision,
	classify_and_save,
	learn_rule,
	load_and_classify_unclassified,
	load_rules,
	save_rules,
)
from small_business.models.transaction import JournalEntry, Transaction
from small_business.storage import load_transactions, save_transaction


def test_e2e_classification_workflow(tmp_path: Path):
	"""Test complete classification workflow from import to learning."""
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "rules.yaml"

	# Step 1: Import unclassified bank transactions
	transactions = [
		Transaction(
			transaction_id="TXN-001",
			date=date(2025, 11, 15),
			description="WOOLWORTHS 1234 PERTH",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
			],
		),
		Transaction(
			transaction_id="TXN-002",
			date=date(2025, 11, 16),
			description="BUNNINGS WAREHOUSE PERTH",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("125.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("125.00")),
			],
		),
		Transaction(
			transaction_id="TXN-003",
			date=date(2025, 11, 17),
			description="UNKNOWN MERCHANT XYZ",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("50.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
			],
		),
	]

	# Save to storage (simulating bank import)
	for txn in transactions:
		save_transaction(txn, data_dir)

	# Step 2: First classification run with no rules
	rules = load_rules(rules_file)  # Empty initially
	assert rules == []

	results = load_and_classify_unclassified(data_dir, transactions[0].date, rules, rules_file)

	# All should be pending (no rules)
	assert len(results) == 3
	assert all(r.decision == AcceptanceDecision.PENDING for r in results.values())

	# Step 3: User manually classifies first transaction
	txn1 = transactions[0]
	learned_rule1 = learn_rule(txn1, "EXP-GRO", "Groceries", True)

	# Verify pattern extracted correctly
	assert learned_rule1.pattern == r"WOOLWORTHS"
	assert learned_rule1.account_code == "EXP-GRO"

	# Save learned rule
	rules.append(learned_rule1)
	save_rules(rules, rules_file)

	# Apply classification and save
	result1 = classify_and_save(txn1, rules, rules_file, data_dir, auto_accept_threshold=1.0)
	assert result1.decision == AcceptanceDecision.ACCEPTED

	# Step 4: Second classification run with one rule
	rules = load_rules(rules_file)
	assert len(rules) == 1

	# Verify TXN-001 was updated in storage and is no longer unclassified
	stored_txns = load_transactions(data_dir, txn1.date)
	stored_txn1 = next(t for t in stored_txns if t.transaction_id == "TXN-001")
	assert stored_txn1.entries[0].account_code == "EXP-GRO"

	results = load_and_classify_unclassified(data_dir, transactions[0].date, rules, rules_file)

	# TXN-001 not in results (already classified), others still pending
	assert "TXN-001" not in results  # Already classified
	assert len(results) == 2  # Only TXN-002 and TXN-003
	assert results["TXN-002"].decision == AcceptanceDecision.PENDING
	assert results["TXN-003"].decision == AcceptanceDecision.PENDING

	# Step 5: User classifies second transaction
	txn2 = transactions[1]
	learned_rule2 = learn_rule(txn2, "EXP-SUP", "Supplies", True)

	assert learned_rule2.pattern == r"BUNNINGS WAREHOUSE"

	rules.append(learned_rule2)
	save_rules(rules, rules_file)

	result2 = classify_and_save(txn2, rules, rules_file, data_dir, auto_accept_threshold=1.0)
	assert result2.decision == AcceptanceDecision.ACCEPTED

	# Step 6: Third classification run with two rules
	rules = load_rules(rules_file)
	assert len(rules) == 2

	# Verify both transactions updated in storage
	stored_txns = load_transactions(data_dir, txn1.date)
	stored_txn2 = next(t for t in stored_txns if t.transaction_id == "TXN-002")
	assert stored_txn2.entries[0].account_code == "EXP-SUP"

	results = load_and_classify_unclassified(data_dir, transactions[0].date, rules, rules_file)

	# TXN-001 and TXN-002 not in results (already classified), only TXN-003 pending
	assert "TXN-001" not in results
	assert "TXN-002" not in results
	assert len(results) == 1  # Only TXN-003
	assert results["TXN-003"].decision == AcceptanceDecision.PENDING

	# Step 7: Import new transaction matching existing rule
	new_txn = Transaction(
		transaction_id="TXN-004",
		date=date(2025, 11, 18),
		description="WOOLWORTHS 5678 FREMANTLE",  # Should match WOOLWORTHS rule
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("32.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("32.50")),
		],
	)

	save_transaction(new_txn, data_dir)

	# Step 8: Auto-classification of new transaction
	results = load_and_classify_unclassified(data_dir, transactions[0].date, rules, rules_file)

	# Should auto-classify TXN-004 using existing WOOLWORTHS rule
	assert "TXN-004" in results
	assert results["TXN-004"].decision == AcceptanceDecision.ACCEPTED
	assert results["TXN-004"].match.rule.account_code == "EXP-GRO"

	# Verify auto-classification saved to storage
	stored_txns = load_transactions(data_dir, new_txn.date)
	stored_new_txn = next(t for t in stored_txns if t.transaction_id == "TXN-004")
	assert stored_new_txn.entries[0].account_code == "EXP-GRO"

	# Step 9: Verify final state
	# Only unclassified transaction should be in results
	final_results = load_and_classify_unclassified(data_dir, transactions[0].date, rules, rules_file)

	# Only TXN-003 is unclassified, so should only have 1 result
	assert len(final_results) == 1
	assert "TXN-003" in final_results
	assert final_results["TXN-003"].decision == AcceptanceDecision.PENDING

	# Verify all other transactions are classified in storage
	all_stored_txns = load_transactions(data_dir, transactions[0].date)
	assert len(all_stored_txns) == 4  # All 4 transactions

	classified_txns = [
		t
		for t in all_stored_txns
		if not any("UNCLASSIFIED" in e.account_code for e in t.entries)
	]
	assert len(classified_txns) == 3  # TXN-001, TXN-002, TXN-004

	# Verify rules file persisted correctly
	reloaded_rules = load_rules(rules_file)
	assert len(reloaded_rules) == 2
	assert any(r.pattern == r"WOOLWORTHS" for r in reloaded_rules)
	assert any(r.pattern == r"BUNNINGS WAREHOUSE" for r in reloaded_rules)
