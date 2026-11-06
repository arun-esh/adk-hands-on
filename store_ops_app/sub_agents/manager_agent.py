from google.adk.agents.llm_agent import Agent

from ..guards import require_role
from ..tools.manager_role_tools import get_sales_summary, get_top_sellers
from ..tools.staff_role_tools import get_low_stock, get_product_details

# before_agent_callback checks the signed-in role in code before this agent runs.
# disallow_transfer_to_peers stops this agent from handing someone sideways to another role.
manager_agent = Agent(
    model='gemini-3.8-flash',
    name='manager_agent',
    description='Back-office assistant for managers: products, stock and sales.',
    instruction=(
        "You are a back-office assistant for a manager of Maple Lane Corner Market. "
        "You can look up products and stock levels, list items that are low on stock, "
        "and report units sold and best sellers. "
        "You cannot see revenue: if asked, say that is only available to the owner. "
        "You can only read information, never change anything. "
        "Always use your tools instead of guessing. All prices are in Canadian dollars ($)."
    ),
    tools=[get_product_details, get_low_stock, get_sales_summary, get_top_sellers],
    before_agent_callback=require_role("manager"),
    disallow_transfer_to_peers=True,
)
