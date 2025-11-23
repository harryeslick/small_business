"""Client storage using JSONL format with case-insensitive lookups."""

import json
from pathlib import Path

from small_business.models import Client


def save_client(client: Client, data_dir: Path) -> None:
	"""Save or update client in JSONL file with case-insensitive uniqueness.

	Args:
		client: Client to save
		data_dir: Base data directory

	Notes:
		- Client IDs are matched case-insensitively
		- Updates existing client if found (case-insensitive match)
		- Preserves the new client_id case when updating
	"""
	clients_dir = data_dir / "clients"
	clients_dir.mkdir(parents=True, exist_ok=True)
	clients_file = clients_dir / "clients.jsonl"

	# Load existing clients
	existing_clients = load_clients(data_dir)

	# Normalize ID for comparison
	normalized_id = client.client_id.lower()

	# Find and update existing client (case-insensitive)
	updated = False
	for i, existing in enumerate(existing_clients):
		if existing.client_id.lower() == normalized_id:
			# Update existing record with new client data
			existing_clients[i] = client
			updated = True
			break

	if not updated:
		# New client
		existing_clients.append(client)

	# Rewrite file
	with open(clients_file, "w") as f:
		for c in existing_clients:
			f.write(c.model_dump_json() + "\n")


def load_client(client_id: str, data_dir: Path) -> Client:
	"""Load a client by ID (case-insensitive lookup).

	Args:
		client_id: Client business name (case-insensitive)
		data_dir: Base data directory

	Returns:
		Client matching the ID

	Raises:
		KeyError: If client not found
	"""
	clients = load_clients(data_dir)
	normalized_id = client_id.lower()

	for client in clients:
		if client.client_id.lower() == normalized_id:
			return client

	raise KeyError(f"Client not found: {client_id}")


def load_clients(data_dir: Path) -> list[Client]:
	"""Load all clients from JSONL file.

	Args:
		data_dir: Base data directory

	Returns:
		List of all clients (empty list if file doesn't exist)
	"""
	clients_file = data_dir / "clients" / "clients.jsonl"

	if not clients_file.exists():
		return []

	clients = []
	with open(clients_file) as f:
		for line in f:
			line = line.strip()
			if line:
				data = json.loads(line)
				client = Client.model_validate(data)
				clients.append(client)

	return clients
