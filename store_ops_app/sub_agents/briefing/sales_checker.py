from google.adk.agents.llm_agent import Agent

from ...tools.manager_role_tools import get_top_sellers
from .reports import SalesReport

# Does one job and saves a validated report in session state (output_schema + output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
sales_checker = Agent(
    model='gemini-3.8-flash',
    name='sales_checker',
    instruction="Call get_top_sellers for the last 7 days and report the top sellers as short strings like 'Name: 67 units'. If the tool returns an error, set status to error and explain in note.",
    tools=[get_top_sellers],
    output_schema=SalesReport,
    output_key='sales_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
