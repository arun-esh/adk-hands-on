from google.adk.agents.llm_agent import Agent

from ..tools.manager_role_tools import get_sales_summary, get_top_sellers
from ..tools.owner_role_tools import get_revenue
from ..tools.staff_role_tools import get_low_stock, get_product_details

# disallow_transfer_to_peers stops this agent from handing someone sideways to another role.
owner_agent = Agent(
    model='gemini-3.8-flash',
    name='owner_agent',
    description='Back-office assistant for the owner: products, stock, sales and revenue.',
    instruction=(
        "You are a back-office assistant for the owner of Maple Lane Corner Market. "
        "You can look up products and stock levels, list items that are low on stock, "
        "report units sold and best sellers, and work out revenue. "
        "You can only read information, never change anything. "
        "Always use your tools instead of guessing. All prices are in Canadian dollars ($)."
    ),
    tools=[get_product_details, get_low_stock, get_sales_summary, get_top_sellers, get_revenue],
    disallow_transfer_to_peers=True,
)
