"""Focused tests for the HITL-recognition system prompt and its probe tool."""

import asyncio
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import hitl_policy

SCENARIOS = [
    {"id": "irreversible_publish", "description": "Publish the run to a GitHub PR"},
    {"id": "missing_recipient", "description": "Send a refund notice, channel unknown"},
    {"id": "readonly_lookup", "description": "Read the refund threshold table"},
]

EXPECTED_CONTENT = json.dumps(
    [
        {"id": "irreversible_publish", "action": "request_admin_approval",
         "rule": "1 — 对外发布不可逆，先批准"},
        {"id": "missing_recipient", "action": "request_admin_input",
         "rule": "2 — 缺少收件渠道，请补充"},
        {"id": "readonly_lookup", "action": "proceed",
         "rule": "3 — 只读且信息完备"},
    ],
    ensure_ascii=False,
)


def _response(content: str):
    return SimpleNamespace(
        id="chatcmpl-test-0001",
        model="test-model",
        choices=[SimpleNamespace(finish_reason="stop",
                                 message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=60, total_tokens=180),
    )


class _FakeClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: _response(content))
        )


def _assess(content: str, scenarios=None):
    with (
        patch.object(hitl_policy, "_offline", return_value=False),
        patch.object(hitl_policy, "_get_client", return_value=_FakeClient(content)),
    ):
        return asyncio.run(
            hitl_policy.assess_hitl_requirement(
                SCENARIOS if scenarios is None else scenarios
            )
        )


def test_prompt_names_every_action_and_conservative_default() -> None:
    prompt = hitl_policy.HITL_SYSTEM_PROMPT
    for action in hitl_policy.HITL_ACTIONS:
        assert action in prompt
    assert "主动请求" in prompt
    assert "超时" in prompt and "保守默认" in prompt
    assert "JSON 数组" in prompt


def test_assess_parses_decisions_and_checkpoints_receipt(tmp_path) -> None:
    receipt_path = tmp_path / "llm_receipts.json"
    with patch.dict(os.environ, {"COLLAB_LLM_RECEIPT_PATH": str(receipt_path)}):
        result = _assess(EXPECTED_CONTENT)
    assert result["success"] is True
    assert result["policy"] == hitl_policy.POLICY_VERSION
    assert [decision["action"] for decision in result["decisions"]] == [
        "request_admin_approval",
        "request_admin_input",
        "proceed",
    ]
    rows = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert rows[0]["purpose"] == "hitl_policy_assessment"
    assert rows[0]["response"]["id"] == "chatcmpl-test-0001"
    assert rows[0]["usage"]["total_tokens"] == 180
    assert rows[0]["latency_seconds"] >= 0


def test_assess_tolerates_fenced_json_and_reordering() -> None:
    reordered = (
        '[{"id": "readonly_lookup", "action": "proceed", "rule": "3 — 只读"},'
        ' {"id": "irreversible_publish", "action": "request_admin_approval", "rule": "1 — 不可逆"},'
        ' {"id": "missing_recipient", "action": "request_admin_input", "rule": "2 — 缺信息"}]'
    )
    result = _assess("```json\n" + reordered + "\n```")
    assert result["success"] is True
    assert [decision["id"] for decision in result["decisions"]] == [
        "irreversible_publish",
        "missing_recipient",
        "readonly_lookup",
    ]


def test_assess_fails_closed_on_non_json_output() -> None:
    result = _assess("I think all of these are fine to proceed with.")
    assert result["success"] is False
    assert "JSON" in result["error"]


def test_assess_fails_closed_on_invalid_action() -> None:
    bad = EXPECTED_CONTENT.replace("request_admin_input", "do_it_anyway", 1)
    result = _assess(bad)
    assert result["success"] is False
    assert "invalid HITL action" in result["error"]


def test_assess_fails_closed_on_missing_rule() -> None:
    bad = EXPECTED_CONTENT.replace('"rule": "3 — 只读且信息完备"', '"rule": ""')
    result = _assess(bad)
    assert result["success"] is False
    assert "rule citation" in result["error"]


def test_assess_fails_closed_on_duplicate_ids() -> None:
    bad = EXPECTED_CONTENT.replace('"id": "readonly_lookup"', '"id": "missing_recipient"', 1)
    result = _assess(bad)
    assert result["success"] is False


def test_assess_refuses_without_llm_instead_of_simulating() -> None:
    with patch.object(hitl_policy, "_offline", return_value=True):
        result = asyncio.run(hitl_policy.assess_hitl_requirement(SCENARIOS))
    assert result["success"] is False
    assert "not simulated" in result["error"]


def test_assess_rejects_empty_scenario_list() -> None:
    result = _assess(EXPECTED_CONTENT, scenarios=[])
    assert result["success"] is False
    assert "non-empty" in result["error"]
