"""Tools added for the manager role: sales. The owner gets these too."""
import logging
from typing import Any, Dict

from ._data import load_products, units_sold

logger = logging.getLogger(__name__)


def get_sales_summary(name: str, days: int = 7) -> Dict[str, Any]:
    """
    Shows how many units of a product were sold over the last few days.

    Args:
        name: Part of the product name (e.g., 'Milkyroll').
        days: How many days to look back, before the store's today (default 7).

    Returns:
        A dictionary with a status ('success', 'not_found' or 'error') and the units sold
        for each matching product.
    """
    try:
        if days < 1:
            return {"status": "error", "message": "days must be at least 1."}
        totals = units_sold(days)
        matches = [
            {"name": p["name"], "units_sold": totals.get(p["sku"], 0)}
            for p in load_products()
            if name.strip().lower() in p["name"].lower()
        ]
        if not matches:
            return {"status": "not_found", "message": f"No product name contains '{name}'."}
        return {"status": "success", "days": days, "matches": matches}
    except Exception as e:
        logger.error(f"Error in get_sales_summary: {e}")
        return {"status": "error", "message": f"A problem occurred while reading sales: {str(e)}"}


def get_top_sellers(days: int = 7, limit: int = 3) -> Dict[str, Any]:
    """
    Lists the best-selling products over the last few days.

    Args:
        days: How many days to look back, before the store's today (default 7).
        limit: How many products to list (default 3).

    Returns:
        A dictionary with a status ('success' or 'error') and the top sellers, best first.
    """
    try:
        if days < 1 or limit < 1:
            return {"status": "error", "message": "days and limit must be at least 1."}
        totals = units_sold(days)
        ranked = sorted(
            ({"name": p["name"], "units_sold": totals.get(p["sku"], 0)} for p in load_products()),
            key=lambda item: item["units_sold"],
            reverse=True,
        )
        return {"status": "success", "days": days, "top_sellers": ranked[:limit]}
    except Exception as e:
        logger.error(f"Error in get_top_sellers: {e}")
        return {"status": "error", "message": f"A problem occurred while reading sales: {str(e)}"}
