"""Checks the A2A hop with a real local server and a fake model: no external network, no model calls.

Starts the supplier as an A2A server on localhost, calls it through RemoteA2aAgent, and checks that
the supplier's own tool ran on the other side and that our session state did not cross the boundary.
Run from the repo root:  python -m tests.test_a2a
"""
import asyncio
import json
import socket
import threading
import time

import httpx
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from google.adk.tools.agent_tool import AgentTool

from store_ops_app.sub_agents.owner_agent import owner_agent
from supplier_service.agent import make_supplier


class SupplierFake(BaseLlm):
    """Calls check_availability('Golden Ring'), then replies with the tool result and what it was sent."""
    model: str = "fake"

    async def generate_content_async(self, llm_request, stream=False):
        parts = [p for c in llm_request.contents for p in (c.parts or [])]
        results = [p.function_response.response for p in parts if p.function_response]
        if not results:
            call = types.FunctionCall(name="check_availability", args={"item_name": "Golden Ring"})
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=call)]))
            return
        received = " ".join(p.text for p in parts if p.text)
        text = f"TOOL RESULT: {json.dumps(results[-1])} | SENT TO SUPPLIER: {received}"
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))


class OwnerFake(BaseLlm):
    """Calls the supplier_agent tool, then relays what came back."""
    model: str = "fake"

    async def generate_content_async(self, llm_request, stream=False):
        parts = [p for c in llm_request.contents for p in (c.parts or [])]
        results = [p.function_response.response for p in parts if p.function_response]
        if not results:
            call = types.FunctionCall(name="supplier_agent", args={"request": "Please send 20 Golden Ring."})
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=call)]))
            return
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=str(results[-1]))]))


async def owner_calls_supplier(url):
    remote = RemoteA2aAgent(name="supplier_agent", agent_card=url + AGENT_CARD_WELL_KNOWN_PATH)
    tools = [t for t in owner_agent.tools if getattr(getattr(t, "agent", None), "name", "") != "supplier_agent"]
    owner = owner_agent.model_copy(update={"model": OwnerFake(), "tools": tools + [AgentTool(agent=remote)], "parent_agent": None})
    runner = InMemoryRunner(agent=owner, app_name="a2a_owner_test")
    session = await runner.session_service.create_session(app_name="a2a_owner_test", user_id="u", state={"user_role": "owner"})
    msg = types.Content(role="user", parts=[types.Part(text="send the reorder to the supplier")])
    out = []
    async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        if e.content and e.content.parts:
            out += [p.text for p in e.content.parts if p.text]
    return " ".join(out)


def free_port():
    with socket.socket() as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def start_supplier(port):
    app = to_a2a(make_supplier(model=SupplierFake()), port=port)
    server = uvicorn.Server(uvicorn.Config(app, host="localhost", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    url = f"http://localhost:{port}"
    for _ in range(100):
        try:
            if httpx.get(url + AGENT_CARD_WELL_KNOWN_PATH, timeout=1).status_code == 200:
                return server, url
        except httpx.HTTPError:
            time.sleep(0.1)
    raise RuntimeError("supplier did not start")


async def call_supplier(url, message, state):
    remote = RemoteA2aAgent(name="supplier_agent", agent_card=url + AGENT_CARD_WELL_KNOWN_PATH)
    runner = InMemoryRunner(agent=remote, app_name="a2a_test")
    session = await runner.session_service.create_session(app_name="a2a_test", user_id="u", state=state)
    msg = types.Content(role="user", parts=[types.Part(text=message)])
    out = []
    async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        if e.content and e.content.parts:
            out += [p.text for p in e.content.parts if p.text]
    return " ".join(out)


if __name__ == "__main__":
    server, url = start_supplier(free_port())
    try:
        card = httpx.get(url + AGENT_CARD_WELL_KNOWN_PATH).json()
        print("agent card:", card["name"], "-", card["description"][:60], "...")
        assert card["name"] == "supplier_agent"

        reply = asyncio.run(call_supplier(url, "Please send 20 Golden Ring.", {"user_role": "owner", "user_name": "Maya"}))
        print("reply:", reply[:200])
        assert '"lead_days": 14' in reply, reply                       # the supplier's own tool ran, on the other side
        assert "Please send 20 Golden Ring." in reply, reply           # our message crossed
        assert "user_role" not in reply and "Maya" not in reply, reply  # our session state did not
        owner_reply = asyncio.run(owner_calls_supplier(url))
        assert '"lead_days": 14' in owner_reply, owner_reply
        print("owner_agent -> supplier_agent tool -> A2A: the supplier's answer came back")
        print("A2A: card served, remote tool ran, message crossed, session state stayed home")
    finally:
        server.should_exit = True
