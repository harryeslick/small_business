"""Document generation functionality."""

from .generator import generate_invoice_document, generate_quote_document
from .templates import render_invoice_context, render_quote_context

__all__ = [
	"render_quote_context",
	"render_invoice_context",
	"generate_quote_document",
	"generate_invoice_document",
]
