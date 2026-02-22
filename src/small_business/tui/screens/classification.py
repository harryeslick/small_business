"""Classification screen — batch classify unclassified transactions."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
	Button,
	Checkbox,
	DataTable,
	Footer,
	Header,
	Static,
)

from small_business.classification import (
	classify_and_save,
	load_rules,
	save_rules,
)
from small_business.classification.classifier import classify_transaction
from small_business.models import Transaction
from small_business.tui.utils import format_currency, format_date_short
from small_business.tui.widgets.account_selector import AccountSelector


class ClassificationScreen(Screen):
	"""Classify unclassified transactions with suggestions and manual override."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("a", "accept_suggestion", "Accept", show=True),
		Binding("s", "skip", "Skip", show=True),
		Binding("A", "accept_all", "Accept All", show=True),
	]

	def __init__(self) -> None:
		super().__init__()
		self._transactions: list[Transaction] = []
		self._suggestions: dict[str, object] = {}  # txn_id -> RuleMatch | None
		self._rules: list = []
		self._rules_file: Path | None = None
		self._current_index: int = 0
		self._classified_count: int = 0
		self._accounts: list[tuple[str, str]] = []

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="classify-content"):
			# Header with progress
			with Horizontal(id="classify-header"):
				yield Static(" Classify Transactions", classes="dashboard-panel-title")
				yield Static("", id="classify-progress")

			# Transaction table (top)
			yield DataTable(id="txn-table", cursor_type="row")

			# Detail panel (bottom)
			with Vertical(id="detail-panel", classes="dashboard-panel"):
				yield Static("", id="detail-info")

				# Suggestion display
				yield Static("", id="suggestion-text")

				# Manual classification
				with Vertical(id="manual-classify"):
					yield Static("Select account:", classes="wizard-label")
					yield AccountSelector(id="account-picker")

				# Learn rule checkbox
				yield Checkbox(
					"Learn rule from this classification", id="learn-rule-check", value=True
				)

				# Action buttons
				with Horizontal(id="classify-buttons"):
					yield Button("Accept [a]", variant="primary", id="btn-accept")
					yield Button("Classify [Enter]", variant="success", id="btn-classify")
					yield Button("Skip [s]", variant="default", id="btn-skip")
					yield Button("Accept All High [A]", variant="warning", id="btn-accept-all")

		yield Footer()

	def on_mount(self) -> None:
		"""Load unclassified transactions and rules."""
		# Set up table
		table = self.query_one("#txn-table", DataTable)
		table.add_columns("Date", "Description", "Amount", "Suggestion", "Conf.")
		table.zebra_stripes = True

		self._load_data()

	def _load_data(self) -> None:
		"""Load unclassified transactions and classification rules."""
		storage = self.app.storage
		if storage is None:
			return

		# Load rules
		if self.app.data_dir:
			self._rules_file = self.app.data_dir / "config" / "classification_rules.yaml"
			self._rules = load_rules(self._rules_file)

		# Load account codes for the selector
		try:
			chart = storage.get_chart_of_accounts()
			self._accounts = [(acc.name, acc.description) for acc in chart.accounts]
			account_selector = self.query_one("#account-picker", AccountSelector)
			account_selector.set_accounts(self._accounts)
		except FileNotFoundError:
			pass

		# Load unclassified transactions
		try:
			self._transactions = storage.get_unclassified_transactions()
		except Exception:
			self._transactions = []

		# Classify batch to get suggestions
		self._suggestions = {}
		for txn in self._transactions:
			match = classify_transaction(txn, self._rules)
			self._suggestions[txn.transaction_id] = match

		self._current_index = 0
		self._classified_count = 0
		self._refresh_table()
		self._refresh_detail()

	def _refresh_table(self) -> None:
		"""Refresh the transaction table."""
		table = self.query_one("#txn-table", DataTable)
		table.clear()

		for txn in self._transactions:
			match = self._suggestions.get(txn.transaction_id)
			if match:
				suggestion = match.rule.account_code
				confidence = f"{'*' if match.confidence >= 1.0 else '~'}"
			else:
				suggestion = "???"
				confidence = "?"

			# Calculate display amount from entries
			amount = _txn_display_amount(txn)
			table.add_row(
				format_date_short(txn.date),
				txn.description[:35],
				format_currency(amount, show_sign=True),
				suggestion,
				confidence,
				key=txn.transaction_id,
			)

		# Update progress indicator
		total = len(self._transactions)
		progress_text = f" {self._classified_count} of {total} classified this session"
		self.query_one("#classify-progress", Static).update(progress_text)

		# Move cursor to current index
		if total > 0 and self._current_index < total:
			table.move_cursor(row=self._current_index)

	def _refresh_detail(self) -> None:
		"""Update the detail panel for the currently selected transaction."""
		if not self._transactions or self._current_index >= len(self._transactions):
			self.query_one("#detail-info", Static).update(" No transactions to classify.")
			self.query_one("#suggestion-text", Static).update("")
			return

		txn = self._transactions[self._current_index]
		match = self._suggestions.get(txn.transaction_id)
		amount = _txn_display_amount(txn)

		detail = f"  {txn.description}  |  {format_currency(amount, show_sign=True)}  |  {txn.date}"
		self.query_one("#detail-info", Static).update(detail)

		if match:
			suggestion = (
				f"  Suggested: [bold]{match.rule.account_code}[/]"
				f"  ({match.rule.description})"
				f"  Confidence: {'high' if match.confidence >= 1.0 else 'medium'}"
			)
			# Show accept button, hide manual classify initially
			self.query_one("#btn-accept", Button).disabled = False
		else:
			suggestion = "  No matching rule. Select an account manually below."
			self.query_one("#btn-accept", Button).disabled = True

		self.query_one("#suggestion-text", Static).update(suggestion)

		# Clear the account selector
		self.query_one("#account-picker", AccountSelector).clear()

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Update detail panel when a different row is highlighted."""
		if event.cursor_row is not None:
			self._current_index = event.cursor_row
			self._refresh_detail()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle action button clicks."""
		if event.button.id == "btn-accept":
			self.action_accept_suggestion()
		elif event.button.id == "btn-classify":
			self._do_manual_classify()
		elif event.button.id == "btn-skip":
			self.action_skip()
		elif event.button.id == "btn-accept-all":
			self.action_accept_all()

	def action_accept_suggestion(self) -> None:
		"""Accept the auto-suggested classification for the current transaction."""
		if not self._transactions or self._current_index >= len(self._transactions):
			return

		txn = self._transactions[self._current_index]
		match = self._suggestions.get(txn.transaction_id)
		if not match:
			self.notify("No suggestion to accept. Use manual classification.", severity="warning")
			return

		should_learn = self.query_one("#learn-rule-check", Checkbox).value

		try:
			result = classify_and_save(
				transaction=txn,
				rules=self._rules,
				rules_file=self._rules_file,
				data_dir=self.app.data_dir,
				user_accepted=True,
			)

			if should_learn and result.learned_rule:
				self._rules.append(result.learned_rule)
				save_rules(self._rules, self._rules_file)

			self._on_classified(txn)
		except Exception as e:
			self.notify(f"Classification failed: {e}", severity="error")

	def _do_manual_classify(self) -> None:
		"""Apply manual classification from the account selector."""
		if not self._transactions or self._current_index >= len(self._transactions):
			return

		account_selector = self.query_one("#account-picker", AccountSelector)
		account_code = account_selector.value
		if not account_code:
			self.notify("Please select an account first.", severity="warning")
			return

		txn = self._transactions[self._current_index]
		should_learn = self.query_one("#learn-rule-check", Checkbox).value

		# Find description for the account
		desc = account_code
		for code, d in self._accounts:
			if code == account_code:
				desc = d
				break

		try:
			result = classify_and_save(
				transaction=txn,
				rules=self._rules,
				rules_file=self._rules_file,
				data_dir=self.app.data_dir,
				user_classification=(account_code, desc, True),
			)

			if should_learn and result.learned_rule:
				self._rules.append(result.learned_rule)
				save_rules(self._rules, self._rules_file)

			self._on_classified(txn)
		except Exception as e:
			self.notify(f"Classification failed: {e}", severity="error")

	def on_account_selector_selected(self, event: AccountSelector.Selected) -> None:
		"""Auto-classify when an account is selected from the dropdown."""
		# Don't auto-classify — let the user click "Classify" or press Enter
		pass

	def action_skip(self) -> None:
		"""Skip to the next transaction without classifying."""
		if self._current_index < len(self._transactions) - 1:
			self._current_index += 1
			table = self.query_one("#txn-table", DataTable)
			table.move_cursor(row=self._current_index)
			self._refresh_detail()
		else:
			self.notify("Reached the end of the list.", severity="information")

	def action_accept_all(self) -> None:
		"""Accept all high-confidence suggestions at once."""
		if not self._transactions:
			return

		accepted = 0
		to_remove: list[Transaction] = []

		for txn in self._transactions:
			match = self._suggestions.get(txn.transaction_id)
			if match and match.confidence >= 1.0:
				try:
					classify_and_save(
						transaction=txn,
						rules=self._rules,
						rules_file=self._rules_file,
						data_dir=self.app.data_dir,
						user_accepted=True,
					)
					to_remove.append(txn)
					accepted += 1
				except Exception:
					pass  # Skip individual failures

		# Remove classified transactions from list
		for txn in to_remove:
			self._transactions.remove(txn)
			self._suggestions.pop(txn.transaction_id, None)

		self._classified_count += accepted
		self._current_index = 0
		self._refresh_table()
		self._refresh_detail()

		# Refresh app counts
		self.app.action_data_changed()

		self.notify(
			f"Auto-accepted {accepted} high-confidence classifications.",
			title="Bulk Accept",
		)

	def _on_classified(self, txn: Transaction) -> None:
		"""Handle post-classification bookkeeping for a single transaction."""
		self._transactions.remove(txn)
		self._suggestions.pop(txn.transaction_id, None)
		self._classified_count += 1

		# Adjust index
		if self._current_index >= len(self._transactions):
			self._current_index = max(0, len(self._transactions) - 1)

		self._refresh_table()
		self._refresh_detail()

		# Refresh app counts
		self.app.action_data_changed()

		if not self._transactions:
			self.notify("All transactions classified!", title="Complete")


def _txn_display_amount(txn: Transaction) -> object:
	"""Calculate a display amount for a transaction.

	Uses the first bank entry if present, otherwise the transaction total.
	"""

	for entry in txn.entries:
		if entry.account_code.startswith("BANK"):
			return entry.debit - entry.credit
	# Fallback: show the transaction amount
	return txn.amount
