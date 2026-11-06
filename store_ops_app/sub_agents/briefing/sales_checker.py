from google.adk.agents.llm_agent import Agent

from ...tools.manager_role_tools import get_top_sellers

# Does one job and saves its answer in session state (output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
sales_checker = Agent(
    model='gemini-3.8-flash',
    name='sales_checker',
    instruction="Call get_top_sellers for the last 7 days. Reply with at most 3 short lines: the top sellers and units sold.",
    tools=[get_top_sellers],
    output_key='sales_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
