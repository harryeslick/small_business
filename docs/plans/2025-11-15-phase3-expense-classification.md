# Phase 3: Expense Classification System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build transaction classification engine with regex-based rules, user acceptance workflow, and automated rule learning.

**Architecture:** Implement YAML-based classification rules with pattern matching on transaction descriptions, track classification confidence scores, build user acceptance workflow for updating transactions with approved classifications, and implement rule learning from user-accepted classifications.

**Tech Stack:** Python 3.13+, Pydantic (data models), PyYAML (rule storage), regex (pattern matching)

---

## Task 1: Classification Rule Models

**Files:**
- Create: `src/small_business/classification/__init__.py`
- Create: `src/small_business/classification/models.py`
- Test: `tests/classification/test_models.py`

**Step 1: Write the failing test**

Create `tests/classification/test_models.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_models.py::test_classification_rule_valid -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.classification'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .models import ClassificationRule, RuleMatch

__all__ = ["ClassificationRule", "RuleMatch"]
```

Create `src/small_business/classification/models.py`:

```python
"""Classification rule models."""

from pydantic import BaseModel, Field


class ClassificationRule(BaseModel):
	"""Rule for classifying transactions based on description pattern."""

	pattern: str = Field(min_length=1, description="Regex pattern to match transaction description")
	account_code: str = Field(min_length=1, description="Account code to assign")
	description: str = Field(min_length=1, description="Human-readable description of rule")
	gst_inclusive: bool = Field(description="Whether transactions are GST inclusive")
	priority: int = Field(default=0, ge=0, description="Priority for conflicting rules (higher = higher priority)")


class RuleMatch(BaseModel):
	"""Result of matching a rule against a transaction."""

	rule: ClassificationRule
	confidence: float = Field(ge=0.0, le=1.0, description="Match confidence score (0-1)")
	matched_text: str = Field(description="The text that matched the pattern")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_models.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/ tests/classification/
git commit -m "feat: add classification rule models

Add ClassificationRule and RuleMatch Pydantic models for
transaction classification with regex patterns, confidence
scoring, and priority handling.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Rule Storage (YAML)

**Files:**
- Create: `src/small_business/classification/rule_store.py`
- Test: `tests/classification/test_rule_store.py`

**Step 1: Write the failing test**

Create `tests/classification/test_rule_store.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_rule_store.py::test_save_and_load_rules -v`

Expected: FAIL with "ImportError: cannot import name 'load_rules'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/rule_store.py`:

```python
"""Rule storage using YAML format."""

from pathlib import Path

import yaml

from small_business.classification.models import ClassificationRule


def save_rules(rules: list[ClassificationRule], rules_file: Path) -> None:
	"""Save classification rules to YAML file.

	Args:
		rules: List of classification rules
		rules_file: Path to YAML file
	"""
	# Create parent directory if needed
	rules_file.parent.mkdir(parents=True, exist_ok=True)

	# Convert to dict format for YAML
	rules_data = {"rules": [rule.model_dump() for rule in rules]}

	# Write YAML
	with open(rules_file, "w") as f:
		yaml.dump(rules_data, f, default_flow_style=False, sort_keys=False)


def load_rules(rules_file: Path) -> list[ClassificationRule]:
	"""Load classification rules from YAML file.

	Args:
		rules_file: Path to YAML file

	Returns:
		List of classification rules (empty if file doesn't exist)
	"""
	if not rules_file.exists():
		return []

	with open(rules_file) as f:
		data = yaml.safe_load(f)

	if not data or "rules" not in data:
		return []

	rules = []
	for rule_data in data["rules"]:
		rule = ClassificationRule.model_validate(rule_data)
		rules.append(rule)

	return rules
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules

__all__ = ["ClassificationRule", "RuleMatch", "load_rules", "save_rules"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_rule_store.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/rule_store.py tests/classification/test_rule_store.py src/small_business/classification/__init__.py
git commit -m "feat: add YAML rule storage

Implement save_rules() and load_rules() for persisting
classification rules in YAML format with automatic directory
creation.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Pattern Matcher Engine

**Files:**
- Create: `src/small_business/classification/matcher.py`
- Test: `tests/classification/test_matcher.py`

**Step 1: Write the failing test**

Create `tests/classification/test_matcher.py`:

```python
"""Test pattern matching engine."""

import re

from small_business.classification.matcher import match_pattern, find_best_match
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_matcher.py::test_match_pattern_success -v`

Expected: FAIL with "ImportError: cannot import name 'match_pattern'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/matcher.py`:

```python
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
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_matcher.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/matcher.py tests/classification/test_matcher.py src/small_business/classification/__init__.py
git commit -m "feat: add pattern matching engine

Implement case-insensitive regex pattern matching with
priority-based conflict resolution. Returns best matching
rule with 100% confidence for regex matches.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Transaction Classifier

**Files:**
- Create: `src/small_business/classification/classifier.py`
- Test: `tests/classification/test_classifier.py`

**Step 1: Write the failing test**

Create `tests/classification/test_classifier.py`:

```python
"""Test transaction classifier."""

from datetime import date
from decimal import Decimal

from small_business.classification.classifier import classify_transaction, classify_batch
from small_business.classification.models import ClassificationRule
from small_business.models.transaction import JournalEntry, Transaction


def test_classify_transaction_match():
	"""Test classifying transaction with matching rule."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234 PERTH",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS|COLES",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	match = classify_transaction(txn, rules)
	assert match is not None
	assert match.rule.account_code == "EXP-GRO"
	assert match.confidence == 1.0


def test_classify_transaction_no_match():
	"""Test classifying transaction with no matching rule."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="UNKNOWN MERCHANT",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	match = classify_transaction(txn, rules)
	assert match is None


def test_classify_batch():
	"""Test classifying batch of transactions."""
	transactions = [
		Transaction(
			transaction_id="TXN-001",
			date=date(2025, 11, 15),
			description="WOOLWORTHS 1234",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
			],
		),
		Transaction(
			transaction_id="TXN-002",
			date=date(2025, 11, 16),
			description="QANTAS FLIGHT",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("280.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("280.00")),
			],
		),
		Transaction(
			transaction_id="TXN-003",
			date=date(2025, 11, 17),
			description="UNKNOWN MERCHANT",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("50.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
			],
		),
	]

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		ClassificationRule(
			pattern=r"QANTAS",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
		),
	]

	results = classify_batch(transactions, rules)

	assert len(results) == 3
	assert results["TXN-001"] is not None
	assert results["TXN-001"].rule.account_code == "EXP-GRO"
	assert results["TXN-002"] is not None
	assert results["TXN-002"].rule.account_code == "EXP-TRV-FLT"
	assert results["TXN-003"] is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_classifier.py::test_classify_transaction_match -v`

Expected: FAIL with "ImportError: cannot import name 'classify_transaction'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/classifier.py`:

```python
"""Transaction classification logic."""

from small_business.classification.matcher import find_best_match
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.models.transaction import Transaction


def classify_transaction(
	transaction: Transaction,
	rules: list[ClassificationRule],
) -> RuleMatch | None:
	"""Classify a transaction using classification rules.

	Args:
		transaction: Transaction to classify
		rules: List of classification rules

	Returns:
		RuleMatch if a rule matches, None otherwise
	"""
	return find_best_match(transaction.description, rules)


def classify_batch(
	transactions: list[Transaction],
	rules: list[ClassificationRule],
) -> dict[str, RuleMatch | None]:
	"""Classify a batch of transactions.

	Args:
		transactions: List of transactions to classify
		rules: List of classification rules

	Returns:
		Dictionary mapping transaction_id to RuleMatch (or None if no match)
	"""
	results = {}

	for txn in transactions:
		match = classify_transaction(txn, rules)
		results[txn.transaction_id] = match

	return results
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .classifier import classify_batch, classify_transaction
from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
	"classify_transaction",
	"classify_batch",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_classifier.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/classifier.py tests/classification/test_classifier.py src/small_business/classification/__init__.py
git commit -m "feat: add transaction classifier

Implement classify_transaction() and classify_batch() for
matching transactions against classification rules. Returns
RuleMatch or None for each transaction.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Classification Application (Update Transactions)

**Files:**
- Create: `src/small_business/classification/applicator.py`
- Test: `tests/classification/test_applicator.py`

**Step 1: Write the failing test**

Create `tests/classification/test_applicator.py`:

```python
"""Test classification applicator."""

from datetime import date
from decimal import Decimal

from small_business.classification.applicator import apply_classification
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.models.transaction import JournalEntry, Transaction


def test_apply_classification_expense():
	"""Test applying classification to expense transaction."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="WOOLWORTHS",
	)

	updated = apply_classification(txn, match)

	# Check account code was updated
	assert len(updated.entries) == 2
	expense_entry = next(e for e in updated.entries if e.debit > 0)
	assert expense_entry.account_code == "EXP-GRO"

	# Bank entry should remain unchanged
	bank_entry = next(e for e in updated.entries if e.credit > 0)
	assert bank_entry.account_code == "BANK-CHQ"


def test_apply_classification_income():
	"""Test applying classification to income transaction."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-UNCLASSIFIED", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"PAYMENT",
			account_code="INC-SALES",
			description="Sales",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="PAYMENT",
	)

	updated = apply_classification(txn, match)

	# Check account code was updated
	income_entry = next(e for e in updated.entries if e.credit > 0)
	assert income_entry.account_code == "INC-SALES"

	# Bank entry should remain unchanged
	bank_entry = next(e for e in updated.entries if e.debit > 0)
	assert bank_entry.account_code == "BANK-CHQ"


def test_apply_classification_preserves_original():
	"""Test applying classification creates new transaction (doesn't modify original)."""
	original = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="WOOLWORTHS",
	)

	updated = apply_classification(original, match)

	# Original should be unchanged
	assert original.entries[0].account_code == "EXP-UNCLASSIFIED"

	# Updated should have new account code
	assert updated.entries[0].account_code == "EXP-GRO"

	# Should be different objects
	assert original is not updated
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_applicator.py::test_apply_classification_expense -v`

Expected: FAIL with "ImportError: cannot import name 'apply_classification'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/applicator.py`:

```python
"""Apply classification to transactions."""

from small_business.classification.models import RuleMatch
from small_business.models.transaction import Transaction


def apply_classification(
	transaction: Transaction,
	match: RuleMatch,
) -> Transaction:
	"""Apply classification to a transaction by updating account codes.

	Creates a new Transaction with updated account codes based on the matched rule.
	The original transaction is not modified.

	For expenses (debit entries with UNCLASSIFIED), updates the expense account.
	For income (credit entries with UNCLASSIFIED), updates the income account.
	Bank account entries are never modified.

	Args:
		transaction: Original transaction
		match: Matched classification rule

	Returns:
		New Transaction with updated account codes
	"""
	# Create a deep copy of the transaction
	updated_data = transaction.model_dump()

	# Update account codes in entries
	for entry in updated_data["entries"]:
		# Check if this is an unclassified entry
		if "UNCLASSIFIED" in entry["account_code"]:
			# Replace with the matched rule's account code
			entry["account_code"] = match.rule.account_code

	# Create new transaction from updated data
	return Transaction.model_validate(updated_data)
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .applicator import apply_classification
from .classifier import classify_batch, classify_transaction
from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
	"classify_transaction",
	"classify_batch",
	"apply_classification",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_applicator.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/applicator.py tests/classification/test_applicator.py src/small_business/classification/__init__.py
git commit -m "feat: add classification applicator

Implement apply_classification() to update transaction account
codes based on matched rules. Creates new transaction without
modifying original.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Rule Learning System

**Files:**
- Create: `src/small_business/classification/learning.py`
- Test: `tests/classification/test_learning.py`

**Step 1: Write the failing test**

Create `tests/classification/test_learning.py`:

```python
"""Test rule learning system."""

from small_business.classification.learning import (
	extract_pattern_from_description,
	create_learned_rule,
	should_learn_rule,
)
from small_business.classification.models import ClassificationRule


def test_extract_pattern_from_description():
	"""Test extracting pattern from transaction description."""
	# Should extract the merchant name (first significant word/phrase)
	pattern = extract_pattern_from_description("WOOLWORTHS 1234 PERTH AUS")
	assert pattern == "WOOLWORTHS"

	pattern = extract_pattern_from_description("QANTAS AIRWAYS FLIGHT 123")
	assert pattern == "QANTAS"

	pattern = extract_pattern_from_description("BP SERVICE STATION")
	assert pattern == "BP"


def test_create_learned_rule():
	"""Test creating a rule from user classification."""
	rule = create_learned_rule(
		description="WOOLWORTHS 1234 PERTH",
		account_code="EXP-GRO",
		rule_description="Groceries",
		gst_inclusive=True,
	)

	assert rule.pattern == "WOOLWORTHS"
	assert rule.account_code == "EXP-GRO"
	assert rule.description == "Groceries"
	assert rule.gst_inclusive is True
	assert rule.priority == 0  # Default priority for learned rules


def test_should_learn_rule_new_pattern():
	"""Test should learn rule when pattern doesn't exist."""
	existing_rules = [
		ClassificationRule(
			pattern=r"QANTAS",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
		)
	]

	new_rule = ClassificationRule(
		pattern=r"WOOLWORTHS",
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	assert should_learn_rule(new_rule, existing_rules) is True


def test_should_learn_rule_duplicate_pattern():
	"""Test should not learn rule when pattern already exists."""
	existing_rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	new_rule = ClassificationRule(
		pattern=r"WOOLWORTHS",
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	assert should_learn_rule(new_rule, existing_rules) is False


def test_should_learn_rule_same_pattern_different_account():
	"""Test should learn rule when pattern exists but with different account."""
	existing_rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	new_rule = ClassificationRule(
		pattern=r"WOOLWORTHS",
		account_code="EXP-OTHER",  # Different account
		description="Other",
		gst_inclusive=True,
	)

	# Should still learn (user might want to override later)
	assert should_learn_rule(new_rule, existing_rules) is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_learning.py::test_extract_pattern_from_description -v`

Expected: FAIL with "ImportError: cannot import name 'extract_pattern_from_description'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/learning.py`:

```python
"""Rule learning from user classifications."""

import re

from small_business.classification.models import ClassificationRule


def extract_pattern_from_description(description: str) -> str:
	"""Extract a pattern from transaction description.

	Extracts the first significant word (typically the merchant name).
	Removes numbers, special characters, and common trailing text.

	Args:
		description: Transaction description

	Returns:
		Extracted pattern (single word/merchant name)
	"""
	# Remove common trailing information
	text = description.upper()

	# Split on whitespace and special characters
	parts = re.split(r"[\s\-_/]+", text)

	# Find first significant part (non-numeric, length > 2)
	for part in parts:
		# Remove special characters
		cleaned = re.sub(r"[^A-Z0-9]", "", part)
		# Check if it's a meaningful word (not just numbers)
		if cleaned and len(cleaned) > 2 and not cleaned.isdigit():
			return cleaned

	# Fallback: return first part if nothing found
	return parts[0] if parts else description


def create_learned_rule(
	description: str,
	account_code: str,
	rule_description: str,
	gst_inclusive: bool,
) -> ClassificationRule:
	"""Create a new classification rule from user classification.

	Args:
		description: Transaction description to learn from
		account_code: Account code assigned by user
		rule_description: Human-readable description for the rule
		gst_inclusive: Whether transaction is GST inclusive

	Returns:
		New ClassificationRule
	"""
	pattern = extract_pattern_from_description(description)

	return ClassificationRule(
		pattern=pattern,
		account_code=account_code,
		description=rule_description,
		gst_inclusive=gst_inclusive,
		priority=0,  # Default priority for learned rules
	)


def should_learn_rule(
	new_rule: ClassificationRule,
	existing_rules: list[ClassificationRule],
) -> bool:
	"""Determine if a new rule should be learned.

	A rule should be learned if:
	- The exact pattern + account combination doesn't already exist

	Args:
		new_rule: Proposed new rule
		existing_rules: Existing classification rules

	Returns:
		True if rule should be added
	"""
	for existing in existing_rules:
		# Check if same pattern and same account code
		if existing.pattern == new_rule.pattern and existing.account_code == new_rule.account_code:
			return False

	return True
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .applicator import apply_classification
from .classifier import classify_batch, classify_transaction
from .learning import create_learned_rule, extract_pattern_from_description, should_learn_rule
from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
	"classify_transaction",
	"classify_batch",
	"apply_classification",
	"extract_pattern_from_description",
	"create_learned_rule",
	"should_learn_rule",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_learning.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/learning.py tests/classification/test_learning.py src/small_business/classification/__init__.py
git commit -m "feat: add rule learning system

Implement pattern extraction from descriptions and automated
rule creation from user classifications. Includes duplicate
detection to avoid redundant rules.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Classification Workflow Orchestrator

**Files:**
- Create: `src/small_business/classification/workflow.py`
- Test: `tests/classification/test_workflow.py`

**Step 1: Write the failing test**

Create `tests/classification/test_workflow.py`:

```python
"""Test classification workflow."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.classification.workflow import (
	classify_and_update_transactions,
	AcceptedClassification,
)
from small_business.classification.models import ClassificationRule
from small_business.models.transaction import JournalEntry, Transaction
from small_business.classification.rule_store import load_rules


def test_classify_and_update_transactions(tmp_path):
	"""Test complete classification workflow with user acceptance."""
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "rules.yaml"

	# Initial rules
	initial_rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# Transactions to classify
	transactions = [
		Transaction(
			transaction_id="TXN-001",
			date=date(2025, 11, 15),
			description="WOOLWORTHS 1234",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
			],
		),
		Transaction(
			transaction_id="TXN-002",
			date=date(2025, 11, 16),
			description="QANTAS FLIGHT 789",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("280.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("280.00")),
			],
		),
	]

	# User accepts first classification (auto-matched)
	# User manually classifies second (no rule match)
	accepted_classifications = [
		AcceptedClassification(
			transaction_id="TXN-001",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			learn_rule=False,  # Already has matching rule
		),
		AcceptedClassification(
			transaction_id="TXN-002",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
			learn_rule=True,  # Learn new rule for QANTAS
		),
	]

	# Run workflow
	result = classify_and_update_transactions(
		transactions=transactions,
		initial_rules=initial_rules,
		accepted_classifications=accepted_classifications,
		rules_file=rules_file,
	)

	# Check updated transactions
	assert len(result.updated_transactions) == 2
	assert result.updated_transactions[0].entries[0].account_code == "EXP-GRO"
	assert result.updated_transactions[1].entries[0].account_code == "EXP-TRV-FLT"

	# Check learned rules were saved
	saved_rules = load_rules(rules_file)
	assert len(saved_rules) == 2  # Original + learned
	assert any(r.pattern == "QANTAS" for r in saved_rules)

	# Check statistics
	assert result.stats["total"] == 2
	assert result.stats["classified"] == 2
	assert result.stats["rules_learned"] == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_workflow.py::test_classify_and_update_transactions -v`

Expected: FAIL with "ImportError: cannot import name 'classify_and_update_transactions'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/workflow.py`:

```python
"""Classification workflow orchestration."""

from pathlib import Path

from pydantic import BaseModel

from small_business.classification.applicator import apply_classification
from small_business.classification.classifier import classify_transaction
from small_business.classification.learning import create_learned_rule, should_learn_rule
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.classification.rule_store import save_rules
from small_business.models.transaction import Transaction


class AcceptedClassification(BaseModel):
	"""User-accepted classification for a transaction."""

	transaction_id: str
	account_code: str
	description: str
	gst_inclusive: bool
	learn_rule: bool = True  # Whether to learn a rule from this classification


class ClassificationResult(BaseModel):
	"""Result of classification workflow."""

	updated_transactions: list[Transaction]
	stats: dict[str, int]


def classify_and_update_transactions(
	transactions: list[Transaction],
	initial_rules: list[ClassificationRule],
	accepted_classifications: list[AcceptedClassification],
	rules_file: Path,
) -> ClassificationResult:
	"""Complete classification workflow with user acceptance and rule learning.

	Workflow:
	1. Classify transactions using initial rules
	2. Apply user-accepted classifications
	3. Learn new rules from accepted classifications
	4. Save updated rules

	Args:
		transactions: Transactions to classify
		initial_rules: Existing classification rules
		accepted_classifications: User-accepted classifications
		rules_file: Path to save learned rules

	Returns:
		ClassificationResult with updated transactions and statistics
	"""
	# Create lookup for accepted classifications
	accepted_by_id = {ac.transaction_id: ac for ac in accepted_classifications}

	updated_transactions = []
	rules_to_learn = []

	for txn in transactions:
		accepted = accepted_by_id.get(txn.transaction_id)

		if accepted:
			# Create a RuleMatch from the accepted classification
			rule = ClassificationRule(
				pattern="",  # Not used for application
				account_code=accepted.account_code,
				description=accepted.description,
				gst_inclusive=accepted.gst_inclusive,
			)

			match = RuleMatch(
				rule=rule,
				confidence=1.0,
				matched_text="",
			)

			# Apply classification
			updated_txn = apply_classification(txn, match)
			updated_transactions.append(updated_txn)

			# Learn rule if requested
			if accepted.learn_rule:
				learned_rule = create_learned_rule(
					description=txn.description,
					account_code=accepted.account_code,
					rule_description=accepted.description,
					gst_inclusive=accepted.gst_inclusive,
				)
				rules_to_learn.append(learned_rule)
		else:
			# No accepted classification, keep original
			updated_transactions.append(txn)

	# Add learned rules to initial rules
	all_rules = list(initial_rules)
	for learned_rule in rules_to_learn:
		if should_learn_rule(learned_rule, all_rules):
			all_rules.append(learned_rule)

	# Save updated rules
	save_rules(all_rules, rules_file)

	# Calculate statistics
	stats = {
		"total": len(transactions),
		"classified": len([t for t in updated_transactions if "UNCLASSIFIED" not in str(t.entries[0].account_code)]),
		"rules_learned": len([r for r in rules_to_learn if should_learn_rule(r, initial_rules)]),
	}

	return ClassificationResult(
		updated_transactions=updated_transactions,
		stats=stats,
	)
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .applicator import apply_classification
from .classifier import classify_batch, classify_transaction
from .learning import create_learned_rule, extract_pattern_from_description, should_learn_rule
from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules
from .workflow import AcceptedClassification, ClassificationResult, classify_and_update_transactions

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
	"classify_transaction",
	"classify_batch",
	"apply_classification",
	"extract_pattern_from_description",
	"create_learned_rule",
	"should_learn_rule",
	"AcceptedClassification",
	"ClassificationResult",
	"classify_and_update_transactions",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_workflow.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/workflow.py tests/classification/test_workflow.py src/small_business/classification/__init__.py
git commit -m "feat: add classification workflow orchestrator

Implement complete workflow for classification with user
acceptance, rule learning, and statistics. Handles both
auto-matched and manually classified transactions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Integration with Storage

**Files:**
- Create: `src/small_business/classification/integration.py`
- Test: `tests/classification/test_integration.py`

**Step 1: Write the failing test**

Create `tests/classification/test_integration.py`:

```python
"""Test classification integration with storage."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.classification.integration import (
	load_unclassified_transactions,
	save_classified_transactions,
)
from small_business.models.transaction import JournalEntry, Transaction
from small_business.storage.transaction_store import save_transaction, load_transactions


def test_load_unclassified_transactions(tmp_path):
	"""Test loading only unclassified transactions."""
	data_dir = tmp_path / "data"

	# Save some transactions (mixed classified and unclassified)
	transactions = [
		Transaction(
			transaction_id="TXN-001",
			date=date(2025, 11, 15),
			description="WOOLWORTHS 1234",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
			],
		),
		Transaction(
			transaction_id="TXN-002",
			date=date(2025, 11, 16),
			description="QANTAS FLIGHT",
			entries=[
				JournalEntry(account_code="EXP-TRV-FLT", debit=Decimal("280.00"), credit=Decimal("0")),  # Already classified
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("280.00")),
			],
		),
		Transaction(
			transaction_id="TXN-003",
			date=date(2025, 11, 17),
			description="UNKNOWN",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("50.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
			],
		),
	]

	for txn in transactions:
		save_transaction(txn, data_dir)

	# Load only unclassified
	unclassified = load_unclassified_transactions(data_dir, date(2025, 11, 15))

	assert len(unclassified) == 2
	assert unclassified[0].transaction_id == "TXN-001"
	assert unclassified[1].transaction_id == "TXN-003"


def test_save_classified_transactions(tmp_path):
	"""Test saving classified transactions (replacing unclassified)."""
	data_dir = tmp_path / "data"

	# Save original unclassified transaction
	original = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)
	save_transaction(original, data_dir)

	# Save classified version
	classified = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(account_code="EXP-GRO", debit=Decimal("45.50"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	save_classified_transactions([classified], data_dir)

	# Load and verify
	loaded = load_transactions(data_dir, date(2025, 11, 15))
	assert len(loaded) == 1
	assert loaded[0].entries[0].account_code == "EXP-GRO"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/classification/test_integration.py::test_load_unclassified_transactions -v`

Expected: FAIL with "ImportError: cannot import name 'load_unclassified_transactions'"

**Step 3: Write minimal implementation**

Create `src/small_business/classification/integration.py`:

```python
"""Integration with storage layer for classification."""

from datetime import date
from pathlib import Path

from small_business.models.transaction import Transaction
from small_business.storage.paths import get_financial_year_dir
from small_business.storage.transaction_store import load_transactions


def load_unclassified_transactions(data_dir: Path, txn_date: date) -> list[Transaction]:
	"""Load all unclassified transactions for a financial year.

	Args:
		data_dir: Data directory
		txn_date: Date to determine financial year

	Returns:
		List of unclassified transactions
	"""
	all_txns = load_transactions(data_dir, txn_date)

	# Filter for unclassified transactions
	unclassified = []
	for txn in all_txns:
		# Check if any entry has UNCLASSIFIED account code
		has_unclassified = any("UNCLASSIFIED" in entry.account_code for entry in txn.entries)
		if has_unclassified:
			unclassified.append(txn)

	return unclassified


def save_classified_transactions(
	transactions: list[Transaction],
	data_dir: Path,
) -> None:
	"""Save classified transactions, replacing unclassified versions.

	This rewrites the entire JSONL file for the financial year,
	replacing unclassified versions with classified ones.

	Args:
		transactions: Classified transactions to save
		data_dir: Data directory
	"""
	if not transactions:
		return

	# Group transactions by financial year
	by_year: dict[str, list[Transaction]] = {}
	for txn in transactions:
		fy = txn.financial_year
		if fy not in by_year:
			by_year[fy] = []
		by_year[fy].append(txn)

	# For each financial year, load all transactions and replace classified ones
	for fy, classified_txns in by_year.items():
		# Use first transaction's date to load the year
		first_date = classified_txns[0].date
		all_txns = load_transactions(data_dir, first_date)

		# Create lookup of classified transactions by ID
		classified_by_id = {txn.transaction_id: txn for txn in classified_txns}

		# Replace unclassified with classified versions
		updated_txns = []
		for txn in all_txns:
			if txn.transaction_id in classified_by_id:
				# Use classified version
				updated_txns.append(classified_by_id[txn.transaction_id])
			else:
				# Keep original
				updated_txns.append(txn)

		# Rewrite the file
		fy_dir = get_financial_year_dir(data_dir, first_date)
		txn_file = fy_dir / "transactions.jsonl"

		# Delete old file
		if txn_file.exists():
			txn_file.unlink()

		# Write all transactions
		import json

		with open(txn_file, "w") as f:
			for txn in updated_txns:
				f.write(txn.model_dump_json() + "\n")
```

Update `src/small_business/classification/__init__.py`:

```python
"""Transaction classification system."""

from .applicator import apply_classification
from .classifier import classify_batch, classify_transaction
from .integration import load_unclassified_transactions, save_classified_transactions
from .learning import create_learned_rule, extract_pattern_from_description, should_learn_rule
from .matcher import find_best_match, match_pattern
from .models import ClassificationRule, RuleMatch
from .rule_store import load_rules, save_rules
from .workflow import AcceptedClassification, ClassificationResult, classify_and_update_transactions

__all__ = [
	"ClassificationRule",
	"RuleMatch",
	"load_rules",
	"save_rules",
	"match_pattern",
	"find_best_match",
	"classify_transaction",
	"classify_batch",
	"apply_classification",
	"extract_pattern_from_description",
	"create_learned_rule",
	"should_learn_rule",
	"AcceptedClassification",
	"ClassificationResult",
	"classify_and_update_transactions",
	"load_unclassified_transactions",
	"save_classified_transactions",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/classification/test_integration.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/classification/integration.py tests/classification/test_integration.py src/small_business/classification/__init__.py
git commit -m "feat: add classification storage integration

Implement load_unclassified_transactions() and
save_classified_transactions() for integration with JSONL
storage. Handles replacing unclassified with classified versions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Update Documentation

**Files:**
- Create: `docs/usage/classification.md`
- Modify: `mkdocs.yml` (add navigation entry)

**Step 1: Write documentation**

Create `docs/usage/classification.md`:

```markdown
# Classification Guide

Phase 3 implements transaction classification with regex-based rules, user acceptance workflow, and automated rule learning.

## Quick Start

```python
from pathlib import Path
from small_business.classification import (
    classify_transaction,
    load_rules,
    AcceptedClassification,
    classify_and_update_transactions,
)
from small_business.storage import load_transactions

# Load classification rules
rules = load_rules(Path("data/config/rules.yaml"))

# Load unclassified transactions
transactions = load_transactions(Path("data"), date.today())

# Classify a single transaction
from small_business.classification import classify_transaction

match = classify_transaction(transactions[0], rules)
if match:
    print(f"Matched: {match.rule.account_code} ({match.confidence})")
else:
    print("No match - requires manual classification")
```

## Classification Workflow

### 1. Automatic Matching

```python
from small_business.classification import classify_batch

# Classify multiple transactions
results = classify_batch(transactions, rules)

for txn_id, match in results.items():
    if match:
        print(f"{txn_id}: {match.rule.account_code}")
    else:
        print(f"{txn_id}: No match")
```

### 2. User Acceptance

```python
from small_business.classification import AcceptedClassification

# User accepts or manually classifies transactions
accepted = [
    AcceptedClassification(
        transaction_id="TXN-001",
        account_code="EXP-GRO",
        description="Groceries",
        gst_inclusive=True,
        learn_rule=False,  # Already has matching rule
    ),
    AcceptedClassification(
        transaction_id="TXN-002",
        account_code="EXP-TRV-FLT",
        description="Flights",
        gst_inclusive=True,
        learn_rule=True,  # Learn new rule for future
    ),
]
```

### 3. Apply and Learn

```python
from small_business.classification import classify_and_update_transactions

result = classify_and_update_transactions(
    transactions=transactions,
    initial_rules=rules,
    accepted_classifications=accepted,
    rules_file=Path("data/config/rules.yaml"),
)

print(f"Classified: {result.stats['classified']}/{result.stats['total']}")
print(f"Rules learned: {result.stats['rules_learned']}")
```

## Rule Format

Rules are stored in YAML format:

```yaml
rules:
  - pattern: "WOOLWORTHS|COLES"
    account_code: "EXP-GRO"
    description: "Groceries"
    gst_inclusive: true
    priority: 1

  - pattern: "QANTAS|VIRGIN|JETSTAR"
    account_code: "EXP-TRV-FLT"
    description: "Flights"
    gst_inclusive: true
    priority: 2

  - pattern: "TELSTRA|OPTUS"
    account_code: "EXP-UTL-PHN"
    description: "Phone"
    gst_inclusive: true
    priority: 1
```

## Pattern Matching

- **Case-insensitive**: Patterns match regardless of case
- **Regex support**: Full regex syntax (`|` for OR, `.*` for wildcards, etc.)
- **Priority-based**: Higher priority wins when multiple rules match

## Rule Learning

When you accept a manual classification with `learn_rule=True`:

1. System extracts merchant name from description (e.g., "WOOLWORTHS" from "WOOLWORTHS 1234 PERTH")
2. Creates new rule with extracted pattern
3. Adds to rules file for future auto-classification
4. Avoids duplicates (same pattern + account code)

## Integration with Storage

### Load Unclassified

```python
from small_business.classification import load_unclassified_transactions

unclassified = load_unclassified_transactions(
    data_dir=Path("data"),
    txn_date=date.today(),
)
```

### Save Classified

```python
from small_business.classification import save_classified_transactions

save_classified_transactions(
    transactions=classified_txns,
    data_dir=Path("data"),
)
```

This replaces unclassified versions in the JSONL files.

## Example: Complete Classification Session

```python
from pathlib import Path
from datetime import date
from small_business.classification import (
    load_rules,
    load_unclassified_transactions,
    classify_batch,
    AcceptedClassification,
    classify_and_update_transactions,
    save_classified_transactions,
)

data_dir = Path("data")
rules_file = data_dir / "config" / "rules.yaml"

# 1. Load rules and unclassified transactions
rules = load_rules(rules_file)
unclassified = load_unclassified_transactions(data_dir, date.today())

# 2. Auto-classify
results = classify_batch(unclassified, rules)

# 3. Present to user for acceptance/manual classification
accepted = []
for txn in unclassified:
    match = results[txn.transaction_id]
    if match:
        # Auto-matched - user confirms
        accepted.append(AcceptedClassification(
            transaction_id=txn.transaction_id,
            account_code=match.rule.account_code,
            description=match.rule.description,
            gst_inclusive=match.rule.gst_inclusive,
            learn_rule=False,
        ))
    else:
        # No match - user manually classifies
        # (In TUI, user would select account code)
        accepted.append(AcceptedClassification(
            transaction_id=txn.transaction_id,
            account_code="EXP-OTHER",  # User input
            description="Other expense",  # User input
            gst_inclusive=True,
            learn_rule=True,  # Learn for future
        ))

# 4. Apply classifications and learn rules
result = classify_and_update_transactions(
    transactions=unclassified,
    initial_rules=rules,
    accepted_classifications=accepted,
    rules_file=rules_file,
)

# 5. Save classified transactions
save_classified_transactions(result.updated_transactions, data_dir)

print(f"Session complete: {result.stats}")
```
```

**Step 2: Update mkdocs.yml**

Add to navigation section:

```yaml
nav:
  - Home: index.md
  - Changelog: CHANGELOG.md
  - Usage:
    - Bank Import: usage/bank-import.md
    - Classification: usage/classification.md
  - API Reference:
    - Hello module: api_docs/hello_world.md
  - Examples:
    - Notebooks:
      - 1. Notebook example: notebooks/example.py
```

**Step 3: Test documentation builds**

Run: `mkdocs build`

Expected: Success with no errors

**Step 4: Commit**

```bash
git add docs/usage/classification.md mkdocs.yml
git commit -m "docs: add classification guide

Document classification workflow, rule format, pattern matching,
rule learning, and storage integration for Phase 3.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_classification_integration.py`

**Step 1: Write integration test**

Create `tests/integration/test_classification_integration.py`:

```python
"""End-to-end integration test for classification."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.classification import (
	AcceptedClassification,
	classify_and_update_transactions,
	classify_batch,
	load_rules,
	load_unclassified_transactions,
	save_classified_transactions,
	save_rules,
)
from small_business.classification.models import ClassificationRule
from small_business.models.transaction import JournalEntry, Transaction
from small_business.storage.transaction_store import load_transactions, save_transaction


def test_end_to_end_classification_workflow(tmp_path):
	"""Test complete classification workflow end-to-end."""
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "config" / "rules.yaml"

	# Step 1: Set up initial rules
	initial_rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS|COLES",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			priority=1,
		),
		ClassificationRule(
			pattern=r"BP|SHELL",
			account_code="EXP-TRV-FUL",
			description="Fuel",
			gst_inclusive=True,
			priority=1,
		),
	]
	save_rules(initial_rules, rules_file)

	# Step 2: Import unclassified transactions (simulating bank import)
	unclassified_txns = [
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
			description="QANTAS FLIGHT 789",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("280.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("280.00")),
			],
		),
		Transaction(
			transaction_id="TXN-003",
			date=date(2025, 11, 17),
			description="BP SERVICE STATION",
			entries=[
				JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("85.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("85.00")),
			],
		),
	]

	for txn in unclassified_txns:
		save_transaction(txn, data_dir)

	# Step 3: Load unclassified transactions
	loaded_unclassified = load_unclassified_transactions(data_dir, date(2025, 11, 15))
	assert len(loaded_unclassified) == 3

	# Step 4: Auto-classify
	rules = load_rules(rules_file)
	classification_results = classify_batch(loaded_unclassified, rules)

	# Check auto-classification results
	assert classification_results["TXN-001"] is not None  # WOOLWORTHS matched
	assert classification_results["TXN-001"].rule.account_code == "EXP-GRO"
	assert classification_results["TXN-002"] is None  # QANTAS no match
	assert classification_results["TXN-003"] is not None  # BP matched
	assert classification_results["TXN-003"].rule.account_code == "EXP-TRV-FUL"

	# Step 5: User accepts classifications
	accepted = [
		# Accept auto-matched WOOLWORTHS
		AcceptedClassification(
			transaction_id="TXN-001",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
			learn_rule=False,
		),
		# Manually classify QANTAS (learn rule)
		AcceptedClassification(
			transaction_id="TXN-002",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
			learn_rule=True,
		),
		# Accept auto-matched BP
		AcceptedClassification(
			transaction_id="TXN-003",
			account_code="EXP-TRV-FUL",
			description="Fuel",
			gst_inclusive=True,
			learn_rule=False,
		),
	]

	# Step 6: Apply classifications and learn rules
	result = classify_and_update_transactions(
		transactions=loaded_unclassified,
		initial_rules=rules,
		accepted_classifications=accepted,
		rules_file=rules_file,
	)

	# Check results
	assert len(result.updated_transactions) == 3
	assert result.stats["total"] == 3
	assert result.stats["classified"] == 3
	assert result.stats["rules_learned"] == 1  # QANTAS learned

	# Check account codes updated
	assert result.updated_transactions[0].entries[0].account_code == "EXP-GRO"
	assert result.updated_transactions[1].entries[0].account_code == "EXP-TRV-FLT"
	assert result.updated_transactions[2].entries[0].account_code == "EXP-TRV-FUL"

	# Step 7: Save classified transactions
	save_classified_transactions(result.updated_transactions, data_dir)

	# Step 8: Verify persistence
	all_txns = load_transactions(data_dir, date(2025, 11, 15))
	assert len(all_txns) == 3

	# All should be classified
	for txn in all_txns:
		assert "UNCLASSIFIED" not in txn.entries[0].account_code

	# Step 9: Verify learned rule saved
	updated_rules = load_rules(rules_file)
	assert len(updated_rules) == 3  # Original 2 + learned QANTAS
	qantas_rule = next((r for r in updated_rules if r.pattern == "QANTAS"), None)
	assert qantas_rule is not None
	assert qantas_rule.account_code == "EXP-TRV-FLT"

	# Step 10: Test learned rule on new transaction
	new_qantas_txn = Transaction(
		transaction_id="TXN-004",
		date=date(2025, 11, 18),
		description="QANTAS AIRWAYS BOOKING",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("350.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("350.00")),
		],
	)

	# Should auto-match with learned rule
	from small_business.classification import classify_transaction

	match = classify_transaction(new_qantas_txn, updated_rules)
	assert match is not None
	assert match.rule.account_code == "EXP-TRV-FLT"
	assert match.rule.pattern == "QANTAS"


def test_no_unclassified_after_full_workflow(tmp_path):
	"""Test that workflow results in zero unclassified transactions."""
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "config" / "rules.yaml"

	# Save initial unclassified transaction
	txn = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 15),
		description="TEST MERCHANT",
		entries=[
			JournalEntry(account_code="EXP-UNCLASSIFIED", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	# Run classification workflow
	rules = []
	accepted = [
		AcceptedClassification(
			transaction_id="TXN-001",
			account_code="EXP-OTHER",
			description="Other",
			gst_inclusive=True,
			learn_rule=True,
		)
	]

	result = classify_and_update_transactions(
		transactions=[txn],
		initial_rules=rules,
		accepted_classifications=accepted,
		rules_file=rules_file,
	)

	save_classified_transactions(result.updated_transactions, data_dir)

	# Verify no unclassified remain
	unclassified = load_unclassified_transactions(data_dir, date(2025, 11, 15))
	assert len(unclassified) == 0
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_classification_integration.py -v`

Expected: PASS (all tests)

**Step 3: Commit**

```bash
git add tests/integration/test_classification_integration.py
git commit -m "test: add classification integration tests

Add end-to-end integration tests covering complete classification
workflow from unclassified transactions through rule learning and
persistence.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

Phase 3 implementation delivers:

✅ **Classification rule models** - Pydantic models with regex patterns and priorities
✅ **YAML rule storage** - Persistent rule configuration
✅ **Pattern matching engine** - Case-insensitive regex with priority resolution
✅ **Transaction classifier** - Batch and single transaction classification
✅ **Classification applicator** - Update transaction account codes
✅ **Rule learning system** - Extract patterns and create rules from user input
✅ **Workflow orchestrator** - Complete classification with user acceptance
✅ **Storage integration** - Load unclassified and save classified transactions
✅ **Documentation** - Complete usage guide
✅ **Integration tests** - End-to-end workflow validation

**Next Phase:** Phase 4 will implement document generation for quotes and invoices using templates.

---

## Verification Checklist

Before marking Phase 3 complete, verify:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality: `uv run ruff check .`
- [ ] Formatting: `uv run ruff format .`
- [ ] Documentation builds: `mkdocs build`
- [ ] Manual test: Classify real transactions with rules
- [ ] Verify rule learning creates new rules
- [ ] Check classified transactions saved correctly
- [ ] Verify unclassified count decreases after workflow
