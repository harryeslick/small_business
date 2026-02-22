"""AccountSelector widget — fuzzy search for account codes."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option


class AccountSelector(Widget):
	"""Fuzzy-search input with dropdown for selecting account codes.

	Posts an AccountSelector.Selected message when a selection is made.
	"""

	DEFAULT_CSS = """
	AccountSelector {
		height: auto;
		max-height: 16;
	}

	AccountSelector #account-search {
		margin-bottom: 0;
	}

	AccountSelector #account-options {
		height: auto;
		max-height: 10;
		display: none;
	}

	AccountSelector #account-options.visible {
		display: block;
	}
	"""

	class Selected(Message):
		"""Posted when an account is selected."""

		def __init__(self, account_code: str, description: str) -> None:
			super().__init__()
			self.account_code = account_code
			self.description = description

	value: reactive[str] = reactive("")

	def __init__(
		self,
		accounts: list[tuple[str, str]] | None = None,
		*,
		placeholder: str = "Search accounts...",
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__(id=id, classes=classes)
		# accounts is a list of (code, description) tuples
		self._accounts: list[tuple[str, str]] = accounts or []
		self._placeholder = placeholder

	def compose(self) -> ComposeResult:
		with Vertical():
			yield Input(placeholder=self._placeholder, id="account-search")
			yield OptionList(id="account-options")

	def set_accounts(self, accounts: list[tuple[str, str]]) -> None:
		"""Update the available account list."""
		self._accounts = accounts

	def on_input_changed(self, event: Input.Changed) -> None:
		"""Filter options as user types."""
		if event.input.id != "account-search":
			return

		query = event.value.strip().lower()
		option_list = self.query_one("#account-options", OptionList)
		option_list.clear_options()

		if not query:
			option_list.remove_class("visible")
			return

		# Fuzzy match against both code and description
		matches: list[tuple[str, str]] = []
		for code, desc in self._accounts:
			if query in code.lower() or query in desc.lower():
				matches.append((code, desc))

		if matches:
			for code, desc in matches[:10]:  # Limit to 10 results
				option_list.add_option(Option(f"{code}  {desc}", id=code))
			option_list.add_class("visible")
		else:
			option_list.remove_class("visible")

	def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
		"""Handle account selection from dropdown."""
		code = str(event.option.id)
		# Find the description
		desc = ""
		for c, d in self._accounts:
			if c == code:
				desc = d
				break

		self.value = code
		search_input = self.query_one("#account-search", Input)
		search_input.value = f"{code}  {desc}"
		self.query_one("#account-options", OptionList).remove_class("visible")
		self.post_message(self.Selected(code, desc))

	def on_input_submitted(self, event: Input.Submitted) -> None:
		"""Select first match on Enter."""
		if event.input.id != "account-search":
			return

		option_list = self.query_one("#account-options", OptionList)
		if option_list.option_count > 0:
			# Select the first (highlighted) option
			option = option_list.get_option_at_index(0)
			code = str(option.id)
			desc = ""
			for c, d in self._accounts:
				if c == code:
					desc = d
					break
			self.value = code
			event.input.value = f"{code}  {desc}"
			option_list.remove_class("visible")
			self.post_message(self.Selected(code, desc))

	def clear(self) -> None:
		"""Reset the selector."""
		self.value = ""
		self.query_one("#account-search", Input).value = ""
		self.query_one("#account-options", OptionList).remove_class("visible")
