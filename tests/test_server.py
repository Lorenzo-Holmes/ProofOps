from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from proofops.server import StaticAssetResolver, create_server


class StaticAssetResolverTests(unittest.TestCase):
    def test_resolver_serves_index_and_blocks_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<h1>ProofOps</h1>", encoding="utf-8")
            resolver = StaticAssetResolver(root)

            self.assertEqual(resolver.resolve("/").name, "index.html")
            self.assertIsNone(resolver.resolve("/../secret.txt"))
            self.assertIsNone(resolver.resolve("/%2e%2e/secret.txt"))


class HttpServerTests(unittest.TestCase):
    def test_server_exposes_json_api_and_static_application(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static_dir = root / "static"
            static_dir.mkdir()
            (static_dir / "index.html").write_text("<h1>ProofOps Console</h1>", encoding="utf-8")
            server = create_server("127.0.0.1", 0, root / "data", static_dir)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(f"{base}/api/health", timeout=3) as response:
                    health = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                    self.assertEqual(health["status"], "ok")

                request = Request(
                    f"{base}/api/incidents",
                    data=json.dumps({"scenario_id": "coupon-null-regression"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=3) as response:
                    created = json.loads(response.read())
                    self.assertEqual(response.status, 201)
                    self.assertEqual(created["incident"]["status"], "detected")

                with urlopen(f"{base}/", timeout=3) as response:
                    self.assertIn(b"ProofOps Console", response.read())
                    self.assertEqual(response.headers["Cache-Control"], "no-cache")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()

