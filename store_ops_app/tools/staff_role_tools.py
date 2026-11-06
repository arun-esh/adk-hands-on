"""Tools for the staff role: products and stock. Managers and the owner get these too."""
import logging
from typing import Any, Dict

from ._data import load_products

logger = logging.getLogger(__name__)


def get_product_details(name: str) -> Dict[str, Any]:
    """
    Finds products whose name contains the given text.

    Args:
        name: Part of the product name (e.g., 'milk' or 'Toblerone').

    Returns:
        A dictionary with a status ('success', 'not_found' or 'error') and, on success,
        a list of matching products with brand, category, price, stock and reorder level.
    """
    try:
        matches = [p for p in load_products() if name.strip().lower() in p["name"].lower()]
        if not matches:
            return {"status": "not_found", "message": f"No product name contains '{name}'."}
        return {"status": "success", "matches": matches}
    except Exception as e:
        logger.error(f"Error in get_product_details: {e}")
        return {"status": "error", "message": f"A problem occurred while looking up products: {str(e)}"}


def get_low_stock() -> Dict[str, Any]:
    """
    Lists products whose stock is at or below their reorder level.

    Returns:
        A dictionary with a status ('success' or 'error') and the list of low-stock products.
    """
    try:
        low = [p for p in load_products() if p["stock"] <= p["reorder_level"]]
        return {"status": "success", "count": len(low), "low_stock": low}
    except Exception as e:
        logger.error(f"Error in get_low_stock: {e}")
        return {"status": "error", "message": f"A problem occurred while checking stock: {str(e)}"}
