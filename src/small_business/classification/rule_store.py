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
