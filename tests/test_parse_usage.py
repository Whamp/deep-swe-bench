import json
import tempfile
import unittest
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from harness import parse_usage


def message(role="assistant", *, input_tokens=0, output_tokens=0, cache_read=0,
            cache_write=0, cost=0.0, content=None):
    msg = {"role": role, "content": content or []}
    if role == "assistant":
        msg["usage"] = {
            "input": input_tokens,
            "output": output_tokens,
            "cacheRead": cache_read,
            "cacheWrite": cache_write,
            "totalTokens": input_tokens + output_tokens + cache_read + cache_write,
            "cost": {"total": cost},
        }
    return {"type": "message", "message": msg}


def child_usage_attributed(*, input_tokens=0, output_tokens=0, cache_read=0,
                           cache_write=0, cost=0.0):
    total_tokens = input_tokens + output_tokens + cache_read + cache_write
    return {
        "type": "child_usage_attributed",
        "targetId": "parent-assistant",
        "childUsage": {
            "input": input_tokens,
            "output": output_tokens,
            "cacheRead": cache_read,
            "cacheWrite": cache_write,
            "totalTokens": total_tokens,
            "cost": {"total": cost},
        },
        "aggregateUsage": {
            "input": input_tokens,
            "output": output_tokens,
            "cacheRead": cache_read,
            "cacheWrite": cache_write,
            "totalTokens": total_tokens,
            "cost": {"total": cost},
        },
    }


def write_jsonl(path: Path, records, mtime_ns: int):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    # nanosecond mtimes make ordering deterministic across filesystems that support it.
    import os
    os.utime(path, ns=(mtime_ns, mtime_ns))


class ParseUsageWorkflowRunsTests(unittest.TestCase):
    def test_parse_workflow_runs_counts_persisted_subagent_usage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "workflows"
            runs = root / "projects" / "project-key" / "runs"
            runs.mkdir(parents=True)
            (runs / "run-1.json").write_text(json.dumps({
                "runId": "run-1",
                "status": "completed",
                "agents": [
                    {"label": "inventory", "status": "done", "model": "openai-codex/gpt-5.4-mini"},
                    {"label": "synthesis", "status": "done", "model": "openai-codex/gpt-5.5"},
                ],
                "tokenUsage": {
                    "input": 100,
                    "output": 20,
                    "cacheRead": 7,
                    "cacheWrite": 3,
                    "total": 130,
                    "cost": 0.42,
                },
            }))
            (runs / "run-2.json").write_text(json.dumps({
                "runId": "run-2",
                "status": "failed",
                "agents": [
                    {"label": "debug", "status": "error", "model": "openai-codex/gpt-5.4"},
                ],
                "tokenUsage": {"input": 5, "output": 2, "total": 7, "cost": 0.03},
            }))

            parsed = parse_usage.parse_workflow_runs(path=root)

            self.assertEqual(parsed["workflow_runs"], 2)
            self.assertEqual(parsed["workflow_completed_runs"], 1)
            self.assertEqual(parsed["workflow_failed_runs"], 1)
            self.assertEqual(parsed["workflow_agent_calls"], 3)
            self.assertEqual(parsed["workflow_input_tokens"], 105)
            self.assertEqual(parsed["workflow_output_tokens"], 22)
            self.assertEqual(parsed["workflow_cache_read_tokens"], 7)
            self.assertEqual(parsed["workflow_cache_write_tokens"], 3)
            self.assertEqual(parsed["workflow_total_tokens"], 137)
            self.assertAlmostEqual(parsed["workflow_cost_usd"], 0.45)
            self.assertEqual(parsed["combined_total_tokens"], 137)
            self.assertAlmostEqual(parsed["combined_cost_usd"], 0.45)
            self.assertEqual(parsed["workflow_models"], [
                "openai-codex/gpt-5.4",
                "openai-codex/gpt-5.4-mini",
                "openai-codex/gpt-5.5",
            ])

    def test_parse_combines_workflow_usage_with_executor_usage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            session = root / "session"
            session.mkdir()
            write_jsonl(session / "root.jsonl", [message(input_tokens=10, output_tokens=1, cost=0.11)], 1_000)
            runs = root / "pi-agent" / "workflows" / "projects" / "project-key" / "runs"
            runs.mkdir(parents=True)
            (runs / "workflow.json").write_text(json.dumps({
                "runId": "workflow",
                "status": "completed",
                "agents": [{"label": "worker", "status": "done", "model": "openai-codex/gpt-5.4"}],
                "tokenUsage": {"input": 30, "output": 4, "total": 34, "cost": 0.34},
            }))

            parsed = parse_usage.parse(session_dir=session, workflow_usage_path=root / "pi-agent" / "workflows")

            self.assertEqual(parsed["total_tokens"], 11)
            self.assertEqual(parsed["workflow_total_tokens"], 34)
            self.assertEqual(parsed["combined_total_tokens"], 45)
            self.assertAlmostEqual(parsed["cost_usd"], 0.11)
            self.assertAlmostEqual(parsed["workflow_cost_usd"], 0.34)
            self.assertAlmostEqual(parsed["combined_cost_usd"], 0.45)

    def test_parse_workflow_runs_raises_when_root_exists_without_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "workflows"
            root.mkdir()

            with self.assertRaises(FileNotFoundError):
                parse_usage.parse_workflow_runs(path=root)


class ParseUsageRecursiveSessionsTests(unittest.TestCase):
    def test_parse_separates_recursive_child_sessions_from_root_executor(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            root = session / "2026-07-02T00-00-03-000Z_root.jsonl"
            child1 = session / "trace_d1_c1.jsonl"
            child2 = session / "trace_d2_c2.jsonl"

            write_jsonl(child1, [message(input_tokens=10, output_tokens=2, cost=0.12)], 2_000)
            write_jsonl(child2, [message(input_tokens=20, output_tokens=3, cost=0.23)], 3_000)
            write_jsonl(root, [
                message(input_tokens=100, output_tokens=7, cost=1.07),
                message(input_tokens=50, output_tokens=5, cost=0.55,
                        content=[{"type": "toolCall", "name": "rlm_query"}]),
            ], 4_000)

            parsed = parse_usage.parse(session_dir=session)

            self.assertEqual(parsed["input_tokens"], 150)
            self.assertEqual(parsed["output_tokens"], 12)
            self.assertEqual(parsed["total_tokens"], 162)
            self.assertEqual(parsed["turns"], 2)
            self.assertEqual(parsed["tool_calls"], 1)

            self.assertEqual(parsed["recursive_child_calls"], 2)
            self.assertEqual(parsed["recursive_child_input_tokens"], 30)
            self.assertEqual(parsed["recursive_child_output_tokens"], 5)
            self.assertEqual(parsed["recursive_child_total_tokens"], 35)
            self.assertEqual(parsed["recursive_child_turns"], 2)
            self.assertAlmostEqual(parsed["recursive_child_cost_usd"], 0.35)
            self.assertEqual(parsed["combined_total_tokens"], 197)
            self.assertAlmostEqual(parsed["combined_cost_usd"], 1.97)

    def test_parse_uses_latest_root_attempt_and_only_its_recursive_children(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            old_root = session / "2026-07-02T00-00-01-000Z_old.jsonl"
            old_child = session / "oldtrace_d1_c1.jsonl"
            new_child = session / "newtrace_d1_c1.jsonl"
            new_root = session / "2026-07-02T00-00-04-000Z_new.jsonl"

            write_jsonl(old_child, [message(input_tokens=900, output_tokens=90, cost=9.90)], 1_000)
            write_jsonl(old_root, [message(input_tokens=1000, output_tokens=100, cost=11.00)], 2_000)
            write_jsonl(new_child, [message(input_tokens=30, output_tokens=4, cost=0.34)], 3_000)
            write_jsonl(new_root, [message(input_tokens=70, output_tokens=6, cost=0.76)], 4_000)

            parsed = parse_usage.parse(session_dir=session)

            self.assertEqual(parsed["input_tokens"], 70)
            self.assertEqual(parsed["output_tokens"], 6)
            self.assertEqual(parsed["total_tokens"], 76)
            self.assertEqual(parsed["recursive_child_calls"], 1)
            self.assertEqual(parsed["recursive_child_total_tokens"], 34)
            self.assertEqual(parsed["combined_total_tokens"], 110)

    def test_parse_prime_agent_child_usage_attributions(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            root = session / "2026-08-05T00-00-01-000Z_root.jsonl"
            write_jsonl(root, [
                message(input_tokens=100, output_tokens=7, cost=1.07),
                child_usage_attributed(input_tokens=30, output_tokens=5,
                                       cache_read=4, cost=0.39),
                child_usage_attributed(input_tokens=20, output_tokens=3,
                                       cache_write=2, cost=0.25),
            ], 1_000)

            parsed = parse_usage.parse(session_dir=session)

            self.assertEqual(parsed["total_tokens"], 107)
            self.assertEqual(parsed["recursive_child_calls"], 2)
            self.assertEqual(parsed["recursive_child_input_tokens"], 50)
            self.assertEqual(parsed["recursive_child_output_tokens"], 8)
            self.assertEqual(parsed["recursive_child_cache_read_tokens"], 4)
            self.assertEqual(parsed["recursive_child_cache_write_tokens"], 2)
            self.assertEqual(parsed["recursive_child_total_tokens"], 64)
            self.assertAlmostEqual(parsed["recursive_child_cost_usd"], 0.64)
            self.assertEqual(parsed["combined_total_tokens"], 171)
            self.assertAlmostEqual(parsed["combined_cost_usd"], 1.71)

    def test_parse_session_ignores_recursive_child_when_it_is_newer_than_root(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            root = session / "2026-07-02T00-00-01-000Z_root.jsonl"
            child = session / "trace_d1_c1.jsonl"

            write_jsonl(root, [message(input_tokens=11, output_tokens=1, cost=0.12)], 1_000)
            write_jsonl(child, [message(input_tokens=99, output_tokens=9, cost=1.08)], 2_000)

            parsed = parse_usage.parse_session(session_dir=session)

            self.assertEqual(parsed["total_tokens"], 12)
            self.assertEqual(parsed["input_tokens"], 11)
            self.assertEqual(parsed["output_tokens"], 1)


@given(st.lists(st.tuples(
    st.integers(min_value=0, max_value=1_000_000),
    st.integers(min_value=0, max_value=1_000_000),
    st.integers(min_value=0, max_value=1_000_000),
    st.integers(min_value=0, max_value=1_000_000),
), max_size=20))
def test_child_usage_attribution_totals_are_additive(usages):
    records = [message(input_tokens=1, output_tokens=1)]
    records.extend(
        child_usage_attributed(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read=cache_read,
            cache_write=cache_write,
        )
        for input_tokens, output_tokens, cache_read, cache_write in usages
    )

    parsed = parse_usage.parse_prime_agent_child_attributions(text="\n".join(
        json.dumps(record) for record in records
    ))

    assert parsed["recursive_child_calls"] == len(usages)
    assert parsed["recursive_child_total_tokens"] == sum(sum(usage) for usage in usages)


if __name__ == "__main__":
    unittest.main()
