from google.adk.agents.llm_agent import Agent

from ...tools.staff_role_tools import get_low_stock

# Does one job and saves its answer in session state (output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
stock_checker = Agent(
    model='gemini-3.8-flash',
    name='stock_checker',
    instruction="Call get_low_stock. Reply with at most 3 short lines: which products are low and how many are left.",
    tools=[get_low_stock],
    output_key='stock_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
