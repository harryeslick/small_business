# Expense Classification

The expense classification system automates categorization of bank transactions using pattern-based rules with machine learning assistance.

## Overview

The classification system:

- **Pattern Matching**: Uses regex patterns to match transaction descriptions
- **Priority-Based**: Handles multiple matches using rule priorities
- **Auto-Learning**: Learns new patterns from user classifications
- **Storage Integration**: Automatically updates transactions in JSONL storage

## Quick Start

### 1. Create Classification Rules

Create a YAML file with classification rules:

```yaml
rules:
  - pattern: "WOOLWORTHS|COLES"
    account_code: "EXP-GRO"
    description: "Groceries"
    gst_inclusive: true
    priority: 0

  - pattern: "QANTAS|VIRGIN"
    account_code: "EXP-TRV-FLT"
    description: "Flights"
    gst_inclusive: true
    priority: 0
```

### 2. Load and Classify Transactions

```python
from pathlib import Path
from datetime import date
from small_business.classification import load_rules, load_and_classify_unclassified

# Load rules
rules_file = Path("rules.yaml")
rules = load_rules(rules_file)

# Classify unclassified transactions for financial year
data_dir = Path("data")
txn_date = date(2025, 11, 15)  # Any date in FY

results = load_and_classify_unclassified(
    data_dir,
    txn_date,
    rules,
    rules_file,
    auto_accept_threshold=1.0
)

# Review results
for txn_id, result in results.items():
    if result.decision == "accepted":
        print(f"Auto-classified: {txn_id}")
    elif result.decision == "pending":
        print(f"Needs review: {txn_id}")
```

## Core Components

### 1. Classification Rules

Rules define patterns to match transactions:

```python
from small_business.classification import ClassificationRule

rule = ClassificationRule(
    pattern=r"WOOLWORTHS",  # Regex pattern (case-insensitive)
    account_code="EXP-GRO",  # Target account code
    description="Groceries",  # Human-readable description
    gst_inclusive=True,  # Whether amounts include GST
    priority=0  # Higher priority wins on conflicts
)
```

**Pattern Tips:**
- Patterns are case-insensitive regex
- Use `|` for alternatives: `"WOOLWORTHS|COLES"`
- Simple text works: `"QANTAS"` matches "QANTAS FLIGHT 123"
- Higher priority numbers win when multiple rules match

### 2. Pattern Matching

Match individual transactions:

```python
from small_business.classification import match_pattern, find_best_match

# Match single rule
match = match_pattern("WOOLWORTHS 1234", rule)
if match:
    print(f"Matched: {match.matched_text}")
    print(f"Confidence: {match.confidence}")

# Find best match from multiple rules
best_match = find_best_match("WOOLWORTHS 1234", rules)
```

### 3. Applying Classifications

Update transaction account codes:

```python
from small_business.classification import apply_classification

# Apply matched rule to transaction
classified_txn = apply_classification(transaction, match)

# Original transaction is preserved (returns new instance)
assert transaction is not classified_txn
```

### 4. Rule Learning

Extract patterns from user classifications:

```python
from small_business.classification import learn_rule

# User manually classifies a transaction
new_rule = learn_rule(
    transaction=txn,
    account_code="EXP-GRO",
    description="Groceries",
    gst_inclusive=True,
    priority=0
)

# Automatically extracts merchant name pattern
print(new_rule.pattern)  # "WOOLWORTHS" (extracted from "WOOLWORTHS 1234 PERTH")
```

**Learning Algorithm:**
- Extracts merchant name from description
- Removes numbers, locations (PERTH, SYDNEY, etc.)
- Handles known single-word merchants (COLES, WOOLWORTHS)
- Preserves multi-word brands (BUNNINGS WAREHOUSE)

### 5. Workflow Orchestration

Handle user review and acceptance:

```python
from small_business.classification import classify_and_review, AcceptanceDecision

# Auto-accept high confidence matches
result = classify_and_review(
    transaction=txn,
    rules=rules,
    auto_accept_threshold=1.0
)

if result.decision == AcceptanceDecision.ACCEPTED:
    print("Auto-classified!")
elif result.decision == AcceptanceDecision.PENDING:
    print("Needs user review")

# User accepts suggestion
result = classify_and_review(
    transaction=txn,
    rules=rules,
    auto_accept_threshold=1.1,  # Above confidence
    user_accepted=True
)

# User rejects and provides alternative
result = classify_and_review(
    transaction=txn,
    rules=rules,
    auto_accept_threshold=1.1,
    user_accepted=False,
    user_classification=("EXP-OTH", "Other expense", True)
)

# Learned rule available for both accept and reject
if result.learned_rule:
    rules.append(result.learned_rule)
    save_rules(rules, rules_file)
```

### 6. Storage Integration

Persist classified transactions:

```python
from small_business.classification import classify_and_save

# Classify and save to storage
result = classify_and_save(
    transaction=txn,
    rules=rules,
    rules_file=rules_file,
    data_dir=data_dir,
    auto_accept_threshold=1.0
)

# Transaction automatically updated in JSONL file
```

## Acceptance Decisions

The workflow returns decision types:

- **ACCEPTED**: Auto-accepted or user accepted suggested classification
- **REJECTED**: User rejected suggestion and provided alternative
- **MANUAL**: No suggestion, user classified manually
- **PENDING**: Awaiting user decision

## Rule Storage

Rules are stored in YAML format:

```yaml
rules:
  - pattern: "WOOLWORTHS"
    account_code: "EXP-GRO"
    description: "Groceries"
    gst_inclusive: true
    priority: 0

  - pattern: "BUNNINGS WAREHOUSE"
    account_code: "EXP-SUP"
    description: "Supplies"
    gst_inclusive: true
    priority: 10  # Higher priority for specific match
```

**Load and Save:**
```python
from pathlib import Path
from small_business.classification import load_rules, save_rules

rules_file = Path("rules.yaml")

# Load existing rules
rules = load_rules(rules_file)  # Returns [] if file doesn't exist

# Add new rules
rules.append(new_rule)

# Save back to file
save_rules(rules, rules_file)
```

## Integration with Phase 2 Storage

The classification system integrates with the JSONL storage from Phase 2:

```python
# Load unclassified transactions
from small_business.storage import load_transactions

txns = load_transactions(data_dir, txn_date)
unclassified = [
    txn for txn in txns
    if any("UNCLASSIFIED" in e.account_code for e in txn.entries)
]

# Classify and update storage
results = load_and_classify_unclassified(
    data_dir,
    txn_date,
    rules,
    rules_file
)

# Auto-accepted transactions are automatically updated in JSONL
```

## Example Workflow

Complete classification workflow:

```python
from pathlib import Path
from datetime import date
from small_business.classification import (
    load_rules,
    save_rules,
    load_and_classify_unclassified,
    AcceptanceDecision,
)

# Setup
data_dir = Path("data")
rules_file = Path("rules.yaml")
txn_date = date(2025, 11, 15)

# Load rules
rules = load_rules(rules_file)

# Classify with auto-accept
results = load_and_classify_unclassified(
    data_dir,
    txn_date,
    rules,
    rules_file,
    auto_accept_threshold=1.0
)

# Collect learned rules
new_rules = []

# Review pending classifications
for txn_id, result in results.items():
    if result.decision == AcceptanceDecision.PENDING:
        # Present to user for classification
        # ... user interaction ...

        # User classifies transaction
        from small_business.classification import learn_rule

        new_rule = learn_rule(
            transaction=result.transaction,
            account_code="EXP-GRO",  # User's choice
            description="Groceries",
            gst_inclusive=True
        )
        new_rules.append(new_rule)

# Save learned rules
if new_rules:
    all_rules = rules + new_rules
    save_rules(all_rules, rules_file)
```

## API Reference

See individual module documentation for complete API details:

- `classification.models`: Data models (ClassificationRule, RuleMatch)
- `classification.rule_store`: YAML persistence (load_rules, save_rules)
- `classification.matcher`: Pattern matching (match_pattern, find_best_match)
- `classification.applicator`: Apply rules (apply_classification)
- `classification.learner`: Extract patterns (learn_rule)
- `classification.classifier`: Classify transactions (classify_transaction, classify_batch)
- `classification.workflow`: User review workflow (classify_and_review, AcceptanceDecision)
- `classification.storage_integration`: Storage integration (classify_and_save, load_and_classify_unclassified)
