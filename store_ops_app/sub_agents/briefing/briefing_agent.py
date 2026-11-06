from google.adk.agents import ParallelAgent, SequentialAgent

from ...guards import require_role
from .briefing_writer import briefing_writer
from .revenue_checker import revenue_checker
from .sales_checker import sales_checker
from .stock_checker import stock_checker

# Fan out: all three helpers run at the same time.
gather_facts = ParallelAgent(
    name='gather_facts',
    sub_agents=[stock_checker, sales_checker, revenue_checker],
)

# Order is fixed: gather first, then write. The owner guard applies to the whole pipeline.
briefing_agent = SequentialAgent(
    name='briefing_agent',
    description="Builds the owner's morning briefing: low stock, top sellers and revenue.",
    sub_agents=[gather_facts, briefing_writer],
    before_agent_callback=require_role("owner"),
)
