"""Test pattern matching engine."""

from small_business.classification.matcher import find_best_match, match_pattern
from small_business.classification.models import ClassificationRule


def test_match_pattern_success():
	"""Test successful pattern match."""
	rule = ClassificationRule(
		pattern=r"WOOLWORTHS|COLES",
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	match = match_pattern("WOOLWORTHS 1234 PERTH", rule)
	assert match is not None
	assert match.rule.account_code == "EXP-GRO"
	assert match.confidence == 1.0
	assert "WOOLWORTHS" in match.matched_text


def test_match_pattern_case_insensitive():
	"""Test pattern matching is case-insensitive."""
	rule = ClassificationRule(
		pattern=r"QANTAS",
		account_code="EXP-TRV-FLT",
		description="Flight",
		gst_inclusive=True,
	)

	match = match_pattern("qantas flight booking", rule)
	assert match is not None
	assert match.confidence == 1.0


def test_match_pattern_no_match():
	"""Test pattern that doesn't match returns None."""
	rule = ClassificationRule(
		pattern=r"WOOLWORTHS",
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	match = match_pattern("ALDI SUPERMARKET", rule)
	assert match is None


def test_find_best_match_single_rule():
	"""Test finding best match with single matching rule."""
	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			priority=1,
		),
		ClassificationRule(
			pattern=r"QANTAS",
			account_code="EXP-TRV-FLT",
			description="Flight",
			gst_inclusive=True,
			priority=1,
		),
	]

	match = find_best_match("WOOLWORTHS 1234", rules)
	assert match is not None
	assert match.rule.account_code == "EXP-GRO"


def test_find_best_match_priority():
	"""Test finding best match uses priority for conflicts."""
	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			priority=1,
		),
		ClassificationRule(
			pattern=r"WOOL",  # Also matches "WOOLWORTHS"
			account_code="EXP-OTHER",
			description="Other",
			gst_inclusive=True,
			priority=2,  # Higher priority
		),
	]

	match = find_best_match("WOOLWORTHS 1234", rules)
	assert match is not None
	assert match.rule.account_code == "EXP-OTHER"  # Higher priority wins
	assert match.rule.priority == 2


def test_find_best_match_no_match():
	"""Test finding best match with no matching rules."""
	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
	]

	match = find_best_match("ALDI SUPERMARKET", rules)
	assert match is None
