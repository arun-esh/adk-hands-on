from google.adk.agents.llm_agent import Agent

from .revenue_alert import flag_low_revenue

# Fan in: reads the three reports from session state and writes the briefing.
briefing_writer = Agent(
    model='gemini-3.8-flash',
    name='briefing_writer',
    instruction=(
        "Write a short morning briefing for the owner of Maple Lane Corner Market, "
        "in 5 lines or fewer, using only these reports. "
        "If the alert is not empty, put it on the first line.\n"
        "Alert: {revenue_alert}\n"
        "Stock: {stock_report}\n"
        "Sales: {sales_report}\n"
        "Revenue: {revenue_report}"
    ),
    before_agent_callback=flag_low_revenue,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
