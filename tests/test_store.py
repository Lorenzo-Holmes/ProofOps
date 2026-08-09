from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from proofops.engine import ProofOpsEngine
from proofops.store import JsonIncidentStore


class JsonIncidentStoreTests(unittest.TestCase):
    def test_incident_round_trip_preserves_events_and_enum_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonIncidentStore(Path(directory))
            engine = ProofOpsEngine(store=store)
            created = engine.create_incident("coupon-null-regression")
            engine.advance(created.id)

            reloaded = ProofOpsEngine(store=JsonIncidentStore(Path(directory))).get_incident(created.id)

            self.assertEqual(reloaded.id, created.id)
            self.assertEqual(len(reloaded.events), 2)
            self.assertEqual(reloaded.events[0].event_hash, created.events[0].event_hash)

    def test_store_writes_valid_json_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            engine = ProofOpsEngine(store=JsonIncidentStore(path))
            incident = engine.create_incident("coupon-null-regression")

            payload = json.loads((path / f"{incident.id}.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["scenario_id"], "coupon-null-regression")
            self.assertEqual(list(path.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()

