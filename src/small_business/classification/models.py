"""Classification rule models."""

from pydantic import BaseModel, Field


class ClassificationRule(BaseModel):
	"""Rule for classifying transactions based on description pattern."""

	pattern: str = Field(min_length=1, description="Regex pattern to match transaction description")
	account_code: str = Field(min_length=1, description="Account code to assign")
	description: str = Field(min_length=1, description="Human-readable description of rule")
	gst_inclusive: bool = Field(description="Whether transactions are GST inclusive")
	priority: int = Field(
		default=0, ge=0, description="Priority for conflicting rules (higher = higher priority)"
	)


class RuleMatch(BaseModel):
	"""Result of matching a rule against a transaction."""

	rule: ClassificationRule
	confidence: float = Field(ge=0.0, le=1.0, description="Match confidence score (0-1)")
	matched_text: str = Field(description="The text that matched the pattern")
