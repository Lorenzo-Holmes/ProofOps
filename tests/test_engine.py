from __future__ import annotations

import unittest

from proofops.engine import ApprovalRequired, ProofOpsEngine
from proofops.models import IncidentStatus


class ProofOpsEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ProofOpsEngine()

    def _advance_to_approval(self, incident_id: str):
        incident = self.engine.get_incident(incident_id)
        while incident.status != IncidentStatus.AWAITING_APPROVAL:
            incident = self.engine.advance(incident_id)
        return incident

    def test_create_incident_records_detection_event_and_valid_hash_chain(self) -> None:
        incident = self.engine.create_incident("coupon-null-regression")

        self.assertEqual(incident.status, IncidentStatus.DETECTED)
        self.assertEqual(len(incident.events), 1)
        self.assertEqual(incident.events[0].action, "incident.detected")
        self.assertTrue(self.engine.verify_audit(incident.id))

    def test_incident_cannot_execute_before_human_approval(self) -> None:
        incident = self.engine.create_incident("coupon-null-regression")
        waiting = self._advance_to_approval(incident.id)

        self.assertEqual(waiting.status, IncidentStatus.AWAITING_APPROVAL)
        with self.assertRaises(ApprovalRequired):
            self.engine.advance(incident.id)

    def test_approved_safe_remediation_reaches_resolved(self) -> None:
        incident = self.engine.create_incident("coupon-null-regression")
        self._advance_to_approval(incident.id)
        executing = self.engine.approve(incident.id, actor="judge@example.local")
        self.assertEqual(executing.status, IncidentStatus.EXECUTING)

        while executing.status not in IncidentStatus.terminal():
            executing = self.engine.advance(incident.id)

        self.assertEqual(executing.status, IncidentStatus.RESOLVED)
        self.assertEqual(executing.approval.actor, "judge@example.local")
        self.assertTrue(self.engine.verify_audit(incident.id))

    def test_failed_verification_triggers_rollback(self) -> None:
        incident = self.engine.create_incident("inventory-timeout-cascade")
        self._advance_to_approval(incident.id)
        current = self.engine.approve(incident.id, actor="incident-commander")

        visited = [current.status]
        while current.status not in IncidentStatus.terminal():
            current = self.engine.advance(incident.id)
            visited.append(current.status)

        self.assertIn(IncidentStatus.ROLLING_BACK, visited)
        self.assertEqual(current.status, IncidentStatus.ROLLED_BACK)
        self.assertTrue(any(event.action == "deployment.rollback" for event in current.events))

    def test_rejection_closes_incident_without_execution(self) -> None:
        incident = self.engine.create_incident("coupon-null-regression")
        self._advance_to_approval(incident.id)

        rejected = self.engine.reject(incident.id, actor="release-manager", reason="change freeze")

        self.assertEqual(rejected.status, IncidentStatus.REJECTED)
        self.assertFalse(any(event.agent_id == "execution-agent" for event in rejected.events))

    def test_metrics_are_computed_from_incident_outcomes(self) -> None:
        safe = self.engine.create_incident("coupon-null-regression")
        self._advance_to_approval(safe.id)
        current = self.engine.approve(safe.id, actor="judge")
        while current.status not in IncidentStatus.terminal():
            current = self.engine.advance(safe.id)

        metrics = self.engine.metrics()
        self.assertEqual(metrics["incidents_total"], 1)
        self.assertEqual(metrics["resolved_total"], 1)
        self.assertEqual(metrics["audit_integrity_percent"], 100.0)
        self.assertGreater(metrics["trace_coverage_percent"], 0)


if __name__ == "__main__":
    unittest.main()

