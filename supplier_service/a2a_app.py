"""Serves the supplier agent over A2A.

Run it in its own terminal (the store's agent connects to it by URL):
    uvicorn supplier_service.a2a_app:a2a_app --port 8001
"""
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .agent import root_agent

a2a_app = to_a2a(root_agent, port=8001)
