"""Client model."""

from pydantic import BaseModel, EmailStr, Field


class Client(BaseModel):
	"""Client/customer business information.

	Client ID is the business name (human-readable, unique identifier).
	Supports both physical and billing addresses with structured and formatted fields.
	"""

	# Identity - business name is the unique identifier
	client_id: str = Field(min_length=1)
	name: str = Field(min_length=1)

	# Contact information
	email: EmailStr | None = None
	phone: str | None = None
	contact_person: str | None = None

	# Business information
	abn: str | None = None

	# Structured address fields (for validation/formatting)
	street_address: str | None = None
	suburb: str | None = None
	state: str | None = None
	postcode: str | None = None

	# Formatted address for display/documents
	formatted_address: str | None = None

	# Billing address (if different from physical)
	billing_street_address: str | None = None
	billing_suburb: str | None = None
	billing_state: str | None = None
	billing_postcode: str | None = None
	billing_formatted_address: str | None = None

	# Additional
	notes: str = ""
