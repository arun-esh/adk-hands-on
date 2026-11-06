from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool

from ..guards import require_role
from .briefing import briefing_agent
from .reorder import reorder_agent
from .supplier_agent import supplier_agent
from ..tools.manager_role_tools import get_sales_summary, get_top_sellers
from ..tools.owner_role_tools import get_revenue
from ..tools.staff_role_tools import get_low_stock, get_product_details

# before_agent_callback checks the signed-in role in code before this agent runs.
# disallow_transfer_to_peers stops this agent from handing someone sideways to another role.
owner_agent = Agent(
    model='gemini-3.8-flash',
    name='owner_agent',
    description='Back-office assistant for the owner: products, stock, sales and revenue.',
    instruction=(
        "You are a back-office assistant for the owner of Maple Lane Corner Market. "
        "You can look up products and stock levels, list items that are low on stock, "
        "report units sold and best sellers, and work out revenue. "
        "If the owner asks for a morning or daily briefing, call the briefing_agent tool and share what it returns. "
        "If the owner asks to draft a reorder message for the supplier, call the reorder_agent tool and share what it returns. "
        "If the owner asks to send a reorder message to the supplier, call the supplier_agent tool with the message and share its reply. "
        "You can only read information, never change anything. "
        "Always use your tools instead of guessing. All prices are in Canadian dollars ($)."
    ),
    tools=[get_product_details, get_low_stock, get_sales_summary, get_top_sellers, get_revenue,
           AgentTool(agent=briefing_agent), AgentTool(agent=reorder_agent), AgentTool(agent=supplier_agent)],
    before_agent_callback=require_role("owner"),
    disallow_transfer_to_peers=True,
)
