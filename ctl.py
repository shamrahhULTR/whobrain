#!/usr/bin/env python3
"""
Drive the BRAIN screen from any shell. This is what the Grok bot calls.

    python3 brain/ctl.py select <tool id>
    python3 brain/ctl.py launch website
    python3 brain/ctl.py say "Website is live"
    python3 brain/ctl.py state
    python3 brain/ctl.py --from grok zoom 1.4

Every command goes to the running hub at http://localhost:4747 and shows up on
screen instantly. If the hub is not open it is opened for you.
"""
import json, sys, urllib.request

BASE = "http://localhost:4747"


def call(path, body=None):
    req = urllib.request.Request(BASE + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main(argv):
    who = "grok"
    if argv[:1] == ["--from"]:
        who, argv = argv[1], argv[2:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    verb, rest = argv[0], argv[1:]
    try:
        if verb == "state":
            print(json.dumps(call("/api/state"), indent=2)); return 0
        if verb == "tools":
            reg = call("/api/registry")
            for t in reg["tools"]:
                print("%-18s %-26s %s" % (t["id"], t["name"], "RUNNING" if t["status"]["running"] else ""))
            return 0
        if verb == "missions":
            print(json.dumps(call("/api/missions"), indent=2)); return 0
        cmd = {"type": verb, "from": who}
        if verb in ("select", "launch", "stop", "open"):
            cmd["id"] = rest[0]
        elif verb == "filter":
            cmd["group"] = rest[0] if rest else "all"
        elif verb in ("zoom", "spin"):
            cmd["value"] = float(rest[0])
        elif verb in ("say", "chat", "toast"):
            cmd["text"] = " ".join(rest)
        elif verb == "palette":
            cmd["q"] = " ".join(rest)
        elif verb == "mic":
            cmd["on"] = (rest[:1] or ["on"])[0] != "off"
        elif verb == "mission":
            cmd.update(title=rest[0], owner=(rest[1] if len(rest) > 1 else "grok"), tool=(rest[2] if len(rest) > 2 else ""))
        out = call("/api/cmd", cmd)
        print(json.dumps(out))
        return 0 if out.get("ok") else 1
    except IndexError:
        print("missing argument, see --help"); return 2
    except Exception as e:
        print("hub not reachable (%s). Start it with: python3 brain/serve.py" % e); return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
