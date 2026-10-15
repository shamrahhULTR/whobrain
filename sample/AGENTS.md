# Agents: how to work with BRAIN

The hub runs at http://localhost:4747 and only answers requests from this machine.

## Shared work queue
`brain/missions.json`. Claim a mission by setting `status` to `doing` and `owner` to your name. Finish with `status: "done"`, a `done` date and a one line `result`. Never edit a mission another agent is doing.

## Drive the screen
```bash
python3 brain/ctl.py --from <name> select <tool id>   # turn the globe to it, open its panel
python3 brain/ctl.py --from <name> launch <tool id>   # start it locally
python3 brain/ctl.py --from <name> filter <group id>  # or: all
python3 brain/ctl.py --from <name> zoom 1.2           # 0.45 to 2.4
python3 brain/ctl.py --from <name> fit
python3 brain/ctl.py --from <name> say "Done"
python3 brain/ctl.py --from <name> mission "Title" <owner> <tool id>
python3 brain/ctl.py state                            # what is on screen now
python3 brain/ctl.py tools
```

## Rules
- Never write API keys or secrets into any file.
- Keep `registry.json` true: when a tool's facts change, update it. The hub rereads it every 8 seconds.
