from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable

from . import __version__
from .engine import InvalidInput, ProofOpsEngine, ProofOpsError


CURRENT_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOLS = {"2025-11-25", "2025-06-18", "2025-03-26"}


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {
                "title": self.title,
                "readOnlyHint": self.read_only,
                "destructiveHint": self.destructive,
                "idempotentHint": self.idempotent,
                "openWorldHint": False,
            },
        }


class McpApp:
    """Stateless MCP JSON-RPC adapter with current and legacy discovery support."""

    def __init__(self, engine: ProofOpsEngine) -> None:
        self.engine = engine
        string_id = {"type": "string", "minLength": 1}
        self.tools: dict[str, ToolDefinition] = {
            "proofops.list_scenarios": ToolDefinition(
                "proofops.list_scenarios", "列出故障样本",
                "列出所有可重复的本地故障场景和预期验证分支。",
                self._schema({}), lambda _args: {"items": self.engine.scenarios()}, read_only=True, idempotent=True,
            ),
            "proofops.list_incidents": ToolDefinition(
                "proofops.list_incidents", "列出事件",
                "读取本地事件队列及其完整审计时间线。",
                self._schema({}), lambda _args: {"items": [item.to_dict() for item in self.engine.list_incidents()]}, read_only=True, idempotent=True,
            ),
            "proofops.get_incident": ToolDefinition(
                "proofops.get_incident", "读取事件",
                "按事件标识读取状态、审批记录和证据链。",
                self._schema({"incident_id": string_id}, ["incident_id"]),
                lambda args: {"incident": self.engine.get_incident(args["incident_id"]).to_dict()}, read_only=True, idempotent=True,
            ),
            "proofops.create_incident": ToolDefinition(
                "proofops.create_incident", "创建本地事件",
                "从指定故障样本创建隔离的演示事件，不操作外部系统。",
                self._schema({"scenario_id": string_id}, ["scenario_id"]),
                lambda args: {"incident": self.engine.create_incident(args["scenario_id"]).to_dict()},
            ),
            "proofops.advance_incident": ToolDefinition(
                "proofops.advance_incident", "推进事件一步",
                "执行当前状态允许的下一项Agent Skill；到达风险门时停止并请求人工审批。",
                self._schema({"incident_id": string_id}, ["incident_id"]),
                lambda args: {"incident": self.engine.advance(args["incident_id"]).to_dict()}, destructive=True,
            ),
            "proofops.approve_incident": ToolDefinition(
                "proofops.approve_incident", "批准受控执行",
                "记录明确的人工批准并允许执行Agent进入本地沙箱阶段。",
                self._schema({
                    "incident_id": string_id,
                    "actor": string_id,
                    "reason": {"type": "string", "default": "approved through MCP"},
                }, ["incident_id", "actor"]),
                lambda args: {"incident": self.engine.approve(args["incident_id"], args["actor"], args.get("reason", "approved through MCP")).to_dict()},
                destructive=True,
            ),
            "proofops.reject_incident": ToolDefinition(
                "proofops.reject_incident", "驳回执行",
                "在任何写操作前驳回待审批计划并记录原因。",
                self._schema({"incident_id": string_id, "actor": string_id, "reason": string_id}, ["incident_id", "actor", "reason"]),
                lambda args: {"incident": self.engine.reject(args["incident_id"], args["actor"], args["reason"]).to_dict()},
                destructive=False,
            ),
            "proofops.get_metrics": ToolDefinition(
                "proofops.get_metrics", "读取运行指标",
                "读取事件结果、审计完整度和Trace覆盖率。",
                self._schema({}), lambda _args: self.engine.metrics(), read_only=True, idempotent=True,
            ),
            "proofops.verify_audit": ToolDefinition(
                "proofops.verify_audit", "校验审计链",
                "重新计算指定事件的SHA-256哈希链并报告完整性。",
                self._schema({"incident_id": string_id}, ["incident_id"]),
                lambda args: {"incident_id": args["incident_id"], "valid": self.engine.verify_audit(args["incident_id"])}, read_only=True, idempotent=True,
            ),
        }

    @staticmethod
    def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": False}
        if required:
            schema["required"] = required
        return schema

    def handle(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        request_id = payload.get("id")
        if payload.get("jsonrpc") != "2.0" or not isinstance(payload.get("method"), str):
            return self._error(request_id, -32600, "Invalid Request")
        method = payload["method"]
        params = payload.get("params") or {}
        if not isinstance(params, dict):
            return self._error(request_id, -32602, "Invalid params")
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._success(request_id, {})
        if method == "initialize":
            requested = params.get("protocolVersion")
            protocol = requested if requested in LEGACY_PROTOCOLS else CURRENT_PROTOCOL
            return self._success(request_id, self._discovery(protocol))
        if method == "server/discover":
            return self._success(request_id, self._discovery(CURRENT_PROTOCOL))
        if method == "tools/list":
            return self._success(request_id, {"tools": [tool.to_dict() for tool in self.tools.values()]})
        if method == "tools/call":
            return self._call_tool(request_id, params)
        return self._error(request_id, -32601, f"Method not found: {method}")

    def _discovery(self, protocol: str) -> dict[str, Any]:
        return {
            "protocolVersion": protocol,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "proofops",
                "title": "ProofOps Incident Command MCP",
                "version": __version__,
                "description": "Evidence-driven local incident-response fixture with human approval gates.",
            },
            "instructions": "Use read-only tools first. Never call approve_incident without an explicit human decision.",
        }

    def _call_tool(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or name not in self.tools:
            return self._error(request_id, -32602, f"Unknown tool: {name}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return self._error(request_id, -32602, "Tool arguments must be an object")
        tool = self.tools[name]
        try:
            required = tool.input_schema.get("required", [])
            missing = [key for key in required if key not in arguments or arguments[key] in (None, "")]
            if missing:
                raise InvalidInput(f"缺少必填参数：{', '.join(missing)}")
            structured = tool.handler(arguments)
            return self._success(request_id, self._tool_result(structured, is_error=False))
        except ProofOpsError as error:
            return self._success(request_id, self._tool_result({"code": error.code, "message": error.message}, is_error=True))
        except (KeyError, TypeError, ValueError) as error:
            return self._success(request_id, self._tool_result({"code": "invalid_input", "message": str(error)}, is_error=True))

    @staticmethod
    def _tool_result(structured: dict[str, Any], is_error: bool) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False, separators=(",", ":"))}],
            "structuredContent": structured,
            "isError": is_error,
        }

    @staticmethod
    def _success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
