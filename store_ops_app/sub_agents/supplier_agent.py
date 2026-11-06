import os

from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

# The supplier is another company's service. We only know its address.
# Start it first:  uvicorn supplier_service.a2a_app:a2a_app --port 8001
SUPPLIER_URL = os.environ.get("SUPPLIER_URL", "http://localhost:8001")

supplier_agent = RemoteA2aAgent(
    name='supplier_agent',
    description="Wholesale supplier: confirms availability, prices and lead times for a reorder message.",
    agent_card=SUPPLIER_URL + AGENT_CARD_WELL_KNOWN_PATH,
)
