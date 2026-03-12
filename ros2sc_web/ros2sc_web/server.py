import json
import os
import re
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


def _run_ros2(cmd: list[str], domain_id: str | None, timeout_s: float = 2.0) -> str:
    env = os.environ.copy()
    if domain_id is not None and domain_id != "":
        env["ROS_DOMAIN_ID"] = domain_id
    p = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return p.stdout


_TYPE_IN_BRACKETS_RE = re.compile(r"^(?P<name>\S+)\s+\[(?P<types>.+)\]\s*$")


def _parse_list_with_types(output: str) -> list[dict]:
    items: dict[str, set[str]] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _TYPE_IN_BRACKETS_RE.match(line)
        if not m:
            name = line
            items.setdefault(name, set())
            continue

        name = m.group("name")
        types_str = m.group("types")
        types = [t.strip() for t in types_str.split(",") if t.strip()]
        s = items.setdefault(name, set())
        for t in types:
            s.add(t)

    out = [{"name": n, "types": sorted(list(ts))} for n, ts in items.items()]
    out.sort(key=lambda x: x["name"])
    return out


def snapshot(domain_id: str | None) -> dict:
    topics_out = _run_ros2(["ros2", "topic", "list", "-t"], domain_id)
    services_out = _run_ros2(["ros2", "service", "list", "-t"], domain_id)
    nodes_out = _run_ros2(["ros2", "node", "list"], domain_id)
    pkgs_out = _run_ros2(["ros2", "pkg", "list"], domain_id)

    topics = _parse_list_with_types(topics_out)
    services = _parse_list_with_types(services_out)

    nodes = []
    for line in nodes_out.splitlines():
        line = line.strip()
        if not line:
            continue
        nodes.append(line)
    nodes.sort()

    packages = []
    for line in pkgs_out.splitlines():
        line = line.strip()
        if not line:
            continue
        packages.append(line)
    packages.sort()

    return {
        "domain_id": domain_id if domain_id is not None else "",
        "topics": topics,
        "services": services,
        "nodes": nodes,
        "packages": packages,
    }


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _file_response(handler: BaseHTTPRequestHandler, path: str) -> None:
    if not os.path.exists(path) or not os.path.isfile(path):
        handler.send_error(HTTPStatus.NOT_FOUND, "Not found")
        return

    with open(path, "rb") as f:
        body = f.read()

    if path.endswith(".html"):
        content_type = "text/html; charset=utf-8"
    elif path.endswith(".js"):
        content_type = "text/javascript; charset=utf-8"
    elif path.endswith(".css"):
        content_type = "text/css; charset=utf-8"
    else:
        content_type = "application/octet-stream"

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def make_handler(static_dir: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            # Quiet default http.server logs.
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            domain_id = (qs.get("domain_id", [""])[0] or "").strip()
            if domain_id == "":
                domain_id = None

            if parsed.path in ("/", "/index.html"):
                return _file_response(self, os.path.join(static_dir, "index.html"))

            if parsed.path == "/api/snapshot":
                return _json_response(self, snapshot(domain_id))

            if parsed.path == "/api/topics":
                return _json_response(self, {"domain_id": domain_id or "", "topics": snapshot(domain_id)["topics"]})

            if parsed.path == "/api/services":
                return _json_response(self, {"domain_id": domain_id or "", "services": snapshot(domain_id)["services"]})

            if parsed.path == "/api/nodes":
                return _json_response(self, {"domain_id": domain_id or "", "nodes": snapshot(domain_id)["nodes"]})

            if parsed.path == "/api/packages":
                return _json_response(self, {"domain_id": domain_id or "", "packages": snapshot(domain_id)["packages"]})

            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    return Handler


def main(argv=None) -> None:
    port = int(os.environ.get("ROS2SC_WEB_PORT", "8080"))
    address = os.environ.get("ROS2SC_WEB_ADDRESS", "127.0.0.1")

    static_dir = os.path.join(os.path.dirname(__file__), "static")

    server = ThreadingHTTPServer((address, port), make_handler(static_dir))

    print(f"ROS2SC Web Inspector: http://{address}:{port}", flush=True)
    print("API endpoints: /api/snapshot /api/topics /api/services /api/nodes /api/packages", flush=True)
    print("Tip: add ?domain_id=<N> to query a different ROS_DOMAIN_ID", flush=True)

    def serve() -> None:
        try:
            server.serve_forever(poll_interval=0.2)
        finally:
            server.server_close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    try:
        t.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        t.join(timeout=1.0)

