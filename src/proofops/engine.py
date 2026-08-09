from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from .gateway import FixtureToolGateway, ToolResult
from .models import Approval, AuditEvent, Incident, IncidentStatus
from .scenarios import SCENARIOS, Scenario, list_scenarios
from .store import IncidentStore, MemoryIncidentStore


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProofOpsError(Exception):
    code = "proofops_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ScenarioNotFound(ProofOpsError):
    code = "scenario_not_found"
    http_status = 404


class IncidentNotFound(ProofOpsError):
    code = "incident_not_found"
    http_status = 404


class ApprovalRequired(ProofOpsError):
    code = "approval_required"
    http_status = 409


class InvalidTransition(ProofOpsError):
    code = "invalid_transition"
    http_status = 409


class InvalidInput(ProofOpsError):
    code = "invalid_input"
    http_status = 400


class ProofOpsEngine:
    def __init__(
        self,
        store: IncidentStore | None = None,
        gateway: FixtureToolGateway | None = None,
        clock: Callable[[], str] = utc_now,
    ) -> None:
        self.store = store or MemoryIncidentStore()
        self.gateway = gateway or FixtureToolGateway()
        self.clock = clock

    def scenarios(self) -> list[dict]:
        return list_scenarios()

    def create_incident(self, scenario_id: str) -> Incident:
        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            raise ScenarioNotFound(f"未知故障样本：{scenario_id}")
        now = self.clock()
        incident = Incident(
            id=f"inc-{uuid4().hex[:10]}",
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            service=scenario.service,
            severity=scenario.severity,
            summary=scenario.summary,
            status=IncidentStatus.DETECTED,
            created_at=now,
            updated_at=now,
            trace_id=f"trc-{uuid4().hex}",
            context={
                "trigger": scenario.trigger,
                "candidate_hypotheses": list(scenario.candidate_hypotheses),
                "risk_score": scenario.risk_score,
                "target_outcome": "resolved" if scenario.verification_outcome == "pass" else "rolled_back",
            },
        )
        self._append_event(
            incident, "incident-commander", "incident_intake", "incident.detected",
            f"已接收{scenario.service}事件：{scenario.trigger}", "completed",
            ToolResult("事件已标准化。", metrics={"severity": scenario.severity}),
        )
        self.store.save(incident)
        return incident

    def get_incident(self, incident_id: str) -> Incident:
        incident = self.store.get(incident_id)
        if not incident:
            raise IncidentNotFound(f"事件不存在：{incident_id}")
        return incident

    def list_incidents(self) -> list[Incident]:
        return self.store.list()

    def advance(self, incident_id: str) -> Incident:
        incident = self.get_incident(incident_id)
        scenario = SCENARIOS[incident.scenario_id]
        status = incident.status

        if status == IncidentStatus.DETECTED:
            self._run_step(incident, scenario, IncidentStatus.TRIAGING, "evidence-agent", "collect_evidence", "evidence.collect", "evidence.collected")
        elif status == IncidentStatus.TRIAGING:
            self._run_step(incident, scenario, IncidentStatus.DIAGNOSING, "evidence-agent", "correlate_change", "change.correlate", "change.correlated")
        elif status == IncidentStatus.DIAGNOSING:
            self._run_step(incident, scenario, IncidentStatus.PLANNING, "diagnosis-agent", "test_hypothesis", "hypothesis.test", "diagnosis.verified")
        elif status == IncidentStatus.PLANNING:
            self._run_step(incident, scenario, IncidentStatus.AWAITING_APPROVAL, "remediation-agent", "plan_remediation", "remediation.plan", "remediation.proposed")
        elif status == IncidentStatus.AWAITING_APPROVAL:
            raise ApprovalRequired("高风险写操作需要人工批准。")
        elif status == IncidentStatus.EXECUTING:
            self._run_step(incident, scenario, IncidentStatus.VERIFYING, "execution-agent", "apply_in_sandbox", "sandbox.apply", "sandbox.executed")
        elif status == IncidentStatus.VERIFYING:
            result = self.gateway.invoke("recovery.verify", scenario, incident)
            passed = bool(result.metrics.get("passed"))
            incident.status = IncidentStatus.RESOLVED if passed else IncidentStatus.ROLLING_BACK
            self._append_event(
                incident, "verification-agent", "verify_recovery",
                "verification.accepted" if passed else "verification.failed",
                result.summary, "completed" if passed else "failed", result,
            )
            self._save(incident)
        elif status == IncidentStatus.ROLLING_BACK:
            self._run_step(incident, scenario, IncidentStatus.ROLLED_BACK, "execution-agent", "execute_rollback", "deployment.rollback", "deployment.rollback")
        else:
            raise InvalidTransition(f"终态事件不能继续推进：{status.value}")
        return self.get_incident(incident_id)

    def approve(self, incident_id: str, actor: str, reason: str = "approved for sandbox execution") -> Incident:
        if not actor or not actor.strip():
            raise InvalidInput("审批人不能为空。")
        incident = self.get_incident(incident_id)
        if incident.status != IncidentStatus.AWAITING_APPROVAL:
            raise InvalidTransition("只有等待审批的事件可以批准。")
        now = self.clock()
        incident.approval = Approval(actor.strip(), "approved", reason, now)
        incident.status = IncidentStatus.EXECUTING
        self._append_event(
            incident, "incident-commander", "plan_remediation", "approval.granted",
            f"{actor.strip()}已批准受控沙箱执行。", "completed",
            ToolResult("人工审批已记录。", metrics={"human_approved": True}),
        )
        self._save(incident)
        return self.get_incident(incident_id)

    def reject(self, incident_id: str, actor: str, reason: str) -> Incident:
        if not actor or not reason:
            raise InvalidInput("驳回需要审批人和原因。")
        incident = self.get_incident(incident_id)
        if incident.status != IncidentStatus.AWAITING_APPROVAL:
            raise InvalidTransition("只有等待审批的事件可以驳回。")
        now = self.clock()
        incident.approval = Approval(actor.strip(), "rejected", reason.strip(), now)
        incident.status = IncidentStatus.REJECTED
        self._append_event(
            incident, "incident-commander", "plan_remediation", "approval.rejected",
            f"{actor.strip()}驳回执行：{reason.strip()}", "completed",
            ToolResult("处置在写操作前安全终止。", metrics={"human_approved": False}),
        )
        self._save(incident)
        return self.get_incident(incident_id)

    def verify_audit(self, incident_id: str) -> bool:
        incident = self.get_incident(incident_id)
        previous = "GENESIS"
        for expected_sequence, event in enumerate(incident.events, start=1):
            if event.sequence != expected_sequence or event.previous_hash != previous:
                return False
            if event.event_hash != event.compute_hash():
                return False
            previous = event.event_hash
        return True

    def metrics(self) -> dict[str, float | int]:
        incidents = self.list_incidents()
        events = [event for incident in incidents for event in incident.events]
        valid = sum(1 for incident in incidents if self.verify_audit(incident.id))
        traced = sum(1 for event in events if event.trace_id and event.span_id)
        total = len(incidents)
        return {
            "incidents_total": total,
            "active_total": sum(1 for item in incidents if item.status not in IncidentStatus.terminal()),
            "resolved_total": sum(1 for item in incidents if item.status == IncidentStatus.RESOLVED),
            "rolled_back_total": sum(1 for item in incidents if item.status == IncidentStatus.ROLLED_BACK),
            "rejected_total": sum(1 for item in incidents if item.status == IncidentStatus.REJECTED),
            "human_approvals_total": sum(1 for item in incidents if item.approval and item.approval.decision == "approved"),
            "audit_integrity_percent": round(valid / total * 100, 1) if total else 100.0,
            "trace_coverage_percent": round(traced / len(events) * 100, 1) if events else 100.0,
            "events_total": len(events),
        }

    def _run_step(
        self,
        incident: Incident,
        scenario: Scenario,
        next_status: IncidentStatus,
        agent_id: str,
        skill_id: str,
        operation: str,
        action: str,
    ) -> None:
        result = self.gateway.invoke(operation, scenario, incident)
        incident.status = next_status
        self._append_event(incident, agent_id, skill_id, action, result.summary, "completed", result)
        self._save(incident)

    def _append_event(
        self,
        incident: Incident,
        agent_id: str,
        skill_id: str,
        action: str,
        summary: str,
        outcome: str,
        result: ToolResult,
    ) -> None:
        previous = incident.events[-1].event_hash if incident.events else "GENESIS"
        event = AuditEvent(
            id=f"evt-{uuid4().hex[:12]}",
            sequence=len(incident.events) + 1,
            timestamp=self.clock(),
            trace_id=incident.trace_id,
            span_id=f"spn-{uuid4().hex[:16]}",
            agent_id=agent_id,
            skill_id=skill_id,
            action=action,
            summary=summary,
            outcome=outcome,
            evidence=result.evidence,
            metrics=result.metrics,
            previous_hash=previous,
        ).seal()
        incident.events.append(event)
        incident.updated_at = event.timestamp

    def _save(self, incident: Incident) -> None:
        incident.updated_at = self.clock()
        self.store.save(incident)

