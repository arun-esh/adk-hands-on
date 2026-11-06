"""Checks the briefing pipeline with a fake model: no network, no model calls.

Proves: the three helpers run at the same time, their validated reports reach the writer
through session state, code can read report fields, and only the owner can start the pipeline.
Run from the repo root:  python -m tests.test_briefing
"""
import asyncio
import json
import time

from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from pydantic import ValidationError

from store_ops_app.sub_agents.briefing.briefing_agent import briefing_agent, gather_facts
from store_ops_app.sub_agents.briefing.briefing_writer import briefing_writer
from store_ops_app.sub_agents.briefing.reports import RevenueReport
from store_ops_app.sub_agents.briefing.revenue_alert import flag_low_revenue
from store_ops_app.sub_agents.briefing.revenue_checker import revenue_checker
from store_ops_app.sub_agents.briefing.sales_checker import sales_checker
from store_ops_app.sub_agents.briefing.stock_checker import stock_checker
from store_ops_app.sub_agents.owner_agent import owner_agent

DELAY = 0.6
STOCK = {"status": "ok", "low_items": ["cereal: 2 left"]}
SALES = {"status": "ok", "top_sellers": ["cereal: 67 units"]}
REVENUE_OK = {"status": "ok", "total_cad": 421.5}
REVENUE_ERROR = {"status": "error", "note": "Unable to retrieve total revenue for the last 7 days: sales database unreachable."}
REVENUE_LOW = {"status": "ok", "total_cad": 62.0}


class FakeLlm(BaseLlm):
    """Calls the agent's data tool once, then hands in its report the way ADK expects:
    through set_model_response when the agent has an output_schema."""
    model: str = "fake"
    answer: str = ""     # JSON report, or plain text for agents without a schema
    tool: str = ""

    async def generate_content_async(self, llm_request, stream=False):
        await asyncio.sleep(DELAY)
        parts = [p for c in llm_request.contents for p in (c.parts or [])]
        done = {p.function_response.name for p in parts if p.function_response}
        if self.tool and self.tool not in done:
            call = types.Part(function_call=types.FunctionCall(name=self.tool, args={}))
            yield LlmResponse(content=types.Content(role="model", parts=[call]))
            return
        if "set_model_response" in llm_request.tools_dict and "set_model_response" not in done:
            call = types.Part(function_call=types.FunctionCall(name="set_model_response", args=json.loads(self.answer)))
            yield LlmResponse(content=types.Content(role="model", parts=[call]))
            return
        responses = [p.function_response.response for p in parts if p.function_response]
        if responses and not self.answer:
            text = str(responses[-1])          # relay what the tool returned
        else:
            text = self.answer or str(llm_request.config.system_instruction)
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))


def fake_pipeline(revenue=REVENUE_OK):
    def fake(agent, answer="", tool=""):
        return agent.model_copy(update={"model": FakeLlm(answer=answer, tool=tool), "parent_agent": None})
    stock = fake(stock_checker, json.dumps(STOCK), "get_low_stock")
    sales = fake(sales_checker, json.dumps(SALES), "get_top_sellers")
    rev = fake(revenue_checker, json.dumps(revenue), "get_revenue")
    writer = fake(briefing_writer)
    return briefing_agent.model_copy(update={
        "sub_agents": [gather_facts.model_copy(update={"sub_agents": [stock, sales, rev], "parent_agent": None}), writer],
        "parent_agent": None,
    })


def fake_owner():
    """The real owner_agent, with a fake model that calls the briefing tool, and the fake pipeline inside it."""
    tools = [t for t in owner_agent.tools if not isinstance(t, AgentTool)] + [AgentTool(agent=fake_pipeline())]
    return owner_agent.model_copy(update={
        "model": FakeLlm(answer="", tool="briefing_agent"), "tools": tools, "parent_agent": None})


async def run(agent, role):
    runner = InMemoryRunner(agent=agent, app_name="briefing_test")
    state = {"user_role": role} if role else {}
    session = await runner.session_service.create_session(app_name="briefing_test", user_id="u", state=state)
    msg = types.Content(role="user", parts=[types.Part(text="morning briefing")])
    authors, last = [], ""
    start = time.time()
    async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
        if e.content and e.content.parts and any(p.text for p in e.content.parts):
            authors.append(e.author)
            last = "".join(p.text or "" for p in e.content.parts)
    final = await runner.session_service.get_session(app_name="briefing_test", user_id="u", session_id=session.id)
    return authors, last, time.time() - start, final.state


def test_owner_runs_in_parallel_and_state_flows():
    authors, last, took, state = asyncio.run(run(fake_pipeline(), "owner"))
    print(f"owner: {took:.2f}s, replies from {authors}")
    assert took < 4 * 2 * DELAY * 0.7, f"not parallel: {took:.2f}s"   # one after another this would take about 3 x 2 x DELAY + DELAY = 4.2 s
    assert authors[-1] == "briefing_writer"
    # The saved reports are validated dicts, not sentences.
    assert state["stock_report"] == STOCK, state.get("stock_report")
    assert state["sales_report"] == SALES, state.get("sales_report")
    assert state["revenue_report"] == REVENUE_OK, state.get("revenue_report")
    for text in ("cereal: 2 left", "cereal: 67 units", "421.5"):
        assert text in last, (text, last)


class FakeCallbackContext:
    def __init__(self, revenue_report):
        self.state = {"revenue_report": revenue_report}


def alert_for(report):
    ctx = FakeCallbackContext(report)
    flag_low_revenue(ctx)
    return ctx.state["revenue_alert"]


def test_alert_reads_fields():
    assert alert_for(REVENUE_OK) == ""
    assert alert_for(REVENUE_LOW) == "ALERT: revenue looks low ($62 this week)."
    print("alert reads report fields")


def test_error_report_is_not_a_false_alarm():
    """The step05 KNOWN BREAK: an error mentioning '7 days' no longer looks like $7 of revenue."""
    assert alert_for(REVENUE_ERROR) == ""
    authors, last, _, state = asyncio.run(run(fake_pipeline(revenue=REVENUE_ERROR), "owner"))
    assert state["revenue_report"]["status"] == "error", state["revenue_report"]
    assert "ALERT" not in last, last
    print("error report -> no false alarm (step05 break fixed)")


def test_schema_rejects_free_text():
    try:
        RevenueReport.model_validate_json("Unable to retrieve total revenue for the last 7 days.")
    except ValidationError:
        print("free text is rejected by the schema")
        return
    raise AssertionError("free text should not validate")


def test_owner_agent_calls_briefing_as_a_tool():
    authors, last, took, _ = asyncio.run(run(fake_owner(), "owner"))
    print(f"owner_agent -> briefing tool: {took:.2f}s, replies from {authors}")
    assert authors[-1] == "owner_agent", authors          # owner_agent keeps the conversation
    assert "421.5" in last, last


def test_only_owner_can_start():
    for role in ("staff", "manager", None):
        authors, last, _, _ = asyncio.run(run(fake_pipeline(), role))
        assert last == "Sorry, that isn't available for your role.", (role, last)
        assert authors == ["briefing_agent"], (role, authors)
        print(f"blocked  briefing_agent role={role}")


if __name__ == "__main__":
    test_owner_runs_in_parallel_and_state_flows()
    test_alert_reads_fields()
    test_error_report_is_not_a_false_alarm()
    test_schema_rejects_free_text()
    test_owner_agent_calls_briefing_as_a_tool()
    test_only_owner_can_start()
    print("briefing checks passed (fake model, no network)")
