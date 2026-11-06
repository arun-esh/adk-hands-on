from google.adk.agents.llm_agent import Agent

from ...tools.owner_role_tools import get_revenue

# Does one job and saves its answer in session state (output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
revenue_checker = Agent(
    model='gemini-3.8-flash',
    name='revenue_checker',
    instruction="Call get_revenue for the last 7 days. Reply with one short line: total revenue in Canadian dollars.",
    tools=[get_revenue],
    output_key='revenue_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
