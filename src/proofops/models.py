from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGING = "triaging"
    DIAGNOSING = "diagnosing"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    ROLLING_BACK = "rolling_back"
    RESOLVED = "resolved"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"

    @classmethod
    def terminal(cls) -> tuple["IncidentStatus", ...]:
        return (cls.RESOLVED, cls.ROLLED_BACK, cls.REJECTED)


@dataclass(slots=True)
class EvidenceItem:
    id: str
    source: str
    kind: str
    summary: str
    value: dict[str, Any]
    collected_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "kind": self.kind,
            "summary": self.summary,
            "value": self.value,
            "collected_at": self.collected_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceItem":
        return cls(**payload)


@dataclass(slots=True)
class AuditEvent:
    id: str
    sequence: int
    timestamp: str
    trace_id: str
    span_id: str
    agent_id: str
    skill_id: str
    action: str
    summary: str
    outcome: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    metrics: dict[str, float | int | str | bool] = field(default_factory=dict)
    previous_hash: str = "GENESIS"
    event_hash: str = ""

    def hash_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "action": self.action,
            "summary": self.summary,
            "outcome": self.outcome,
            "evidence": [item.to_dict() for item in self.evidence],
            "metrics": self.metrics,
            "previous_hash": self.previous_hash,
        }

    def compute_hash(self) -> str:
        canonical = json.dumps(
            self.hash_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def seal(self) -> "AuditEvent":
        self.event_hash = self.compute_hash()
        return self

    def to_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "event_hash": self.event_hash}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AuditEvent":
        data = dict(payload)
        data["evidence"] = [EvidenceItem.from_dict(item) for item in data.get("evidence", [])]
        return cls(**data)


@dataclass(slots=True)
class Approval:
    actor: str
    decision: str
    reason: str
    decided_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "actor": self.actor,
            "decision": self.decision,
            "reason": self.reason,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> "Approval":
        return cls(**payload)


@dataclass(slots=True)
class Incident:
    id: str
    scenario_id: str
    scenario_name: str
    service: str
    severity: str
    summary: str
    status: IncidentStatus
    created_at: str
    updated_at: str
    trace_id: str
    context: dict[str, Any] = field(default_factory=dict)
    approval: Approval | None = None
    events: list[AuditEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "service": self.service,
            "severity": self.severity,
            "summary": self.summary,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "trace_id": self.trace_id,
            "context": self.context,
            "approval": self.approval.to_dict() if self.approval else None,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Incident":
        data = dict(payload)
        data["status"] = IncidentStatus(data["status"])
        data["approval"] = Approval.from_dict(data["approval"]) if data.get("approval") else None
        data["events"] = [AuditEvent.from_dict(event) for event in data.get("events", [])]
        return cls(**data)

