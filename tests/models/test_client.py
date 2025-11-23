"""Tests for Client model."""

import pytest
from pydantic import ValidationError

from small_business.models.client import Client


def test_client_with_all_fields():
	"""Test creating a client with all fields including addresses."""
	client = Client(
		client_id="Acme Corporation",
		name="Acme Corporation",
		email="contact@acme.com.au",
		phone="0412 345 678",
		abn="51 824 753 556",
		contact_person="John Smith",
		street_address="123 Business St",
		suburb="Sydney",
		state="NSW",
		postcode="2000",
		formatted_address="123 Business St, Sydney NSW 2000",
		billing_street_address="PO Box 456",
		billing_suburb="Sydney",
		billing_state="NSW",
		billing_postcode="2001",
		billing_formatted_address="PO Box 456, Sydney NSW 2001",
		notes="Preferred contact: email",
	)
	assert client.client_id == "Acme Corporation"
	assert client.name == "Acme Corporation"
	assert client.email == "contact@acme.com.au"
	assert client.phone == "0412 345 678"
	assert client.abn == "51 824 753 556"
	assert client.contact_person == "John Smith"
	assert client.street_address == "123 Business St"
	assert client.suburb == "Sydney"
	assert client.state == "NSW"
	assert client.postcode == "2000"
	assert client.formatted_address == "123 Business St, Sydney NSW 2000"
	assert client.billing_street_address == "PO Box 456"
	assert client.billing_formatted_address == "PO Box 456, Sydney NSW 2001"
	assert client.notes == "Preferred contact: email"


def test_client_with_minimal_fields():
	"""Test creating a client with only required fields (business name)."""
	client = Client(client_id="Woolworths", name="Woolworths")
	assert client.client_id == "Woolworths"
	assert client.name == "Woolworths"
	assert client.email is None
	assert client.phone is None
	assert client.abn is None
	assert client.contact_person is None
	assert client.street_address is None
	assert client.formatted_address is None
	assert client.billing_formatted_address is None
	assert client.notes == ""


def test_client_id_required():
	"""Test that client_id is required (no auto-generation)."""
	with pytest.raises(ValidationError) as exc_info:
		Client(name="Test Client")
	assert "client_id" in str(exc_info.value)


def test_client_id_cannot_be_empty():
	"""Test that client_id cannot be empty string."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="", name="Test Client")
	assert "client_id" in str(exc_info.value)


def test_client_name_required():
	"""Test that client name is required."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="Test Corp")
	assert "name" in str(exc_info.value)


def test_client_name_cannot_be_empty():
	"""Test that client name cannot be empty string."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="Test Corp", name="")
	assert "name" in str(exc_info.value)


def test_client_email_validation():
	"""Test that invalid email is rejected."""
	with pytest.raises(ValidationError) as exc_info:
		Client(client_id="Test Corp", name="Test Corp", email="not-an-email")
	assert "email" in str(exc_info.value)


def test_client_with_physical_address_only():
	"""Test client with structured physical address."""
	client = Client(
		client_id="Local Business",
		name="Local Business",
		street_address="456 Main Rd",
		suburb="Melbourne",
		state="VIC",
		postcode="3000",
	)
	assert client.street_address == "456 Main Rd"
	assert client.suburb == "Melbourne"
	assert client.state == "VIC"
	assert client.postcode == "3000"
	assert client.billing_street_address is None


def test_client_with_separate_billing_address():
	"""Test client with different billing and physical addresses."""
	client = Client(
		client_id="Corp Ltd",
		name="Corp Ltd",
		street_address="789 Office Ave",
		suburb="Brisbane",
		state="QLD",
		postcode="4000",
		billing_street_address="PO Box 123",
		billing_suburb="Brisbane",
		billing_state="QLD",
		billing_postcode="4001",
	)
	assert client.street_address == "789 Office Ave"
	assert client.billing_street_address == "PO Box 123"
	assert client.postcode == "4000"
	assert client.billing_postcode == "4001"


def test_client_serialization():
	"""Test client model serializes to dict correctly with new fields."""
	client = Client(
		client_id="Serialization Test",
		name="Serialization Test",
		email="test@example.com",
		street_address="123 Test St",
		suburb="Sydney",
		state="NSW",
		postcode="2000",
	)
	data = client.model_dump()
	assert data["client_id"] == "Serialization Test"
	assert data["name"] == "Serialization Test"
	assert data["email"] == "test@example.com"
	assert data["street_address"] == "123 Test St"
	assert data["suburb"] == "Sydney"
	assert data["state"] == "NSW"
	assert data["postcode"] == "2000"
	assert data["phone"] is None
	assert data["abn"] is None
	assert data["notes"] == ""


def test_client_deserialization():
	"""Test creating client from dict with new address fields."""
	data = {
		"client_id": "Deserialized Business",
		"name": "Deserialized Business",
		"email": "client@example.com",
		"phone": "0400 000 000",
		"abn": "12 345 678 901",
		"contact_person": "Jane Doe",
		"street_address": "999 Data Lane",
		"suburb": "Perth",
		"state": "WA",
		"postcode": "6000",
		"formatted_address": "999 Data Lane, Perth WA 6000",
		"notes": "Test notes",
	}
	client = Client.model_validate(data)
	assert client.client_id == "Deserialized Business"
	assert client.name == "Deserialized Business"
	assert client.contact_person == "Jane Doe"
	assert client.street_address == "999 Data Lane"
	assert client.formatted_address == "999 Data Lane, Perth WA 6000"
