"""The wire format between scripts/tools/bl.py and the Blender server (spec 18 §4.8.1, D4).

JSON lines over TCP on 127.0.0.1. A request is {"id", "token", "cmd", "args"}; a reply is
{"id", "ok", "result" | "error", "ms"}, and an error reply adds "trace". Standard library only, so the
client runs on any Python 3. bl.py hands the server its token in SGT_SERVER_TOKEN, never on a command
line, and records it with the port in cache/server/<name>.json for later clients.
"""
import json
import os

HOST = "127.0.0.1"
TOKEN_ENV = "SGT_SERVER_TOKEN"
LISTENING = "LISTENING"  # the server prints `LISTENING <port>` once its socket is open
MAX_LINE = 256 << 20  # a message longer than this is refused rather than buffered forever
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(PROJECT_DIR, "cache", "server")

COMMANDS = ("ping", "status", "exec", "set", "get", "snapshot", "restore", "save", "load", "build",
            "render", "measure", "silhouette", "variants", "optimise", "selftest", "shutdown")


def state_path(name):
    """pid, port, token, start time and blend of a running server."""
    return os.path.join(SERVER_DIR, f"{name}.json")


def log_path(name):
    """The server's stdout and stderr (Blender's messages, LISTENING, tracebacks)."""
    return os.path.join(SERVER_DIR, f"{name}.log")


def events_path(name):
    """One JSON line per request other than ping and status (exec with its code)."""
    return os.path.join(SERVER_DIR, f"{name}.jsonl")


def snapshot_path(name, k):
    return os.path.join(SERVER_DIR, f"{name}_snap_{k}.blend")


def encode(msg):
    return (json.dumps(msg, separators=(",", ":")) + "\n").encode("utf-8")


def decode(line):
    msg = json.loads(line.decode("utf-8"))
    if not isinstance(msg, dict):
        raise ValueError("a message is a JSON object")
    return msg


def request(rid, token, cmd, args=None):
    return {"id": rid, "token": token, "cmd": cmd, "args": args or {}}


def reply(rid, ms, result=None, error=None, trace=None):
    msg = {"id": rid, "ok": error is None, "ms": round(ms, 3)}
    if error is None:
        msg["result"] = result
    else:
        msg["error"] = error
        if trace:
            msg["trace"] = trace
    return msg


class Lines:
    """Cuts a byte stream into lines, holding back an unfinished one (chunks are joined only when a
    line ends, so a large reply arriving in pieces costs linear time)."""

    def __init__(self):
        self.parts, self.size = [], 0

    def feed(self, data):
        if b"\n" not in data:
            self.parts.append(data)
            self.size += len(data)
            if self.size > MAX_LINE:
                raise ValueError(f"a line longer than {MAX_LINE} bytes")
            return []
        *lines, rest = (b"".join(self.parts) + data).split(b"\n")
        self.parts, self.size = ([rest], len(rest)) if rest else ([], 0)
        return [ln for ln in lines if ln.strip()]


def listening_port(text):
    for line in text.splitlines():
        if line.startswith(LISTENING + " "):
            return int(line.split()[1])
    return None
