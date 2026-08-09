from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from proofops.server import create_server


class McpHttpTransportTests(unittest.TestCase):
    def test_streamable_http_endpoint_accepts_json_rpc_tool_requests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "static"
            static.mkdir()
            (static / "index.html").write_text("ProofOps", encoding="utf-8")
            server = create_server("127.0.0.1", 0, root / "data", static)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                request = Request(
                    f"http://127.0.0.1:{server.server_port}/mcp",
                    data=json.dumps({
                        "jsonrpc": "2.0",
                        "id": 7,
                        "method": "tools/list",
                        "params": {},
                    }).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "MCP-Protocol-Version": "2026-07-28",
                    },
                    method="POST",
                )
                with urlopen(request, timeout=3) as response:
                    payload = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                    self.assertEqual(payload["id"], 7)
                    self.assertGreaterEqual(len(payload["result"]["tools"]), 8)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
