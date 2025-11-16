"""Learn classification rules from user input."""

import re

from small_business.classification.models import ClassificationRule
from small_business.models.transaction import Transaction


def learn_rule(
	transaction: Transaction,
	account_code: str,
	description: str,
	gst_inclusive: bool,
	priority: int = 0,
) -> ClassificationRule:
	"""Learn a classification rule from a user-classified transaction.

	Extracts a pattern from the transaction description by identifying
	the merchant name (first sequence of alphabetic words before numbers).

	Args:
		transaction: Transaction that was manually classified
		account_code: Account code chosen by user
		description: Human-readable description for the rule
		gst_inclusive: Whether GST is included in amounts
		priority: Rule priority (default 0)

	Returns:
		ClassificationRule extracted from the transaction
	"""
	# Extract merchant pattern from description
	# Strategy: Take first continuous sequence of words (letters/spaces only)
	# Remove trailing numbers and locations
	pattern = _extract_merchant_pattern(transaction.description)

	return ClassificationRule(
		pattern=pattern,
		account_code=account_code,
		description=description,
		gst_inclusive=gst_inclusive,
		priority=priority,
	)


def _extract_merchant_pattern(description: str) -> str:
	"""Extract merchant name pattern from transaction description.

	Removes numbers, location names, and extra whitespace.
	Returns the first sequence of words (alphabetic characters).

	Args:
		description: Transaction description

	Returns:
		Regex pattern for the merchant name
	"""
	# Find all sequences of alphabetic characters (words)
	words = re.findall(r"[A-Z]+", description.upper())

	if not words:
		# Fallback: use first word if no alphabetic sequences found
		return description.strip().split()[0]

	# Take first 1-2 words that form the merchant name
	# Strategy: Take consecutive words until we hit a likely location
	merchant_words = []
	# Common locations to stop at (not descriptors like WAREHOUSE which may be part of brand)
	stop_words = {
		"PERTH", "SYDNEY", "MELBOURNE", "BRISBANE", "ADELAIDE",
		"STORE", "BRANCH", "PTY", "LTD",
	}

	for word in words:
		# Stop at common location words
		if word in stop_words:
			break

		# For first word, always add it
		if not merchant_words:
			merchant_words.append(word)
			continue

		# For second word, only add if it looks like part of brand name
		# (WAREHOUSE, etc.) not generic descriptor (SUPERMARKET after a complete brand)
		if len(merchant_words) == 1:
			# Add second word if it's a brand component (WAREHOUSE, etc)
			# Skip if it's after a well-known single-word merchant
			known_single_merchants = {"COLES", "WOOLWORTHS", "ALDI", "IGA"}
			if merchant_words[0] in known_single_merchants:
				break
			merchant_words.append(word)
			break

	if not merchant_words:
		merchant_words = [words[0]]

	return r" ".join(merchant_words)
