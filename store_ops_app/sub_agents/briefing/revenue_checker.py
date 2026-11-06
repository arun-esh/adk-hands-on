from google.adk.agents.llm_agent import Agent

from ...tools.owner_role_tools import get_revenue
from .reports import RevenueReport

# Does one job and saves a validated report in session state (output_schema + output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
revenue_checker = Agent(
    model='gemini-3.8-flash',
    name='revenue_checker',
    instruction="Call get_revenue for the last 7 days and report the total revenue in Canadian dollars as total_cad. If the tool returns an error, set status to error, leave total_cad empty and explain in note.",
    tools=[get_revenue],
    output_schema=RevenueReport,
    output_key='revenue_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
