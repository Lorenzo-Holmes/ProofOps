from __future__ import annotations

import unittest
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitHubPagesContractTests(unittest.TestCase):
    def test_static_entrypoint_uses_repository_relative_assets(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="./styles.css"', html)
        self.assertIn('src="./demo-api.js"', html)
        self.assertIn('src="./app.js"', html)
        self.assertNotIn('href="/styles.css"', html)
        self.assertNotIn('src="/app.js"', html)

    def test_browser_demo_adapter_covers_dashboard_routes(self) -> None:
        script = (ROOT / "web" / "demo-api.js").read_text(encoding="utf-8")

        for route in ("/api/scenarios", "/api/agents", "/api/skills", "/api/incidents", "/api/metrics"):
            self.assertIn(route, script)
        for operation in ("advance", "approve", "reject"):
            self.assertIn(operation, script)
        self.assertIn("window.ProofOpsDemoApi", script)

    def test_pages_workflow_deploys_web_directory(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v7", workflow)
        self.assertIn("actions/configure-pages@v6", workflow)
        self.assertIn("actions/upload-pages-artifact@v5", workflow)
        self.assertIn("actions/deploy-pages@v5", workflow)
        self.assertIn("path: ./web", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for browser adapter runtime checks")
    def test_static_demo_runtime_and_tamper_detection(self) -> None:
        completed = subprocess.run(
            ["node", str(ROOT / "tests" / "demo_api_runtime_test.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("demo-api runtime checks passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
