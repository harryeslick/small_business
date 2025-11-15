"""Client model."""

from pydantic import BaseModel, EmailStr, Field

from .utils import generate_client_id


class Client(BaseModel):
	"""Client/customer information."""

	client_id: str = Field(default_factory=generate_client_id)
	name: str = Field(min_length=1)
	email: EmailStr | None = None
	phone: str | None = None
	abn: str | None = None
	notes: str = ""
