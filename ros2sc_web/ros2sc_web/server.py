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
_INTERFACE_TYPE_RE = re.compile(r"^[a-zA-Z0-9_]+/(msg|srv|action)/[A-Za-z0-9_]+$")
_FIELD_RE = re.compile(r"^(?P<type>\S+)\s+(?P<name>[A-Za-z_]\w*)$")
_PRIMITIVES = {
    "bool",
    "byte",
    "char",
    "float32",
    "float64",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "string",
    "wstring",
}


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
    actions_out = _run_ros2(["ros2", "action", "list", "-t"], domain_id)
    nodes_out = _run_ros2(["ros2", "node", "list"], domain_id)
    pkgs_out = _run_ros2(["ros2", "pkg", "list"], domain_id)

    topics = _parse_list_with_types(topics_out)
    services = _parse_list_with_types(services_out)
    actions = _parse_list_with_types(actions_out)

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
        "actions": actions,
        "nodes": nodes,
        "packages": packages,
    }


def interface_show(interface_type: str) -> dict:
    interface_type = (interface_type or "").strip()
    if not _INTERFACE_TYPE_RE.match(interface_type):
        return {
            "type": interface_type,
            "ok": False,
            "error": "Invalid type. Expected like 'std_msgs/msg/String' or 'example_interfaces/srv/AddTwoInts'.",
            "text": "",
        }

    out = _run_ros2(["ros2", "interface", "show", interface_type], domain_id=None, timeout_s=3.0)
    out = out[:200_000]
    return {"type": interface_type, "ok": True, "error": "", "text": out}


def _default_value_for_primitive(t: str):
    if t in ("string", "wstring"):
        return ""
    if t == "bool":
        return False
    if t in ("float32", "float64"):
        return 0.0
    if t in _PRIMITIVES:
        return 0
    return ""


def _normalize_type_token(t: str) -> str:
    # Remove bounded/array decorations we don't handle fully; keep base.
    # Examples:
    #   string<=10 -> string
    #   int32[3]   -> int32
    #   pkg/msg/T[] -> pkg/msg/T
    t = t.split("<=")[0]
    t = re.sub(r"\[.*\]$", "", t)
    t = re.sub(r"\[\]$", "", t)
    return t


def _expand_type_with_context(t: str, context_pkg: str | None) -> str:
    """
    ros2 interface show sometimes prints nested message types as `pkg/Type` (without `/msg/`).
    Convert to `pkg/msg/Type` best-effort.
    """
    if _INTERFACE_TYPE_RE.match(t):
        return t
    if t in _PRIMITIVES:
        return t
    # e.g. geometry_msgs/Vector3 -> geometry_msgs/msg/Vector3
    if re.match(r"^[A-Za-z0-9_]+/[A-Za-z0-9_]+$", t):
        pkg, typ = t.split("/", 1)
        return f"{pkg}/msg/{typ}"
    # e.g. Twist uses `Vector3` (no package). Assume same package msg.
    if context_pkg and re.match(r"^[A-Za-z0-9_]+$", t):
        return f"{context_pkg}/msg/{t}"
    return t


def _split_interface_sections(text: str) -> list[list[str]]:
    sections: list[list[str]] = [[]]
    for line in text.splitlines():
        if line.strip() == "---":
            sections.append([])
            continue
        sections[-1].append(line)
    return sections


def _build_object_from_interface_lines(lines: list[str], context_pkg: str | None, depth: int = 1) -> dict:
    obj: dict = {}
    for raw in lines:
        # Skip nested/indented expansions; we only parse top-level fields.
        if raw.startswith((" ", "\t")):
            continue
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            # constants
            continue
        m = _FIELD_RE.match(line)
        if not m:
            continue
        t = _expand_type_with_context(_normalize_type_token(m.group("type")), context_pkg)
        name = m.group("name")

        if t in _PRIMITIVES:
            obj[name] = _default_value_for_primitive(t)
            continue

        # Try recursive expansion for nested message types when available.
        if depth <= 0:
            obj[name] = {}
            continue

        if _INTERFACE_TYPE_RE.match(t):
            nested = interface_show(t)
            if nested.get("ok"):
                nested_sections = _split_interface_sections(nested.get("text", ""))
                # For msg: section[0]
                nested_pkg = t.split("/", 1)[0] if "/" in t else context_pkg
                nested_obj = _build_object_from_interface_lines(
                    nested_sections[0], context_pkg=nested_pkg, depth=depth - 1
                )
                obj[name] = nested_obj
            else:
                obj[name] = {}
        else:
            obj[name] = {}
    return obj


def _to_inline_yaml(obj) -> str:
    # Simple inline YAML/JSON-ish for ROS 2 CLI, without quoting keys.
    if isinstance(obj, dict):
        inner = ", ".join([f"{k}: {_to_inline_yaml(v)}" for k, v in obj.items()])
        return "{" + inner + "}"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return str(obj)
    # strings
    return f"\"{str(obj)}\""


def command_template(kind: str, name: str, interface_type: str) -> dict:
    kind = (kind or "").strip().lower()
    name = (name or "").strip()
    interface_type = (interface_type or "").strip()

    if kind not in ("topic", "service", "action"):
        return {"ok": False, "error": "Invalid kind", "command": "", "payload": ""}
    if not name:
        return {"ok": False, "error": "Missing name", "command": "", "payload": ""}
    if not _INTERFACE_TYPE_RE.match(interface_type):
        return {"ok": False, "error": "Invalid type", "command": "", "payload": ""}

    shown = interface_show(interface_type)
    if not shown.get("ok"):
        return {"ok": False, "error": shown.get("error", "interface show failed"), "command": "", "payload": ""}

    sections = _split_interface_sections(shown.get("text", ""))
    context_pkg = interface_type.split("/", 1)[0] if "/" in interface_type else None

    if kind == "topic":
        obj = _build_object_from_interface_lines(sections[0], context_pkg=context_pkg, depth=2)
        payload = _to_inline_yaml(obj)
        cmd = f"ros2 topic pub {name} {interface_type} '{payload}'"
        return {"ok": True, "error": "", "command": cmd, "payload": payload}

    if kind == "service":
        # srv: request is section[0]
        req_lines = sections[0] if len(sections) >= 1 else []
        obj = _build_object_from_interface_lines(req_lines, context_pkg=context_pkg, depth=2)
        payload = _to_inline_yaml(obj)
        cmd = f"ros2 service call {name} {interface_type} '{payload}'"
        return {"ok": True, "error": "", "command": cmd, "payload": payload}

    # action: goal is section[0]
    goal_lines = sections[0] if len(sections) >= 1 else []
    obj = _build_object_from_interface_lines(goal_lines, context_pkg=context_pkg, depth=2)
    payload = _to_inline_yaml(obj)
    cmd = f"ros2 action send_goal {name} {interface_type} '{payload}'"
    return {"ok": True, "error": "", "command": cmd, "payload": payload}


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

            if parsed.path == "/api/interface":
                interface_type = (qs.get("type", [""])[0] or "").strip()
                return _json_response(self, interface_show(interface_type))

            if parsed.path == "/api/template":
                kind = (qs.get("kind", [""])[0] or "").strip()
                item_name = (qs.get("name", [""])[0] or "").strip()
                interface_type = (qs.get("type", [""])[0] or "").strip()
                return _json_response(self, command_template(kind, item_name, interface_type))

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

