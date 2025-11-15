"""Tests for Client model."""

import pytest
from pydantic import ValidationError

from small_business.models.client import Client


def test_client_with_all_fields():
	"""Test creating a client with all fields."""
	client = Client(
		client_id="C-20251115-001",
		name="Acme Corporation",
		email="contact@acme.com.au",
		phone="0412 345 678",
		abn="51 824 753 556",
		notes="Preferred contact: email",
	)
	assert client.client_id == "C-20251115-001"
	assert client.name == "Acme Corporation"
	assert client.email == "contact@acme.com.au"
	assert client.phone == "0412 345 678"
	assert client.abn == "51 824 753 556"
	assert client.notes == "Preferred contact: email"


def test_client_with_minimal_fields():
	"""Test creating a client with only required fields."""
	client = Client(client_id="C-20251115-002", name="Jane Doe")
	assert client.client_id == "C-20251115-002"
	assert client.name == "Jane Doe"
	assert client.email is None
	assert client.phone is None
	assert client.abn is None
	assert client.notes == ""


def test_client_auto_generates_id():
	"""Test that client ID is auto-generated if not provided."""
	client = Client(name="Test Client")
	assert client.client_id.startswith("C-")
	assert len(client.client_id) >= 14


def test_client_name_required():
	"""Test that client name is required."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="C-20251115-003")
	assert "name" in str(exc_info.value)


def test_client_name_cannot_be_empty():
	"""Test that client name cannot be empty string."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="C-20251115-004", name="")
	assert "name" in str(exc_info.value)


def test_client_email_validation():
	"""Test that invalid email is rejected."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="C-20251115-005", name="Test", email="not-an-email")
	assert "email" in str(exc_info.value)


def test_client_serialization():
	"""Test client model serializes to dict correctly."""
	client = Client(client_id="C-20251115-006", name="Test Client", email="test@example.com")
	data = client.model_dump()
	assert data["client_id"] == "C-20251115-006"
	assert data["name"] == "Test Client"
	assert data["email"] == "test@example.com"
	assert data["phone"] is None
	assert data["abn"] is None
	assert data["notes"] == ""


def test_client_deserialization():
	"""Test creating client from dict."""
	data = {
		"client_id": "C-20251115-007",
		"name": "Deserialized Client",
		"email": "client@example.com",
		"phone": "0400 000 000",
		"abn": "12 345 678 901",
		"notes": "Test notes",
	}
	client = Client.model_validate(data)
	assert client.client_id == "C-20251115-007"
	assert client.name == "Deserialized Client"
