"""Shared settings for the E-Commerce Admin Dashboard project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "output"

# City -> sales region (used to enrich customers during cleaning)
CITY_REGION = {
    "Jaipur": "North", "Delhi": "North", "Lucknow": "North", "Chandigarh": "North",
    "Mumbai": "West", "Pune": "West", "Ahmedabad": "West",
    "Bengaluru": "South", "Hyderabad": "South", "Chennai": "South",
    "Kolkata": "East", "Indore": "Central",
}

# Orders in these statuses count as real sales. Cancelled / Returned do not.
VALID_STATUSES = ["Delivered", "Shipped", "Processing"]
ALL_STATUSES = VALID_STATUSES + ["Cancelled", "Returned"]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Net Banking"]
