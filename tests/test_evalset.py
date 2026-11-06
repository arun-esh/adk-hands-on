"""Checks that the eval files are valid ADK files, with no model calls.

This does NOT run the evals: `adk eval` calls the model. Run from the repo root:  python -m tests.test_evalset
"""
from pathlib import Path

from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet

if __name__ == "__main__":
    evalset = EvalSet.model_validate_json(Path("evals/store_ops.evalset.json").read_text())
    EvalConfig.model_validate_json(Path("evals/test_config.json").read_text())
    for c in evalset.eval_cases:
        calls = [u.name for inv in c.conversation for u in inv.intermediate_data.tool_uses]
        print(f"{c.eval_id}: {len(c.conversation)} turns, expects tools {calls}")
        assert "verify_user" in calls
    print("eval files are valid (not run: that needs model calls)")
