import logging
from typing import Any, Dict

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Mock database of registered users. Demo data only: the passwords are fake
# and stored in plain text on purpose.
db = {
    "maya": {"password": "owner123", "first_name": "Maya", "last_name": "Tremblay", "role": "owner", "active": True},
    "daniel": {"password": "manager123", "first_name": "Daniel", "last_name": "Roy", "role": "manager", "active": True},
    "sam": {"password": "staff123", "first_name": "Sam", "last_name": "Patel", "role": "staff", "active": True},
    "priya": {"password": "staff456", "first_name": "Priya", "last_name": "Nguyen", "role": "staff", "active": True},
    "luc": {"password": "staff789", "first_name": "Luc", "last_name": "Gagnon", "role": "staff", "active": False},
}


def verify_user(username: str, password: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Checks a username and password against the list of registered users.

    Args:
        username: The username the person typed (e.g., 'maya').
        password: The password the person typed.
        tool_context: Supplied by ADK (not by the model); used to remember who signed in.

    Returns:
        A dictionary with a status ('success', 'denied', 'inactive' or 'error'),
        a verified flag, the person's name and role when the login is correct,
        and a short message for the agent.
    """
    try:
        user = db.get(username.strip().lower())

        # Same answer for "no such user" and "wrong password", so nobody can
        # use this tool to find out which usernames exist.
        if user is None or user["password"] != password:
            return {
                "status": "denied",
                "verified": False,
                "message": "Wrong username or password.",
            }

        if not user["active"]:
            return {
                "status": "inactive",
                "verified": False,
                "message": "This account is switched off.",
            }

        # Written by this code, not by the model. The role guards read it later.
        tool_context.state["user_role"] = user["role"]
        tool_context.state["user_name"] = user["first_name"]

        return {
            "status": "success",
            "verified": True,
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"],
            "message": f"Success: {user['first_name']} is signed in as {user['role']}.",
        }

    except Exception as e:
        # Never log the password.
        logger.error(f"Error in verify_user: {e}")
        return {
            "status": "error",
            "verified": False,
            "message": f"A problem occurred while checking the login: {str(e)}",
        }
