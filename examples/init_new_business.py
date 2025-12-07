"""Example: Initialize a new business directory.

This example shows how to use the init_business function to set up
a complete business directory structure with all required folders
and configuration files.
"""

from pathlib import Path

from small_business import init_business
from small_business.models import Settings

# Create business settings
settings = Settings(
	business_name="Earthworks Studio",
	business_abn="12 345 678 901",
	business_email="hello@earthworks.studio",
	business_phone="0400 123 456",
	business_address="123 Studio Lane, Brunswick VIC 3056",
	gst_rate=0.10,
	financial_year_start_month=7,  # July (Australian financial year)
)

# Initialize business in a specific directory
# (Use Path.cwd() for current directory, or specify a path)
business_path = Path.home() / "businesses"

try:
	business_dir = init_business(settings, business_path)
	print(f"✅ Business initialized successfully!")
	print(f"📁 Business directory: {business_dir}")
	print("\n📂 Created structure:")
	print(f"   {business_dir}/")
	print("   ├── clients/")
	print("   ├── quotes/")
	print("   ├── invoices/")
	print("   ├── jobs/")
	print("   ├── transactions/")
	print("   ├── receipts/")
	print("   ├── reports/")
	print("   └── config/")
	print("       ├── settings.json")
	print("       └── chart_of_accounts.yaml")

except FileExistsError as e:
	print(f"❌ Error: {e}")
	print("Business directory already exists. Use a different name or location.")
