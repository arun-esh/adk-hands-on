"""Helpers shared by the tool files: read the JSON data files."""
import json
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load_products() -> list:
    return json.loads((DATA / "products.json").read_text(encoding="utf-8"))["products"]


def units_sold(days: int) -> dict:
    """Units sold per product (by sku) over the last `days` full days before the store's
    'today' (as_of_date in sales.json), so 30 days is the whole history. The real clock
    is never used."""
    data = json.loads((DATA / "sales.json").read_text(encoding="utf-8"))
    today = date.fromisoformat(data["as_of_date"])
    first_day = today - timedelta(days=days)
    last_day = today - timedelta(days=1)
    totals = {}
    for row in data["sales"]:
        if first_day <= date.fromisoformat(row["date"]) <= last_day:
            totals[row["sku"]] = totals.get(row["sku"], 0) + row["units_sold"]
    return totals
