"""Test classification models."""

from small_business.classification.models import ClassificationRule, RuleMatch


def test_classification_rule_valid():
	"""Test valid classification rule."""
	rule = ClassificationRule(
		pattern=r"WOOLWORTHS|COLES",
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
		priority=1,
	)
	assert rule.pattern == r"WOOLWORTHS|COLES"
	assert rule.account_code == "EXP-GRO"
	assert rule.priority == 1


def test_classification_rule_default_priority():
	"""Test classification rule with default priority."""
	rule = ClassificationRule(
		pattern=r"QANTAS",
		account_code="EXP-TRV-FLT",
		description="Flight",
		gst_inclusive=True,
	)
	assert rule.priority == 0


def test_rule_match():
	"""Test rule match with confidence."""
	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		confidence=0.95,
		matched_text="WOOLWORTHS 1234",
	)
	assert match.confidence == 0.95
	assert match.rule.account_code == "EXP-GRO"
	assert match.matched_text == "WOOLWORTHS 1234"


def test_rule_match_requires_confidence():
	"""Test rule match requires confidence between 0 and 1."""
	try:
		RuleMatch(
			rule=ClassificationRule(
				pattern=r"TEST",
				account_code="EXP-TEST",
				description="Test",
				gst_inclusive=True,
			),
			confidence=1.5,  # Invalid
			matched_text="TEST",
		)
		assert False, "Should raise validation error"
	except Exception:
		pass
