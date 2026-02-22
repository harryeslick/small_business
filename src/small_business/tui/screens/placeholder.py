"""Placeholder screen used for sections not yet implemented."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class PlaceholderScreen(Screen):
	"""Generic placeholder for screens that will be built in later phases."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
	]

	def __init__(self, title: str, description: str = "Coming soon.") -> None:
		super().__init__()
		self._title = title
		self._description = description

	def compose(self) -> ComposeResult:
		yield Header()
		yield Static(f"\n\n  {self._title}", classes="placeholder-title")
		yield Static(f"  {self._description}\n", classes="placeholder-subtitle")
		yield Footer()
