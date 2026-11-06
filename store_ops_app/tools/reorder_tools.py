"""Plain-code check used by the reorder critic: the exact part of the review."""
import logging
from typing import Any, Dict

from google.adk.tools import ToolContext

from ._data import load_products

logger = logging.getLogger(__name__)


def check_reorder_items(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Checks that the saved reorder draft mentions every item that is low on stock, by name.

    Returns:
        A dictionary with a status ('success' or 'error'), all_present (True when nothing is missing)
        and the list of low-stock item names that the draft does not mention.
    """
    try:
        draft = (tool_context.state.get("reorder_draft") or "").lower()
        low = [p["name"] for p in load_products() if p["stock"] <= p["reorder_level"]]
        missing = [name for name in low if name.lower() not in draft]
        return {"status": "success", "all_present": not missing, "missing": missing}
    except Exception as e:
        logger.error(f"Error in check_reorder_items: {e}")
        return {"status": "error", "message": f"A problem occurred while checking the draft: {str(e)}"}
