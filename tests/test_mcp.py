from __future__ import annotations

import unittest

from proofops.engine import ProofOpsEngine
from proofops.mcp import McpApp


class McpAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ProofOpsEngine()
        self.mcp = McpApp(self.engine)

    def request(self, method: str, params: dict | None = None, request_id: int = 1):
        return self.mcp.handle({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        })

    def test_discovery_and_legacy_initialize_advertise_tool_capability(self) -> None:
        discovery = self.request("server/discover")
        initialized = self.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        )

        self.assertEqual(discovery["result"]["protocolVersion"], "2026-07-28")
        self.assertIn("tools", discovery["result"]["capabilities"])
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "proofops")

    def test_tools_list_contains_read_only_and_human_gated_operations(self) -> None:
        response = self.request("tools/list")
        tools = {tool["name"]: tool for tool in response["result"]["tools"]}

        self.assertIn("proofops.list_scenarios", tools)
        self.assertIn("proofops.create_incident", tools)
        self.assertIn("proofops.approve_incident", tools)
        self.assertTrue(tools["proofops.list_scenarios"]["annotations"]["readOnlyHint"])
        self.assertFalse(tools["proofops.approve_incident"]["annotations"]["readOnlyHint"])
        self.assertIn("actor", tools["proofops.approve_incident"]["inputSchema"]["required"])

    def test_tool_call_returns_text_and_structured_content(self) -> None:
        response = self.request(
            "tools/call",
            {
                "name": "proofops.create_incident",
                "arguments": {"scenario_id": "coupon-null-regression"},
            },
        )

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["type"], "text")
        self.assertEqual(result["structuredContent"]["incident"]["status"], "detected")

    def test_domain_failure_is_reported_as_recoverable_tool_error(self) -> None:
        response = self.request(
            "tools/call",
            {
                "name": "proofops.create_incident",
                "arguments": {"scenario_id": "missing-scenario"},
            },
        )

        self.assertTrue(response["result"]["isError"])
        self.assertIn("未知故障样本", response["result"]["content"][0]["text"])

    def test_unknown_tool_is_json_rpc_protocol_error(self) -> None:
        response = self.request("tools/call", {"name": "proofops.unknown", "arguments": {}})

        self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(response["id"], 1)


if __name__ == "__main__":
    unittest.main()
