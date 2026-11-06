"""Checks the briefing pipeline with a fake model: no network, no model calls.

Proves three things: the three helpers run at the same time, their reports reach
the writer through session state, and only the owner can start the pipeline.
Run from the repo root:  python -m tests.test_briefing
"""
import asyncio
import time

from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from store_ops_app.sub_agents.owner_agent import owner_agent
from store_ops_app.sub_agents.briefing.briefing_agent import briefing_agent, gather_facts
from store_ops_app.sub_agents.briefing.briefing_writer import briefing_writer
from store_ops_app.sub_agents.briefing.revenue_alert import flag_low_revenue
from store_ops_app.sub_agents.briefing.revenue_checker import revenue_checker
from store_ops_app.sub_agents.briefing.sales_checker import sales_checker
from store_ops_app.sub_agents.briefing.stock_checker import stock_checker

DELAY = 0.6


class FakeLlm(BaseLlm):
    """Calls the agent's tool once (if it has one), waits, then answers with a fixed line."""
    model: str = "fake"
    answer: str = ""
    tool: str = ""

    async def generate_content_async(self, llm_request, stream=False):
        await asyncio.sleep(DELAY)
        parts = [p for c in llm_request.contents for p in (c.parts or [])]
        if self.tool and not any(p.function_response for p in parts):
            call = types.Part(function_call=types.FunctionCall(name=self.tool, args={}))
            yield LlmResponse(content=types.Content(role="model", parts=[call]))
            return
        responses = [p.function_response.response for p in parts if p.function_response]
        if responses and not self.answer:
            text = str(responses[-1])          # relay what the tool returned
        else:
            text = self.answer or str(llm_request.config.system_instruction)
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))


def fake_pipeline(revenue="REVENUE: $421"):
    def fake(agent, answer="", tool=""):
        return agent.model_copy(update={"model": FakeLlm(answer=answer, tool=tool), "parent_agent": None})
    stock = fake(stock_checker, "STOCK: cereal low", "get_low_stock")
    sales = fake(sales_checker, "SALES: cereal top", "get_top_sellers")
    rev = fake(revenue_checker, revenue, "get_revenue")
    writer = fake(briefing_writer)
    return briefing_agent.model_copy(update={
        "sub_agents": [gather_facts.model_copy(update={"sub_agents": [stock, sales, rev], "parent_agent": None}), writer],
        "parent_agent": None,
    })


def fake_owner():
    """The real owner_agent, with a fake model that calls the briefing tool, and the fake pipeline inside it."""
    from google.adk.tools.agent_tool import AgentTool
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
    return authors, last, time.time() - start


def test_owner_runs_in_parallel_and_state_flows():
    authors, last, took = asyncio.run(run(fake_pipeline(), "owner"))
    print(f"owner: {took:.2f}s, replies from {authors}")
    # 3 helpers + writer, each DELAY twice (tool call, then answer). Serial would be >= 4 x 2 x DELAY.
    assert took < 4 * 2 * DELAY * 0.7, f"not parallel: {took:.2f}s"
    assert authors[-1] == "briefing_writer"
    for report in ("STOCK: cereal low", "SALES: cereal top", "REVENUE: $421"):
        assert report in last, (report, last)


def test_owner_agent_calls_briefing_as_a_tool():
    runner_agent = fake_owner()
    authors, last, took = asyncio.run(run(runner_agent, "owner"))
    print(f"owner_agent -> briefing tool: {took:.2f}s, replies from {authors}")
    assert authors[-1] == "owner_agent", authors          # owner_agent keeps the conversation
    assert "REVENUE: $421" in last, last


class FakeCallbackContext:
    def __init__(self, revenue_report):
        self.state = {"revenue_report": revenue_report}


def alert_for(text):
    ctx = FakeCallbackContext(text)
    flag_low_revenue(ctx)
    return ctx.state["revenue_alert"]


def test_alert_reads_a_normal_report():
    assert alert_for("Total revenue: $421.50 over the last 7 days.") == "", "should not alert on $421.50"
    assert alert_for("Total revenue: $62.00.") == "ALERT: revenue looks low ($62 this week)."
    print("alert reads a normal revenue sentence")


def test_known_break_free_text_false_alarm():
    """KNOWN BREAK (fixed in step06): the helper reports an error, the code finds the '7' in '7 days'."""
    text = "Unable to retrieve total revenue for the last 7 days: sales database unreachable."
    alert = alert_for(text)
    print(f"KNOWN BREAK: error text -> {alert!r}")
    assert alert == "ALERT: revenue looks low ($7 this week).", alert


def test_known_break_end_to_end():
    text = "Unable to retrieve total revenue for the last 7 days: sales database unreachable."
    authors, last, _ = asyncio.run(run(fake_pipeline(revenue=text), "owner"))
    assert "ALERT: revenue looks low ($7 this week)." in last, last
    print("KNOWN BREAK reaches the writer's instruction")


def test_only_owner_can_start():
    for role in ("staff", "manager", None):
        authors, last, _ = asyncio.run(run(fake_pipeline(), role))
        assert last == "Sorry, that isn't available for your role.", (role, last)
        assert authors == ["briefing_agent"], (role, authors)
        print(f"blocked  briefing_agent role={role}")


if __name__ == "__main__":
    test_owner_runs_in_parallel_and_state_flows()
    test_alert_reads_a_normal_report()
    test_known_break_free_text_false_alarm()
    test_known_break_end_to_end()
    test_owner_agent_calls_briefing_as_a_tool()
    test_only_owner_can_start()
    print("briefing checks passed (fake model, no network)")
