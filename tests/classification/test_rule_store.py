"""Test rule storage."""

from pathlib import Path

from small_business.classification.models import ClassificationRule
from small_business.classification.rule_store import load_rules, save_rules


def test_save_and_load_rules(tmp_path):
	"""Test saving and loading classification rules."""
	rules_file = tmp_path / "rules.yaml"

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS|COLES",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			priority=1,
		),
		ClassificationRule(
			pattern=r"QANTAS|VIRGIN",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
			priority=2,
		),
	]

	# Save rules
	save_rules(rules, rules_file)

	# Verify file exists
	assert rules_file.exists()

	# Load rules
	loaded = load_rules(rules_file)
	assert len(loaded) == 2
	assert loaded[0].pattern == r"WOOLWORTHS|COLES"
	assert loaded[0].account_code == "EXP-GRO"
	assert loaded[1].pattern == r"QANTAS|VIRGIN"
	assert loaded[1].priority == 2


def test_load_rules_nonexistent_file(tmp_path):
	"""Test loading from non-existent file returns empty list."""
	rules_file = tmp_path / "nonexistent.yaml"
	loaded = load_rules(rules_file)
	assert loaded == []


def test_save_rules_creates_directory(tmp_path):
	"""Test saving rules creates parent directory if needed."""
	rules_file = tmp_path / "subdir" / "rules.yaml"

	rules = [
		ClassificationRule(
			pattern=r"TEST",
			account_code="EXP-TEST",
			description="Test",
			gst_inclusive=True,
		)
	]

	save_rules(rules, rules_file)
	assert rules_file.exists()
	assert rules_file.parent.exists()
