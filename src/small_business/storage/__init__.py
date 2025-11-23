"""Storage and data persistence."""

from .client_store import load_client, load_clients, save_client
from .invoice_store import load_invoice, load_invoices, save_invoice
from .paths import ensure_data_directory, get_financial_year_dir, get_transaction_file_path
from .quote_store import load_quote, load_quotes, save_quote
from .settings_store import load_settings, save_settings
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
	# Quotes
	"save_quote",
	"load_quote",
	"load_quotes",
	# Invoices
	"save_invoice",
	"load_invoice",
	"load_invoices",
	# Settings
	"save_settings",
	"load_settings",
]
