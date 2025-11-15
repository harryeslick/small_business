"""Line item model for quotes and invoices."""

from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class LineItem(BaseModel):
	"""Line item for quotes and invoices."""

	description: str = Field(min_length=1)
	quantity: Decimal = Field(gt=0, decimal_places=2)
	unit_price: Decimal = Field(ge=0, decimal_places=2)
	gst_inclusive: bool = True

	@computed_field
	@property
	def subtotal(self) -> Decimal:
		"""Calculate subtotal (quantity × unit_price)."""
		return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

	@computed_field
	@property
	def gst_amount(self) -> Decimal:
		"""Calculate GST amount (1/11 if inclusive, 10% if exclusive)."""
		if self.gst_inclusive:
			# GST = subtotal × 1/11
			return (self.subtotal / Decimal("11")).quantize(Decimal("0.01"))
		else:
			# GST = subtotal × 10%
			return (self.subtotal * Decimal("0.10")).quantize(Decimal("0.01"))

	@computed_field
	@property
	def total(self) -> Decimal:
		"""Calculate total (subtotal + GST if exclusive, subtotal if inclusive)."""
		if self.gst_inclusive:
			return self.subtotal
		else:
			return (self.subtotal + self.gst_amount).quantize(Decimal("0.01"))
