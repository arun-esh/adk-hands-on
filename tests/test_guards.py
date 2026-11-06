"""Checks the role guards with no model calls.

A guard that says "no" returns before the agent's model is ever called, so the
blocked cases run through the real ADK Runner without touching the network.
Run from the repo root:  python -m tests.test_guards
"""
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from store_ops_app.sub_agents.manager_agent import manager_agent
from store_ops_app.sub_agents.owner_agent import owner_agent
from store_ops_app.sub_agents.staff_agent import staff_agent
from store_ops_app.tools.gatekeeper_tools import verify_user


class FakeToolContext:
    def __init__(self):
        self.state = {}


def test_verify_user_writes_role():
    ctx = FakeToolContext()
    verify_user("sam", "staff123", ctx)
    assert ctx.state == {"user_role": "staff", "user_name": "Sam"}, ctx.state
    for bad in (("sam", "wrong"), ("nobody", "x"), ("luc", "staff789")):
        c = FakeToolContext()
        verify_user(*bad, c)
        assert c.state == {}, (bad, c.state)


async def ask(agent, role):
    runner = InMemoryRunner(agent=agent, app_name="guard_test")
    state = {"user_role": role} if role else {}
    session = await runner.session_service.create_session(
        app_name="guard_test", user_id="u", state=state
    )
    msg = types.Content(role="user", parts=[types.Part(text="show me revenue")])
    texts = []
    async for event in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        if event.content and event.content.parts:
            texts += [p.text for p in event.content.parts if p.text]
    return texts


def test_blocked_paths():
    cases = [
        (owner_agent, "staff"), (owner_agent, "manager"), (owner_agent, None),
        (manager_agent, "staff"), (manager_agent, "owner"), (manager_agent, None),
        (staff_agent, "manager"), (staff_agent, "owner"), (staff_agent, None),
    ]
    for agent, role in cases:
        out = asyncio.run(ask(agent, role))
        assert out == ["Sorry, that isn't available for your role."], (agent.name, role, out)
        print(f"blocked  {agent.name:14} role={role}")


def test_allowed_paths():
    for agent, role in ((staff_agent, "staff"), (manager_agent, "manager"), (owner_agent, "owner")):
        ctx = FakeToolContext()
        ctx.state["user_role"] = role
        (callback,) = agent.canonical_before_agent_callbacks
        assert callback(ctx) is None, (agent.name, role)
        print(f"allowed  {agent.name:14} role={role}")


if __name__ == "__main__":
    test_verify_user_writes_role()
    print("verify_user writes the role to state only on success")
    test_blocked_paths()
    test_allowed_paths()
    print("all blocked-path checks passed (no model calls)")
