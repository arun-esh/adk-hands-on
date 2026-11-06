from google.adk.agents.llm_agent import Agent

from ...tools.staff_role_tools import get_low_stock

# Writes the draft and saves it in state. On later rounds it also sees the critic's notes.
reorder_writer = Agent(
    model='gemini-3.8-flash',
    name='reorder_writer',
    instruction=(
        "Write a short, polite reorder message to our supplier, under 80 words, in plain text. "
        "Call get_low_stock, then mention every low item by its exact name with how many are left. "
        "Notes from the reviewer to fix (ignore if empty): {critique?}"
    ),
    tools=[get_low_stock],
    output_key='reorder_draft',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
