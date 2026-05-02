"""Command-line interface for initializing a new business."""

from small_business.services.business_setup import init_business

# This is where command-line argument parsing would go.
# For now, it just re-exports the service function.
__all__ = ["init_business"]
