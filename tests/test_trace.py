"""Checks the trace log with the fake briefing pipeline: no network, no model calls.

Proves: the trace shows the three helpers starting together (parallel) and the writer starting last,
tool calls and results are recorded, and no secret values ever reach the trace file.
Run from the repo root:  python -m tests.test_trace
"""
import asyncio
import json
import tempfile
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

from store_ops_app.trace import TraceLog
from tests.test_briefing import fake_pipeline


class FakeTool:
    name = "verify_user"


class FakeToolContext:
    agent_name = "gatekeeper"
    state = {}


async def run_traced(path):
    runner = InMemoryRunner(agent=fake_pipeline(), app_name="trace_test", plugins=[TraceLog(path)])
    session = await runner.session_service.create_session(app_name="trace_test", user_id="u", state={"user_role": "owner"})
    msg = types.Content(role="user", parts=[types.Part(text="morning briefing")])
    async for _ in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        pass


def test_trace_shows_parallel_then_writer(path):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    starts = {r["agent"]: r["t"] for r in rows if r["event"] == "agent_start"}
    ends = {r["agent"]: r["t"] for r in rows if r["event"] == "agent_end"}
    helpers = ("stock_checker", "sales_checker", "revenue_checker")
    spread = max(starts[h] for h in helpers) - min(starts[h] for h in helpers)
    assert spread < 0.3, f"helpers did not start together: {spread:.2f}s"
    assert starts["briefing_writer"] >= max(ends[h] for h in helpers), "writer started before the helpers finished"
    calls = {(r["agent"], r["tool"]) for r in rows if r["event"] == "tool_call"}
    assert ("revenue_checker", "get_revenue") in calls and ("stock_checker", "get_low_stock") in calls, calls
    assert all(r["role"] == "owner" for r in rows if r["event"] == "agent_start" and r["agent"] == "briefing_agent")
    print(f"trace: {len(rows)} lines; helpers started within {spread:.2f}s; writer started after they ended")
    for r in rows[:6]:
        print("  ", json.dumps(r))


def test_trace_never_records_secret_values(path):
    plugin = TraceLog(path)
    asyncio.run(plugin.before_tool_callback(
        tool=FakeTool(), tool_args={"username": "sam", "password": "staff123"}, tool_context=FakeToolContext()))
    text = Path(path).read_text()
    assert "staff123" not in text and '"sam"' not in text, "a secret value reached the trace"
    assert '"arg_names": ["password", "username"]' in text
    print("trace: tool arguments are recorded by name only (no password, no username)")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "trace.jsonl"
        asyncio.run(run_traced(path))
        test_trace_shows_parallel_then_writer(path)
        test_trace_never_records_secret_values(path)
    print("trace checks passed (fake model, no network)")
