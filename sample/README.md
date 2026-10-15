# BRAIN · command core

A living 3D command center for a business. Every tool and service orbits one glowing brain, wrapped in a breathing aura. It launches tools, talks, listens, and lets AI agents drive the screen.

## Start

```bash
python3 brain/serve.py
# open http://localhost:4747
```

Python 3.9 or newer. No other installs.

## Make it yours (5 minutes)

1. **brand.json**: product name, tagline, owner, one paragraph about the business (the AI reads it), voice, and aura colors.
2. **registry.json**: your tools and connections. Each tool can carry a `serve` block so the hub can start it: `{"kind":"static","dir":"site","port":8080}`.
3. **missions.json**: the shared work queue for you and your agents. Start empty.

## Keep it running

```bash
brain/always-on.sh install     # macOS: starts at login, restarts itself if it ever stops
brain/always-on.sh status
brain/always-on.sh uninstall
```

## Talk to it

Gear icon, then paste an API key for xAI, Anthropic, or any OpenAI compatible endpoint. The key stays in that browser. Local commands work with no key: "launch website", "status", "missions".

## Let agents drive it

See AGENTS.md. Any agent with a shell can rotate the globe, open tools, queue missions and speak:

```bash
python3 brain/ctl.py --from agent select planner
python3 brain/ctl.py --from agent say "Pipeline updated"
```
