from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_dashboard_contains_required_operator_controls_and_landmarks(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn('lang="zh-CN"', html)
        self.assertIn("<main", html)
        self.assertIn('id="incident-board"', html)
        self.assertIn('id="scenario-select"', html)
        self.assertIn('data-action="create-incident"', html)
        self.assertIn('data-action="run-demo"', html)
        self.assertIn('id="approval-dialog"', html)
        self.assertIn('aria-live="polite"', html)

    def test_client_uses_api_contract_without_unsafe_html_injection(self) -> None:
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        for endpoint in ("/api/scenarios", "/api/agents", "/api/skills", "/api/incidents", "/api/metrics"):
            self.assertIn(endpoint, script)
        self.assertIn("textContent", script)
        self.assertNotIn(".innerHTML", script)
        self.assertNotIn("eval(", script)

    def test_visual_system_is_responsive_and_respects_reduced_motion(self) -> None:
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("--signal", css)
        self.assertIn("@media (max-width:", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)


if __name__ == "__main__":
    unittest.main()
