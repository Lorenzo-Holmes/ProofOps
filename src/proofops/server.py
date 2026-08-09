from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

from .api import ApiApp, ApiResponse
from .engine import ProofOpsEngine
from .mcp import McpApp
from .store import JsonIncidentStore


MAX_BODY_BYTES = 1_048_576


class StaticAssetResolver:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def resolve(self, raw_path: str) -> Path | None:
        decoded = unquote(urlsplit(raw_path).path)
        relative = PurePosixPath(decoded.lstrip("/"))
        if any(part in ("..", "") for part in relative.parts):
            return None
        if str(relative) in ("", "."):
            relative = PurePosixPath("index.html")
        candidate = self.root.joinpath(*relative.parts).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        if candidate.is_dir():
            candidate = candidate / "index.html"
        return candidate if candidate.is_file() else None


class ProofOpsHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        app: ApiApp,
        mcp: McpApp,
        static_resolver: StaticAssetResolver,
    ) -> None:
        self.app = app
        self.mcp = mcp
        self.static_resolver = static_resolver
        super().__init__(server_address, ProofOpsRequestHandler)


class ProofOpsRequestHandler(BaseHTTPRequestHandler):
    server: ProofOpsHttpServer
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        if urlsplit(self.path).path.startswith("/api/"):
            self._serve_json_request("GET")
        else:
            self._serve_static()

    def do_POST(self) -> None:  # noqa: N802
        self._serve_json_request("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._common_headers()
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve_json_request(self, method: str) -> None:
        body: dict[str, Any] = {}
        if method == "POST":
            body = self._read_json_body()
            if body is None:
                return
        if urlsplit(self.path).path == "/mcp":
            response = self.server.mcp.handle(body)
            if response is None:
                self._write_empty(202)
            else:
                self._write_json(ApiResponse(200, response))
            return
        self._write_json(self.server.app.dispatch(method, self.path, body))

    def _read_json_body(self) -> dict[str, Any] | None:
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError:
            self._write_json(ApiResponse(400, {"error": {"code": "invalid_length", "message": "Content-Length无效。"}}))
            return None
        if length > MAX_BODY_BYTES:
            self._write_json(ApiResponse(413, {"error": {"code": "payload_too_large", "message": "请求体超过1 MiB。"}}))
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            decoded = json.loads(raw.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise ValueError("JSON请求体必须是对象。")
            return decoded
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._write_json(ApiResponse(400, {"error": {"code": "invalid_json", "message": str(error)}}))
            return None

    def _serve_static(self) -> None:
        asset = self.server.static_resolver.resolve(self.path)
        if not asset:
            self._write_json(ApiResponse(404, {"error": {"code": "asset_not_found", "message": "静态资源不存在。"}}))
            return
        content = asset.read_bytes()
        content_type, _ = mimetypes.guess_type(asset.name)
        self.send_response(200)
        self._common_headers()
        self.send_header("Content-Type", f"{content_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _write_json(self, response: ApiResponse) -> None:
        content = json.dumps(response.payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(response.status)
        self._common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _write_empty(self, status: int) -> None:
        self.send_response(status)
        self._common_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _common_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def log_message(self, format: str, *args: object) -> None:
        print(f"[proofops-http] {self.address_string()} - {format % args}")


def create_server(host: str, port: int, data_dir: Path, static_dir: Path) -> ProofOpsHttpServer:
    engine = ProofOpsEngine(store=JsonIncidentStore(Path(data_dir)))
    return ProofOpsHttpServer(
        (host, port),
        ApiApp(engine),
        McpApp(engine),
        StaticAssetResolver(Path(static_dir)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ProofOps local competition demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data-dir", type=Path, default=Path("work/data"))
    parser.add_argument("--static-dir", type=Path, default=Path("web"))
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port, args.data_dir, args.static_dir)
    print(f"ProofOps running at http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
