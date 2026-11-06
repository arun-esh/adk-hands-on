"""Tools added for the owner role: revenue. Only the owner gets these."""
import logging
from typing import Any, Dict

from ._data import load_products, units_sold

logger = logging.getLogger(__name__)


def get_revenue(days: int = 7) -> Dict[str, Any]:
    """
    Works out revenue (units sold x shelf price, in Canadian dollars) over the last few days.
    Owner only.

    Args:
        days: How many days to look back, before the store's today (default 7).

    Returns:
        A dictionary with a status ('success' or 'error'), the total revenue and the revenue
        for each product that sold, biggest first.
    """
    try:
        if days < 1:
            return {"status": "error", "message": "days must be at least 1."}
        totals = units_sold(days)
        by_product = [
            {"name": p["name"], "units_sold": totals[p["sku"]], "revenue": round(totals[p["sku"]] * p["price"], 2)}
            for p in load_products()
            if p["sku"] in totals
        ]
        by_product.sort(key=lambda item: item["revenue"], reverse=True)
        return {
            "status": "success",
            "days": days,
            "currency": "CAD",
            "total_revenue": round(sum(item["revenue"] for item in by_product), 2),
            "by_product": by_product,
        }
    except Exception as e:
        logger.error(f"Error in get_revenue: {e}")
        return {"status": "error", "message": f"A problem occurred while working out revenue: {str(e)}"}
