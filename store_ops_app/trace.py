import json
import os
import time
from pathlib import Path

from google.adk.plugins.base_plugin import BasePlugin


class TraceLog(BasePlugin):
    """Writes one JSON line per step: agent start/end, tool call, tool result.

    It records tool argument NAMES only, never the values: verify_user receives a password,
    and a trace file must not become the place where secrets end up.
    """

    def __init__(self, path=None):
        super().__init__(name="trace_log")
        self.path = Path(path or os.environ.get("TRACE_FILE", "traces/trace.jsonl"))

    def _write(self, **row):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row["t"] = round(time.time(), 3)
        with self.path.open("a") as f:
            f.write(json.dumps(row) + "\n")

    async def before_agent_callback(self, *, agent, callback_context):
        self._write(event="agent_start", agent=agent.name, role=callback_context.state.get("user_role"))

    async def after_agent_callback(self, *, agent, callback_context):
        self._write(event="agent_end", agent=agent.name)

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        self._write(event="tool_call", agent=tool_context.agent_name, tool=tool.name, arg_names=sorted(tool_args))

    async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
        status = result.get("status") if isinstance(result, dict) else None
        self._write(event="tool_result", agent=tool_context.agent_name, tool=tool.name, status=status)
