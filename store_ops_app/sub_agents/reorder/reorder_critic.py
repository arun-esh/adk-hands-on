from google.adk.agents.llm_agent import Agent
from google.adk.tools.exit_loop_tool import exit_loop

from ...tools.reorder_tools import check_reorder_items

# Splits the review in two. The exact part (is every item named?) is plain code in a tool.
# The fuzzy part (is the tone polite, is anything made up?) is the model's judgement.
reorder_critic = Agent(
    model='gemini-3.8-flash',
    name='reorder_critic',
    instruction=(
        "You review a reorder message to our supplier.\n"
        "Draft: {reorder_draft}\n"
        "First call check_reorder_items. If any items are missing, reply with one short line "
        "saying which to add. Also check the tone is polite and nothing is made up. "
        "If you find any problem, reply with one short line saying what to fix. "
        "If everything is fine, call exit_loop and say nothing else."
    ),
    tools=[check_reorder_items, exit_loop],
    output_key='critique',
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
