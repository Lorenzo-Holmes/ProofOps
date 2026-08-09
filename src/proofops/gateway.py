from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import EvidenceItem, Incident
from .scenarios import Scenario


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ToolResult:
    summary: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    metrics: dict[str, float | int | str | bool] = field(default_factory=dict)


class FixtureToolGateway:
    """Deterministic MCP-equivalent gateway for local competition fixtures."""

    def invoke(self, operation: str, scenario: Scenario, incident: Incident) -> ToolResult:
        handlers = {
            "evidence.collect": self._collect,
            "change.correlate": self._correlate,
            "hypothesis.test": self._diagnose,
            "remediation.plan": self._plan,
            "sandbox.apply": self._execute,
            "recovery.verify": self._verify,
            "deployment.rollback": self._rollback,
        }
        return handlers[operation](scenario, incident)

    def _evidence(self, source: str, kind: str, summary: str, value: dict[str, Any]) -> EvidenceItem:
        return EvidenceItem(
            id=f"evd-{uuid4().hex[:10]}",
            source=source,
            kind=kind,
            summary=summary,
            value=value,
            collected_at=utc_now(),
        )

    def _collect(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        items = [
            self._evidence(item["source"], item["kind"], item["summary"], item["value"])
            for item in scenario.evidence_fixture
        ]
        return ToolResult(
            f"已从{len(items)}个来源建立标准化证据包。",
            items,
            {"sources": len(items), "evidence_completeness_percent": 100.0},
        )

    def _correlate(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        item = self._evidence(
            "repository", "correlation", f"高相关变更：{scenario.correlated_change}",
            {"change": scenario.correlated_change, "correlation": 0.93},
        )
        return ToolResult("已将异常时间窗与发布记录关联。", [item], {"candidates": 1})

    def _diagnose(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        item = self._evidence(
            "diagnostic-runner", "hypothesis-test", scenario.root_cause,
            {
                "tested": list(scenario.candidate_hypotheses),
                "selected": scenario.candidate_hypotheses[-1],
                "confidence": 0.88,
                "counter_evidence_count": len(scenario.candidate_hypotheses) - 1,
            },
        )
        return ToolResult("竞争性假设检验完成，已保留支持证据与反证。", [item], {"hypotheses_tested": len(scenario.candidate_hypotheses)})

    def _plan(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        item = self._evidence(
            "remediation-planner", "change-plan", scenario.remediation,
            {"patch": scenario.remediation, "rollback": scenario.rollback_plan, "risk_score": scenario.risk_score},
        )
        return ToolResult("最小修复与对应回滚计划已生成，等待人工审批。", [item], {"risk_score": scenario.risk_score})

    def _execute(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        item = self._evidence(
            "ci-sandbox", "test-run", "补丁已在隔离环境构建并执行回归套件。",
            {"tests_total": 48, "tests_passed": 48, "candidate": scenario.correlated_change},
        )
        return ToolResult("沙箱执行完成，进入独立恢复验证。", [item], {"tests_total": 48, "tests_passed": 48})

    def _verify(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        passed = scenario.verification_outcome == "pass"
        verdict = "恢复指标与业务断言均通过。" if passed else "业务准确率断言失败，拒绝验收。"
        item = self._evidence(
            "independent-verifier", "verification", verdict,
            {"baseline": scenario.baseline, "candidate": scenario.candidate_metrics, "passed": passed},
        )
        return ToolResult(verdict, [item], {"passed": passed, "checks": len(scenario.baseline)})

    def _rollback(self, scenario: Scenario, _incident: Incident) -> ToolResult:
        item = self._evidence(
            "deployment", "rollback", scenario.rollback_plan,
            {"idempotent": True, "health_check": "passed"},
        )
        return ToolResult("已回滚至验证版本并通过二次健康检查。", [item], {"rollback_verified": True})

