#!/usr/bin/env python3
"""
BRAIN control server. Zero dependencies, Python 3.9+.

Serves the 3D hub (index.html) and exposes a small local API so the hub
can actually launch, stop, inspect and reveal every tool in the workspace.

    python3 brain/serve.py            # http://localhost:4747

API (all local only, bound to 127.0.0.1):
    GET  /api/registry          registry.json + live status per tool
    POST /api/launch/<id>       start that tool's local server, returns its url
    POST /api/stop/<id>         stop a server this process started
    POST /api/reveal/<id>       open the tool's folder in Finder
    GET  /api/git/<id>          branch, last commit, dirty file list
    GET  /api/missions          shared task queue (missions.json)
    POST /api/missions          replace the queue (JSON array)
    POST /api/agent             proxy a chat completion to the configured
                                provider. Body: {provider, baseUrl, model,
                                key, messages}. The key comes from the
                                browser each call and is never stored here.
    POST /api/say               macOS `say` text to speech fallback
    POST /api/cmd               drive the screen: {"type":"select","id":"<tool id>","from":"grok"}
    GET  /api/stream            server-sent events the open hub listens to
    GET/POST /api/state         what the hub is currently showing (hub posts, agents read)
"""
import json, os, sys, subprocess, socket, time, threading, shutil, queue
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTRY = os.path.join(HERE, "registry.json")
MISSIONS = os.path.join(HERE, "missions.json")
PORT = int(os.environ.get("BRAIN_PORT", "4747"))

PROCS = {}          # tool id -> Popen
LOCK = threading.Lock()
CLIENTS = []        # one queue per open hub tab (SSE)
STATE = {}          # last state the hub reported
APPROVALS = []      # decisions made on the approval card (newest last)
ALLOWED_HOSTS = {"localhost:%d" % PORT, "127.0.0.1:%d" % PORT}
ALLOWED_ORIGINS = {"http://" + h for h in ALLOWED_HOSTS}


def broadcast(cmd):
    with LOCK:
        for q in CLIENTS:
            q.put(cmd)
        return len(CLIENTS)


def private_or_sample(name):
    """Your own file if it exists, otherwise the demo copy in sample/ (fresh clones run out of the box)."""
    own = os.path.join(HERE, name)
    return own if os.path.exists(own) else os.path.join(HERE, "sample", name)


def load_registry():
    with open(private_or_sample("registry.json"), encoding="utf-8") as f:
        return json.load(f)


def tool_by_id(tid):
    for t in load_registry()["tools"]:
        if t["id"] == tid:
            return t
    return None


def port_open(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def git_info(folder):
    path = os.path.join(ROOT, folder)
    if not os.path.isdir(os.path.join(path, ".git")):
        return {"repo": False}
    def run(*args):
        try:
            return subprocess.check_output(["git", "-C", path] + list(args),
                                           stderr=subprocess.DEVNULL, timeout=5).decode().strip()
        except Exception:
            return ""
    dirty = [l for l in run("status", "--porcelain").splitlines() if l.strip()]
    return {
        "repo": True,
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "last": run("log", "-1", "--format=%h %ad %s", "--date=short"),
        "dirty": len(dirty),
        "dirtyFiles": [l[3:] for l in dirty][:20],
    }


def status_for(tool):
    serve = tool.get("serve") or {}
    port = serve.get("port")
    running = bool(port and port_open(port))
    mine = tool["id"] in PROCS and PROCS[tool["id"]].poll() is None
    return {
        "running": running,
        "owned": mine,
        "url": "http://localhost:%d/" % port if port else None,
        "exists": os.path.exists(os.path.join(ROOT, tool.get("folder", ""))),
    }


def launch(tool):
    serve = tool.get("serve")
    if not serve:
        return {"ok": False, "error": "nothing to launch"}
    port = serve["port"]
    url = "http://localhost:%d/" % port
    if port_open(port):
        return {"ok": True, "url": url, "already": True}
    kind = serve["kind"]
    env = dict(os.environ)
    env.update(serve.get("env") or {})
    log = open(os.path.join(HERE, ".logs", tool["id"] + ".log"), "ab")
    if kind in ("static", "build-static"):
        if kind == "build-static":
            subprocess.run(serve["build"], cwd=os.path.join(ROOT, serve["cwd"]),
                           stdout=log, stderr=log, timeout=120)
        cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
        cwd = os.path.join(ROOT, serve["dir"])
    elif kind == "cmd":
        cmd = serve["cmd"]
        cwd = os.path.join(ROOT, serve["cwd"])
    else:
        return {"ok": False, "error": "unknown serve kind " + kind}
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=log)
    with LOCK:
        PROCS[tool["id"]] = p
    for _ in range(40):
        if port_open(port):
            break
        if p.poll() is not None:
            return {"ok": False, "error": "process exited %s, see brain/.logs/%s.log" % (p.returncode, tool["id"])}
        time.sleep(0.1)
    return {"ok": True, "url": url, "pid": p.pid}


def stop(tool):
    p = PROCS.get(tool["id"])
    if not p or p.poll() is not None:
        return {"ok": False, "error": "not started by brain (may be running elsewhere)"}
    p.terminate()
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        p.kill()
    return {"ok": True}


def agent_proxy(body):
    provider = body.get("provider", "openai")
    key = body.get("key", "")
    model = body.get("model", "")
    messages = body.get("messages", [])
    base = (body.get("baseUrl") or "").rstrip("/")
    if not key:
        return 400, {"error": "no api key set in the hub settings"}
    if provider == "anthropic":
        base = base or "https://api.anthropic.com"
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        convo = [m for m in messages if m["role"] != "system"]
        req = Request(base + "/v1/messages", method="POST",
                      data=json.dumps({"model": model or "claude-sonnet-5-5",
                                       "max_tokens": 1500, "system": system,
                                       "messages": convo}).encode(),
                      headers={"content-type": "application/json", "x-api-key": key,
                               "anthropic-version": "2023-06-01"})
    else:
        if provider == "xai":
            base = base or "https://api.x.ai"
            model = model or "grok-4"
        elif provider == "openai":
            base = base or "https://api.openai.com"
            model = model or "gpt-4o"
        req = Request(base + "/v1/chat/completions", method="POST",
                      data=json.dumps({"model": model, "messages": messages,
                                       "temperature": 0.4}).encode(),
                      headers={"content-type": "application/json",
                               "authorization": "Bearer " + key})
    try:
        with urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode())
    except HTTPError as e:
        return e.code, {"error": e.read().decode()[:800]}
    except URLError as e:
        return 502, {"error": str(e.reason)}
    if provider == "anthropic":
        text = "".join(b.get("text", "") for b in data.get("content", []))
    else:
        text = data["choices"][0]["message"]["content"]
    return 200, {"text": text}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        line = fmt % args if args else fmt
        if "/api/" in line and "/api/registry" not in line:
            sys.stderr.write("[brain] %s\n" % line)

    def send_json(self, obj, code=200):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        n = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def guard(self):
        """Local-only: block DNS-rebinding and cross-site pages from driving the hub."""
        host = self.headers.get("host", "")
        origin = self.headers.get("origin")
        if host not in ALLOWED_HOSTS or (origin and origin not in ALLOWED_ORIGINS):
            self.send_json({"error": "forbidden"}, 403)
            return False
        return True

    def stream(self):
        q = queue.Queue()
        with LOCK:
            CLIENTS.append(q)
        try:
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("connection", "keep-alive")
            super().end_headers()
            self.wfile.write(b"retry: 1500\n\n")
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=15)
                    self.wfile.write(b"data: " + json.dumps(msg).encode() + b"\n\n")
                except queue.Empty:
                    self.wfile.write(b": ka\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with LOCK:
                if q in CLIENTS:
                    CLIENTS.remove(q)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/") and not self.guard():
            return
        if path == "/api/stream":
            return self.stream()
        if path == "/api/state":
            return self.send_json({"clients": len(CLIENTS), "state": STATE})
        if path == "/api/approvals":
            return self.send_json(APPROVALS[-50:])
        if path == "/api/calendar":
            try:
                with open(os.path.join(HERE, "calendar.json"), encoding="utf-8") as f:
                    return self.send_json(json.load(f))
            except FileNotFoundError:
                return self.send_json({"events": [], "synced": None})
        if path == "/api/registry":
            reg = load_registry()
            for t in reg["tools"]:
                t["status"] = status_for(t)
                t["git"] = git_info(t["folder"])
            reg["server"] = {"port": PORT, "root": ROOT, "time": time.time()}
            return self.send_json(reg)
        if path.startswith("/api/git/"):
            t = tool_by_id(path.split("/")[-1])
            return self.send_json(git_info(t["folder"]) if t else {"error": "no such tool"}, 200 if t else 404)
        if path == "/api/missions":
            try:
                with open(MISSIONS, encoding="utf-8") as f:
                    return self.send_json(json.load(f))
            except FileNotFoundError:
                return self.send_json([])
        if path == "/api/health":
            return self.send_json({"ok": True, "procs": {k: v.poll() is None for k, v in PROCS.items()}})
        if path == "/brand.js":
            # brand.json as a script, so colors and fonts apply before the first frame draws
            try:
                with open(private_or_sample("brand.json"), encoding="utf-8") as f:
                    brand = json.load(f)
            except (FileNotFoundError, ValueError):
                brand = {}
            raw = ("window.BRAND = %s;" % json.dumps(brand)).encode()
            self.send_response(200)
            self.send_header("content-type", "application/javascript")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == "/favicon.ico":
            return self.send_json({}, 204)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        # Static files (index.html, registry.json) must never be cached either.
        self.send_header("cache-control", "no-store")
        super().end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        parts = path.split("/")
        if not self.guard():
            return
        if path == "/api/state":
            STATE.clear()
            STATE.update(self.read_json())
            STATE["at"] = time.time()
            return self.send_json({"ok": True})
        if path == "/api/approval":
            body = self.read_json()
            body["at"] = time.time()
            with LOCK:
                APPROVALS.append(body)
                del APPROVALS[:-200]
            return self.send_json({"ok": True})
        if path == "/api/cmd":
            cmd = self.read_json()
            if not cmd.get("type"):
                return self.send_json({"ok": False, "error": "missing type"}, 400)
            cmd.setdefault("from", "agent")
            n = broadcast(cmd)
            if n == 0 and cmd.get("autoopen", True):
                # nobody is watching: open the hub, wait for it to connect, then deliver
                subprocess.Popen(["open", "http://localhost:%d/" % PORT])
                for _ in range(40):
                    time.sleep(.25)
                    if CLIENTS:
                        break
                time.sleep(1.0)
                n = broadcast(cmd)
            return self.send_json({"ok": n > 0, "delivered": n})
        if path.startswith("/api/launch/"):
            t = tool_by_id(parts[-1])
            return self.send_json(launch(t) if t else {"ok": False, "error": "no such tool"})
        if path.startswith("/api/stop/"):
            t = tool_by_id(parts[-1])
            return self.send_json(stop(t) if t else {"ok": False, "error": "no such tool"})
        if path.startswith("/api/reveal/"):
            t = tool_by_id(parts[-1])
            if not t:
                return self.send_json({"ok": False}, 404)
            target = os.path.join(ROOT, t.get("entry") or t["folder"])
            if os.path.isfile(target):
                subprocess.Popen(["open", "-R", target])      # reveal file in Finder
            else:
                subprocess.Popen(["open", target])            # open folder
            return self.send_json({"ok": True})
        if path == "/api/open":
            body = self.read_json()
            target = body.get("path")
            if target:
                full = os.path.normpath(os.path.join(ROOT, target))
                if full.startswith(ROOT):
                    subprocess.Popen(["open", full])
                    return self.send_json({"ok": True})
            return self.send_json({"ok": False}, 400)
        if path == "/api/missions":
            body = self.read_json()
            if not isinstance(body, list):
                return self.send_json({"ok": False, "error": "expected array"}, 400)
            tmp = MISSIONS + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(body, f, indent=2)
            os.replace(tmp, MISSIONS)
            return self.send_json({"ok": True, "count": len(body)})
        if path == "/api/agent":
            code, out = agent_proxy(self.read_json())
            return self.send_json(out, code)
        if path == "/api/say":
            body = self.read_json()
            if shutil.which("say"):
                subprocess.Popen(["say", "-v", body.get("voice", "Samantha"), body.get("text", "")[:500]])
                return self.send_json({"ok": True})
            return self.send_json({"ok": False, "error": "no say binary"}, 501)
        return self.send_json({"error": "unknown endpoint"}, 404)


def main():
    os.makedirs(os.path.join(HERE, ".logs"), exist_ok=True)
    if not os.path.exists(MISSIONS):
        with open(MISSIONS, "w") as f:
            json.dump([], f)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("BRAIN online  ->  http://localhost:%d/" % PORT, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for p in PROCS.values():
            if p.poll() is None:
                p.terminate()


if __name__ == "__main__":
    main()
