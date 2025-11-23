"""Storage and data persistence."""

from .client_store import load_client, load_clients, save_client
from .paths import ensure_data_directory, get_financial_year_dir, get_transaction_file_path
from .transaction_store import (
	load_transactions,
	save_transaction,
	transaction_exists,
	update_transaction,
)

__all__ = [
	# Paths
	"ensure_data_directory",
	"get_financial_year_dir",
	"get_transaction_file_path",
	# Transactions
	"save_transaction",
	"load_transactions",
	"transaction_exists",
	"update_transaction",
	# Clients
	"save_client",
	"load_client",
	"load_clients",
]
