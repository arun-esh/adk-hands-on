from google.adk.agents.llm_agent import Agent

from .catalogue import check_availability


def make_supplier(model='gemini-3.8-flash'):
    """Builds the supplier agent. A function so tests can plug in a fake model."""
    return Agent(
        model=model,
        name='supplier_agent',
        description="Wholesale supplier for Maple Lane Corner Market: confirms availability, prices and lead times for a reorder.",
        instruction=(
            "You are the order desk at a wholesale supplier. You will receive a reorder message from a store. "
            "For every item it mentions, call check_availability, then reply with one short line per item: "
            "units available, unit cost in Canadian dollars and lead time in days. "
            "If an item is not available, say so and give the lead time. "
            "You know nothing about the store's staff or roles, and you never ask for passwords."
        ),
        tools=[check_availability],
    )


root_agent = make_supplier()
