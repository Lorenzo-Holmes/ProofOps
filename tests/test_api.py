from __future__ import annotations

import unittest

from proofops.api import ApiApp
from proofops.engine import ProofOpsEngine


class ApiAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = ApiApp(ProofOpsEngine())

    def test_health_and_catalog_endpoints(self) -> None:
        health = self.app.dispatch("GET", "/api/health")
        agents = self.app.dispatch("GET", "/api/agents")
        skills = self.app.dispatch("GET", "/api/skills")

        self.assertEqual(health.status, 200)
        self.assertEqual(health.payload["status"], "ok")
        self.assertEqual(len(agents.payload["items"]), 6)
        self.assertGreaterEqual(len(skills.payload["items"]), 7)

    def test_create_advance_approve_and_read_incident(self) -> None:
        created = self.app.dispatch(
            "POST", "/api/incidents", {"scenario_id": "coupon-null-regression"}
        )
        self.assertEqual(created.status, 201)
        incident_id = created.payload["incident"]["id"]

        current = created
        while current.payload["incident"]["status"] != "awaiting_approval":
            current = self.app.dispatch("POST", f"/api/incidents/{incident_id}/advance", {})
            self.assertEqual(current.status, 200)

        blocked = self.app.dispatch("POST", f"/api/incidents/{incident_id}/advance", {})
        self.assertEqual(blocked.status, 409)
        self.assertEqual(blocked.payload["error"]["code"], "approval_required")

        approved = self.app.dispatch(
            "POST",
            f"/api/incidents/{incident_id}/approve",
            {"actor": "demo-judge"},
        )
        self.assertEqual(approved.status, 200)
        self.assertEqual(approved.payload["incident"]["status"], "executing")

        fetched = self.app.dispatch("GET", f"/api/incidents/{incident_id}")
        self.assertEqual(fetched.status, 200)
        self.assertEqual(fetched.payload["incident"]["approval"]["actor"], "demo-judge")

    def test_unknown_scenario_and_route_return_structured_errors(self) -> None:
        unknown_scenario = self.app.dispatch(
            "POST", "/api/incidents", {"scenario_id": "not-real"}
        )
        missing_route = self.app.dispatch("GET", "/api/not-a-route")

        self.assertEqual(unknown_scenario.status, 404)
        self.assertEqual(unknown_scenario.payload["error"]["code"], "scenario_not_found")
        self.assertEqual(missing_route.status, 404)
        self.assertEqual(missing_route.payload["error"]["code"], "route_not_found")


if __name__ == "__main__":
    unittest.main()

