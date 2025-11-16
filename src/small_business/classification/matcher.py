"""Pattern matching engine for transaction classification."""

import re

from small_business.classification.models import ClassificationRule, RuleMatch


def match_pattern(description: str, rule: ClassificationRule) -> RuleMatch | None:
	"""Match transaction description against a rule pattern.

	Args:
		description: Transaction description text
		rule: Classification rule to match

	Returns:
		RuleMatch if pattern matches, None otherwise
	"""
	# Case-insensitive matching
	pattern = re.compile(rule.pattern, re.IGNORECASE)
	match = pattern.search(description)

	if match:
		return RuleMatch(
			rule=rule,
			confidence=1.0,  # Exact regex match = 100% confidence
			matched_text=match.group(0),
		)

	return None


def find_best_match(
	description: str,
	rules: list[ClassificationRule],
) -> RuleMatch | None:
	"""Find the best matching rule for a transaction description.

	If multiple rules match, returns the one with highest priority.
	If priorities are equal, returns the first match.

	Args:
		description: Transaction description text
		rules: List of classification rules to try

	Returns:
		Best RuleMatch, or None if no rules match
	"""
	matches = []

	# Find all matching rules
	for rule in rules:
		match = match_pattern(description, rule)
		if match:
			matches.append(match)

	if not matches:
		return None

	# Sort by priority (highest first), then by order in list
	matches.sort(key=lambda m: m.rule.priority, reverse=True)

	return matches[0]
