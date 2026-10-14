"""Browser UI for the CLIPS-backed BNPL classroom demo.

Run ``python web_app.py`` for localhost. Cloud hosts can set PORT and pass
``--host 0.0.0.0``. The application does not persist applicant data.
"""

from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from backward_diagnosis import diagnose
from bnpl_expert import evaluate_dict


ROOT = Path(__file__).parent
STATIC = ROOT / "static"
MAX_REQUEST_BYTES = 64 * 1024
ASSETS = {
    "/": (STATIC / "index.html", "text/html; charset=utf-8"),
    "/styles.css": (STATIC / "styles.css", "text/css; charset=utf-8"),
    "/app.js": (STATIC / "app.js", "text/javascript; charset=utf-8"),
}


class BNPLHandler(BaseHTTPRequestHandler):
    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlsplit(self.path).path
        if path == "/healthz":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return
        asset = ASSETS.get(path)
        if asset is None:
            self._json(HTTPStatus.NOT_FOUND, {"error": "页面不存在。"})
            return
        file_path, content_type = asset
        try:
            content = file_path.read_bytes()
        except OSError:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "页面文件不可用。"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlsplit(self.path).path
        if path not in {"/api/evaluate", "/api/diagnose"}:
            self._json(HTTPStatus.NOT_FOUND, {"error": "接口不存在。"})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "只接受 application/json。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "请求内容为空或过大。"})
            return
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or not isinstance(body.get("applicant"), dict):
                raise ValueError("请提供申请人资料。")
            if path == "/api/evaluate":
                result = evaluate_dict(body["applicant"])
            else:
                target = body.get("target_limit", 10000)
                if type(target) is not int:
                    raise ValueError("目标额度必须是整数。")
                result = diagnose(body["applicant"], target)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON 格式不正确。"})
            return
        except (TypeError, ValueError, AttributeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "规则运行失败，请检查服务端日志。"})
            raise
        self._json(HTTPStatus.OK, {"result": result})

    def log_message(self, format: str, *args: object) -> None:
        # Avoid writing URLs or applicant data to terminal history.
        if not self.path.startswith("/api/"):
            super().log_message(format, *args)


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), BNPLHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BNPL expert-system web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost).")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    with make_server(host=args.host, port=args.port) as server:
        print(f"Listening on {args.host}:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
