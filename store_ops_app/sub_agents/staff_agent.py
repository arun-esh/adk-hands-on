from google.adk.agents.llm_agent import Agent

from ..guards import require_role
from ..tools.staff_role_tools import get_low_stock, get_product_details

# before_agent_callback checks the signed-in role in code before this agent runs.
# disallow_transfer_to_peers stops this agent from handing someone sideways to another role.
staff_agent = Agent(
    model='gemini-3.8-flash',
    name='staff_agent',
    description='Back-office assistant for staff: products and stock.',
    instruction=(
        "You are a back-office assistant for a staff member of Maple Lane Corner Market. "
        "You can look up products and stock levels and list items that are low on stock. "
        "You cannot see sales or revenue: if asked, say that is not available to staff. "
        "You can only read information, never change anything. "
        "Always use your tools instead of guessing. All prices are in Canadian dollars ($)."
    ),
    tools=[get_product_details, get_low_stock],
    before_agent_callback=require_role("staff"),
    disallow_transfer_to_peers=True,
)
