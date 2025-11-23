"""Test client storage with case-insensitive lookups."""

from pathlib import Path

import pytest

from small_business.models import Client
from small_business.storage.client_store import load_client, load_clients, save_client


def test_save_and_load_client(tmp_path):
	"""Test saving and loading a client."""
	data_dir = tmp_path / "data"

	client = Client(
		client_id="Woolworths",
		name="Woolworths",
		email="contact@woolworths.com.au",
		phone="1300 767 969",
		abn="88 000 014 675",
	)

	# Save client
	save_client(client, data_dir)

	# Verify file exists
	client_file = data_dir / "clients" / "clients.jsonl"
	assert client_file.exists()

	# Load client
	loaded = load_client("Woolworths", data_dir)
	assert loaded.client_id == "Woolworths"
	assert loaded.name == "Woolworths"
	assert loaded.email == "contact@woolworths.com.au"


def test_case_insensitive_lookup(tmp_path):
	"""Test that client lookup is case-insensitive."""
	data_dir = tmp_path / "data"

	client = Client(
		client_id="Acme Corporation",
		name="Acme Corporation",
		email="info@acme.com",
	)
	save_client(client, data_dir)

	# Load with different cases
	loaded_lower = load_client("acme corporation", data_dir)
	loaded_upper = load_client("ACME CORPORATION", data_dir)
	loaded_mixed = load_client("AcMe CoRpOrAtIoN", data_dir)

	# All should return the same client with canonical case
	assert loaded_lower.client_id == "Acme Corporation"
	assert loaded_upper.client_id == "Acme Corporation"
	assert loaded_mixed.client_id == "Acme Corporation"


def test_update_existing_client(tmp_path):
	"""Test updating an existing client."""
	data_dir = tmp_path / "data"

	# Save initial client
	client_v1 = Client(
		client_id="Test Business",
		name="Test Business",
		email="old@test.com",
		phone="0400 000 000",
	)
	save_client(client_v1, data_dir)

	# Update client (same ID, different details)
	client_v2 = Client(
		client_id="Test Business",
		name="Test Business",
		email="new@test.com",
		phone="0400 111 111",
		abn="12 345 678 901",
	)
	save_client(client_v2, data_dir)

	# Should have only one client with updated details
	all_clients = load_clients(data_dir)
	assert len(all_clients) == 1
	assert all_clients[0].email == "new@test.com"
	assert all_clients[0].phone == "0400 111 111"
	assert all_clients[0].abn == "12 345 678 901"


def test_case_insensitive_update(tmp_path):
	"""Test that update works with different case."""
	data_dir = tmp_path / "data"

	# Save with one case
	client_v1 = Client(
		client_id="MyCompany",
		name="MyCompany",
		email="old@mycompany.com",
	)
	save_client(client_v1, data_dir)

	# Update with different case (should update, not create new)
	client_v2 = Client(
		client_id="mycompany",
		name="mycompany",
		email="new@mycompany.com",
	)
	save_client(client_v2, data_dir)

	# Should have only one client
	all_clients = load_clients(data_dir)
	assert len(all_clients) == 1
	# Should use the new case
	assert all_clients[0].client_id == "mycompany"
	assert all_clients[0].email == "new@mycompany.com"


def test_load_all_clients(tmp_path):
	"""Test loading all clients."""
	data_dir = tmp_path / "data"

	clients = [
		Client(client_id="Client A", name="Client A", email="a@example.com"),
		Client(client_id="Client B", name="Client B", email="b@example.com"),
		Client(client_id="Client C", name="Client C", email="c@example.com"),
	]

	for client in clients:
		save_client(client, data_dir)

	loaded = load_clients(data_dir)
	assert len(loaded) == 3

	# Verify all clients present (order not guaranteed)
	loaded_ids = {c.client_id for c in loaded}
	assert loaded_ids == {"Client A", "Client B", "Client C"}


def test_load_client_not_found(tmp_path):
	"""Test loading non-existent client raises KeyError."""
	data_dir = tmp_path / "data"

	with pytest.raises(KeyError, match="Client not found: NonExistent"):
		load_client("NonExistent", data_dir)


def test_load_clients_empty_directory(tmp_path):
	"""Test loading clients from empty directory returns empty list."""
	data_dir = tmp_path / "data"

	clients = load_clients(data_dir)
	assert clients == []


def test_client_with_full_address(tmp_path):
	"""Test saving and loading client with full address information."""
	data_dir = tmp_path / "data"

	client = Client(
		client_id="Full Address Corp",
		name="Full Address Corp",
		email="contact@fulladdress.com",
		phone="0400 000 000",
		abn="11 222 333 444",
		contact_person="Jane Smith",
		street_address="123 Main St",
		suburb="Sydney",
		state="NSW",
		postcode="2000",
		formatted_address="123 Main St, Sydney NSW 2000",
		billing_street_address="PO Box 456",
		billing_suburb="Sydney",
		billing_state="NSW",
		billing_postcode="2001",
		billing_formatted_address="PO Box 456, Sydney NSW 2001",
		notes="Important client",
	)

	save_client(client, data_dir)
	loaded = load_client("Full Address Corp", data_dir)

	assert loaded.contact_person == "Jane Smith"
	assert loaded.street_address == "123 Main St"
	assert loaded.suburb == "Sydney"
	assert loaded.formatted_address == "123 Main St, Sydney NSW 2000"
	assert loaded.billing_formatted_address == "PO Box 456, Sydney NSW 2001"
	assert loaded.notes == "Important client"
