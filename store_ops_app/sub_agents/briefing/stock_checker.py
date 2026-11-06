from google.adk.agents.llm_agent import Agent

from ...tools.staff_role_tools import get_low_stock
from .reports import StockReport

# Does one job and saves a validated report in session state (output_schema + output_key).
# It never talks to the user or to the other helpers, so it is safe to run at the same time.
stock_checker = Agent(
    model='gemini-3.8-flash',
    name='stock_checker',
    instruction="Call get_low_stock and report the low items as short strings like 'Name: 3 left'. If the tool returns an error, set status to error and explain in note.",
    tools=[get_low_stock],
    output_schema=StockReport,
    output_key='stock_report',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
