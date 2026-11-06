"""Checks the writer + critic loop with scripted fake models: no network, no model calls.

Proves: a draft missing items is sent back and fixed, the critic's exit_loop stops the loop early,
the loop is capped at 3 rounds, the plain-code check finds missing items, and only the owner can start it.
Run from the repo root:  python -m tests.test_reorder
"""
import asyncio

from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from store_ops_app.sub_agents.reorder.reorder_agent import reorder_agent
from store_ops_app.sub_agents.reorder.reorder_critic import reorder_critic
from store_ops_app.sub_agents.reorder.reorder_writer import reorder_writer
from store_ops_app.tools._data import load_products
from store_ops_app.tools.reorder_tools import check_reorder_items

LOW = [p["name"] for p in load_products() if p["stock"] <= p["reorder_level"]]
PARTIAL = f"Hello, please send more {LOW[0]} (0 left). Thanks!"
FULL = "Hello, please send more: " + "; ".join(LOW) + ". Thank you!"


class ScriptedLlm(BaseLlm):
    """Plays a fixed script: 'call:<tool>' makes a tool call, 'text:<words>' answers. Repeats the script if `cycle`."""
    model: str = "fake"
    script: list[str]
    pos: list[int]
    cycle: bool = False

    async def generate_content_async(self, llm_request, stream=False):
        i = self.pos[0]
        self.pos[0] += 1
        step = self.script[i % len(self.script)] if self.cycle else self.script[min(i, len(self.script) - 1)]
        kind, _, value = step.partition(":")
        part = (types.Part(function_call=types.FunctionCall(name=value, args={})) if kind == "call"
                else types.Part(text=value))
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


def fake_loop(writer_script, critic_script, critic_cycle=False):
    w_llm = ScriptedLlm(script=writer_script, pos=[0])
    c_llm = ScriptedLlm(script=critic_script, pos=[0], cycle=critic_cycle)
    w = reorder_writer.model_copy(update={"model": w_llm, "parent_agent": None})
    c = reorder_critic.model_copy(update={"model": c_llm, "parent_agent": None})
    loop = reorder_agent.model_copy(update={"sub_agents": [w, c], "parent_agent": None})
    return loop, w_llm.pos, c_llm.pos


async def run(agent, role="owner"):
    runner = InMemoryRunner(agent=agent, app_name="reorder_test")
    state = {"user_role": role} if role else {}
    session = await runner.session_service.create_session(app_name="reorder_test", user_id="u", state=state)
    msg = types.Content(role="user", parts=[types.Part(text="draft a reorder message")])
    texts = []
    async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        if e.content and e.content.parts:
            for p in e.content.parts:
                if p.text:
                    texts.append((e.author, p.text))
    return texts


class FakeCtx:
    def __init__(self, draft):
        self.state = {"reorder_draft": draft}


def test_check_tool_finds_missing_items():
    r = check_reorder_items(FakeCtx(PARTIAL))
    assert r["all_present"] is False and r["missing"] == LOW[1:], r
    assert check_reorder_items(FakeCtx(FULL))["all_present"] is True
    print(f"check tool: partial draft is missing {len(LOW) - 1} of {len(LOW)} items; full draft passes")


def test_critic_sends_draft_back_then_approves():
    loop, w_pos, c_pos = fake_loop(
        ["call:get_low_stock", "text:" + PARTIAL, "text:" + FULL],
        ["call:check_reorder_items", "text:Add: " + ", ".join(LOW[1:]),
         "call:check_reorder_items", "call:exit_loop"],
    )
    texts = asyncio.run(run(loop))
    drafts = [t for a, t in texts if a == "reorder_writer"]
    assert drafts == [PARTIAL, FULL], drafts
    assert texts[-1] == ("reorder_agent", FULL), texts[-1]          # the published result is the fixed draft
    assert w_pos[0] == 3, f"writer ran more than 2 rounds: {w_pos[0]}"
    print(f"loop: 2 rounds, critic approved, published the full draft")


def test_loop_stops_after_three_rounds():
    loop, w_pos, c_pos = fake_loop(
        ["call:get_low_stock", "text:d1", "text:d2", "text:d3", "text:d4"],
        ["call:check_reorder_items", "text:Still missing items"], critic_cycle=True,
    )
    texts = asyncio.run(run(loop))
    drafts = [t for a, t in texts if a == "reorder_writer"]
    assert drafts == ["d1", "d2", "d3"], drafts
    assert texts[-1] == ("reorder_agent", "d3"), texts[-1]
    print("loop: critic never approves, stops after 3 rounds")


def test_only_owner_can_start():
    for role in ("staff", "manager", None):
        loop, _, _ = fake_loop(["text:x"], ["text:y"])
        texts = asyncio.run(run(loop, role))
        assert texts == [("reorder_agent", "Sorry, that isn't available for your role.")], (role, texts)
        print(f"blocked  reorder_agent role={role}")


if __name__ == "__main__":
    test_check_tool_finds_missing_items()
    test_critic_sends_draft_back_then_approves()
    test_loop_stops_after_three_rounds()
    test_only_owner_can_start()
    print("reorder checks passed (fake models, no network)")
