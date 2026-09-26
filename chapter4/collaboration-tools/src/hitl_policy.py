"""HITL 识别策略：让 Agent 知道何时需要人工介入的系统提示词与自查工具。

实验 4-5 的实验要求之一是"编写系统提示词让 Agent 识别何时需要 HITL，主动请求
确认或输入"。本模块实现该要求：

- ``HITL_SYSTEM_PROMPT``    —— 该系统提示词本体（角色定位、判定规则、超时与
  保守默认、标准化 JSON 输出），与 hitl_tools 的工具语义一一对应；
- ``assess_hitl_requirement`` —— 用真实 LLM 按提示词对给定操作分类
  （request_admin_approval / request_admin_input / proceed），通过 MCP 工具
  ``mcp_assess_hitl_requirement`` 暴露，Agent 可在行动前自查该不该请人类介入。

分类调用走 subagent_tools 的同一 LLM 客户端，并以 ``_record_call`` 落原始模型
收据（response.id / usage / latency）。解析失败一律 fail-closed 返回错误，
绝不输出臆造的判定。离线（未配置 LLM）时同样拒绝，而不是模拟判定。
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List

from subagent_tools import DEFAULT_MODEL, _get_client, _offline, _record_call

logger = logging.getLogger(__name__)

HITL_ACTIONS = ("request_admin_approval", "request_admin_input", "proceed")
POLICY_VERSION = "hitl_system_prompt_v1"

HITL_SYSTEM_PROMPT = """你是行动前的人工介入判定器（HITL triage Agent）。在执行任何操作前，你必须按下列规则判定应采取的协作动作，并主动请求人类确认或补充信息；凡命中规则就先请求，绝不能"先斩后奏"。

判定规则（按顺序匹配，命中即停）：
1. request_admin_approval —— 操作不可逆或对外部世界产生副作用时请求人类批准。例如：发布或公开内容、创建/合并 PR、删除数据、发送消息或邮件、付款或退款、修改权限与配置。此外，超出授权范围或金额阈值、策略本身模糊不清时，同样请求批准。
2. request_admin_input —— 执行所必需的关键信息缺失（如收件人、目标对象、选项范围、生效时间），且无法从给定上下文推断时，请求人类补充输入，而不是猜测默认值。
3. proceed —— 操作只读、可逆、无副作用，且所需信息完备时，直接执行，不必打扰人类。

超时与保守默认：发起任何人类请求时都应设置超时；超时未获响应时采用保守默认——未获批准的不可逆操作不执行，缺失的信息不臆造，必要时改走可逆路径或上报用户决定。

输出格式：只输出一个 JSON 数组，长度与待判断操作数一致，每个元素为：
{"id": "<操作 id>", "action": "request_admin_approval" | "request_admin_input" | "proceed", "rule": "<命中的规则序号与理由，一句话>"}
不要输出 JSON 之外的任何文字。"""


def _parse_decisions(content: str, expected_ids: List[str]) -> List[Dict[str, str]]:
    """Parse the model output into one decision per scenario (fail-closed)."""
    text = (content or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        raise ValueError("model output contains no JSON decision array")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, list):
        raise ValueError("model output must be a JSON array")

    by_id: Dict[str, Dict[str, str]] = {}
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("each decision must be a JSON object")
        item_id = item.get("id")
        if item_id not in expected_ids or item_id in by_id:
            raise ValueError(f"decision id {item_id!r} is not an unmatched scenario id")
        action = item.get("action")
        if action not in HITL_ACTIONS:
            raise ValueError(f"invalid HITL action {action!r}")
        rule = str(item.get("rule") or "").strip()
        if not rule:
            raise ValueError(f"decision {item_id!r} carries no rule citation")
        by_id[item_id] = {"id": item_id, "action": action, "rule": rule}
    if set(by_id) != set(expected_ids):
        raise ValueError("model did not classify every scenario exactly once")
    return [by_id[item_id] for item_id in expected_ids]


def _run_assessment(request: Dict[str, Any]):
    """One real model call; raw usage/latency evidence is checkpointed."""
    client = _get_client()
    started = time.perf_counter()
    response = client.chat.completions.create(**request)
    _record_call("hitl_policy_assessment", request, response, time.perf_counter() - started)
    return response


async def assess_hitl_requirement(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Classify each operation under ``HITL_SYSTEM_PROMPT`` with one real model call.

    Returns ``{"success": True, "policy", "model", "decisions": [...]}`` with one
    ``{"id", "action", "rule"}`` decision per input scenario. Any malformed
    output, missing LLM configuration, or duplicate/unknown id fails closed.
    """
    try:
        if not isinstance(scenarios, list) or not scenarios:
            return {"success": False, "error": "scenarios must be a non-empty list"}
        expected_ids = [
            str(item.get("id") or f"scenario_{index + 1}")
            for index, item in enumerate(scenarios)
        ]
        if _offline():
            return {
                "success": False,
                "error": "no LLM configured; HITL policy assessment is not simulated",
            }

        request = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": HITL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "待判断的操作：\n"
                    + json.dumps(
                        [
                            {"id": scenario_id, "description": str(item.get("description") or "")}
                            for scenario_id, item in zip(expected_ids, scenarios)
                        ],
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0.2,
            # Reasoning models spend completion budget on their reasoning first:
            # the retained run real_mcp_human_20260926_v3 truncated at 800
            # tokens with an empty content field (finish_reason "length"),
            # which the parser correctly rejected. 8000 leaves room for the
            # reasoning AND the JSON verdict (same remedy as Experiment 4-4).
            "max_tokens": 8000,
        }
        response = await asyncio.to_thread(_run_assessment, request)
        content = response.choices[0].message.content or ""
        decisions = _parse_decisions(content, expected_ids)
        return {
            "success": True,
            "policy": POLICY_VERSION,
            "model": DEFAULT_MODEL,
            "decisions": decisions,
        }
    except Exception as exc:  # noqa: BLE001 - fail closed with a readable error
        logger.error("assess_hitl_requirement failed: %s", exc)
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}
