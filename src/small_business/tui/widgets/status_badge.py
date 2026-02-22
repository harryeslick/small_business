"""StatusBadge widget — coloured label for entity statuses."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Label


# Map status values to CSS class names
_STATUS_CLASS_MAP: dict[str, str] = {
	"DRAFT": "status-draft",
	"SENT": "status-sent",
	"ACCEPTED": "status-accepted",
	"PAID": "status-paid",
	"OVERDUE": "status-overdue",
	"EXPIRED": "status-expired",
	"CANCELLED": "status-cancelled",
	"REJECTED": "status-rejected",
	"SCHEDULED": "status-scheduled",
	"IN_PROGRESS": "status-in-progress",
	"COMPLETED": "status-completed",
	"INVOICED": "status-invoiced",
}


class StatusBadge(Label):
	"""Display an entity status with colour coding."""

	status: reactive[str] = reactive("")

	def __init__(
		self,
		status: str = "",
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)
		self.status = status

	def watch_status(self, status: str) -> None:
		"""Update display when status changes."""
		display_text = status.replace("_", " ")
		self.update(f" {display_text} ")
		# Remove all status classes, then apply the matching one
		for cls in _STATUS_CLASS_MAP.values():
			self.remove_class(cls)
		css_class = _STATUS_CLASS_MAP.get(status.upper(), "")
		if css_class:
			self.add_class(css_class)
