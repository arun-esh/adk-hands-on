"""The supplier's own stock list. It lives here, not in the store's data: a different company."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Demo data only. Prices are what the supplier charges the store, per unit, in Canadian dollars.
CATALOGUE = {
    "Toblerone": {"available": 500, "unit_cost": 1.40, "lead_days": 2},
    "CARAMILK Salted Caramel": {"available": 320, "unit_cost": 1.10, "lead_days": 2},
    "Dairyland 2% Ultrafiltered Chocolate Partly Skimmed Milk": {"available": 80, "unit_cost": 2.60, "lead_days": 1},
    "Milkyroll": {"available": 210, "unit_cost": 0.95, "lead_days": 2},
    "Golden Ring": {"available": 0, "unit_cost": 1.20, "lead_days": 14},   # backordered on purpose
    "Unsalted mixed nuts": {"available": 150, "unit_cost": 3.10, "lead_days": 3},
    "Purple yam(ube) ice bar": {"available": 60, "unit_cost": 1.60, "lead_days": 4},
    "Apple cinnamon oatmeal cereal baby": {"available": 400, "unit_cost": 3.40, "lead_days": 3},
    "Dark Chocolate With Sea Salt And Almonds (Owl)": {"available": 120, "unit_cost": 2.20, "lead_days": 3},
    "Unsweet. Vanilla Almond Bev. Shelf-stable.": {"available": 240, "unit_cost": 2.30, "lead_days": 3},
}


def check_availability(item_name: str) -> Dict[str, Any]:
    """
    Looks up an item in the supplier's catalogue.

    Args:
        item_name: Part of the item name (e.g., 'Golden Ring').

    Returns:
        A dictionary with a status ('success', 'not_found' or 'error') and, on success, the matching
        items with units available, unit cost (CAD) and lead time in days.
    """
    try:
        matches = [
            {"name": name, **info}
            for name, info in CATALOGUE.items()
            if item_name.strip().lower() in name.lower()
        ]
        if not matches:
            return {"status": "not_found", "message": f"We do not carry '{item_name}'."}
        return {"status": "success", "matches": matches}
    except Exception as e:
        logger.error(f"Error in check_availability: {e}")
        return {"status": "error", "message": f"A problem occurred while checking the catalogue: {str(e)}"}
