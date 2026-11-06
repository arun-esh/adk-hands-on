from google.adk.agents import LoopAgent
from google.genai import types

from ...guards import require_role
from .reorder_critic import reorder_critic
from .reorder_writer import reorder_writer


def publish_draft(callback_context):
    """After the loop ends, hand back the last draft (plain code, no extra model call)."""
    draft = callback_context.state.get("reorder_draft")
    if draft:
        return types.Content(role="model", parts=[types.Part(text=draft)])
    return None


# Write, review, repeat. The loop stops when the critic calls exit_loop, or after 3 rounds.
reorder_agent = LoopAgent(
    name='reorder_agent',
    description="Drafts a reorder message to the supplier for low-stock items, reviewed by a critic.",
    sub_agents=[reorder_writer, reorder_critic],
    max_iterations=3,
    before_agent_callback=require_role("owner"),
    after_agent_callback=publish_draft,
)
