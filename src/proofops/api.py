from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from . import __version__
from .catalog import AGENTS, SKILLS
from .engine import InvalidInput, ProofOpsEngine, ProofOpsError


@dataclass(slots=True)
class ApiResponse:
    status: int
    payload: dict[str, Any]


class ApiApp:
    def __init__(self, engine: ProofOpsEngine) -> None:
        self.engine = engine

    def dispatch(self, method: str, raw_path: str, body: dict[str, Any] | None = None) -> ApiResponse:
        method = method.upper()
        path = urlsplit(raw_path).path.rstrip("/") or "/"
        body = body or {}
        try:
            return self._dispatch(method, path, body)
        except ProofOpsError as error:
            return self._error(error.http_status, error.code, error.message)
        except (TypeError, ValueError) as error:
            return self._error(400, "invalid_input", str(error))

    def _dispatch(self, method: str, path: str, body: dict[str, Any]) -> ApiResponse:
        if method == "GET" and path == "/api/health":
            return ApiResponse(200, {"status": "ok", "service": "proofops", "version": __version__})
        if method == "GET" and path == "/api/scenarios":
            return ApiResponse(200, {"items": self.engine.scenarios()})
        if method == "GET" and path == "/api/agents":
            return ApiResponse(200, {"items": [agent.to_dict() for agent in AGENTS]})
        if method == "GET" and path == "/api/skills":
            return ApiResponse(200, {"items": [skill.to_dict() for skill in SKILLS]})
        if method == "GET" and path == "/api/metrics":
            return ApiResponse(200, self.engine.metrics())
        if path == "/api/incidents":
            if method == "GET":
                return ApiResponse(200, {"items": [item.to_dict() for item in self.engine.list_incidents()]})
            if method == "POST":
                scenario_id = body.get("scenario_id")
                if not isinstance(scenario_id, str) or not scenario_id:
                    raise InvalidInput("scenario_id不能为空。")
                return ApiResponse(201, {"incident": self.engine.create_incident(scenario_id).to_dict()})

        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and parts[:2] == ["api", "incidents"]:
            incident_id = parts[2]
            if len(parts) == 3 and method == "GET":
                return ApiResponse(200, {"incident": self.engine.get_incident(incident_id).to_dict()})
            if len(parts) == 4 and method == "POST":
                action = parts[3]
                if action == "advance":
                    incident = self.engine.advance(incident_id)
                elif action == "approve":
                    incident = self.engine.approve(
                        incident_id, str(body.get("actor", "")), str(body.get("reason", "approved for demo"))
                    )
                elif action == "reject":
                    incident = self.engine.reject(
                        incident_id, str(body.get("actor", "")), str(body.get("reason", ""))
                    )
                else:
                    return self._error(404, "route_not_found", f"未知操作：{action}")
                return ApiResponse(200, {"incident": incident.to_dict()})
            if len(parts) == 4 and parts[3] == "audit" and method == "GET":
                incident = self.engine.get_incident(incident_id)
                return ApiResponse(
                    200,
                    {"incident_id": incident_id, "valid": self.engine.verify_audit(incident_id), "events": [event.to_dict() for event in incident.events]},
                )

        return self._error(404, "route_not_found", f"未找到路由：{method} {path}")

    @staticmethod
    def _error(status: int, code: str, message: str) -> ApiResponse:
        return ApiResponse(status, {"error": {"code": code, "message": message}})

