# WHOBRAIN · command core by whosystems

One glowing map of everything a business runs on, with the switches to run it.

```bash
python3 brain/serve.py
# open http://localhost:4747
```

- **The globe**: one spinning sphere, always fully in view. Every tool and every connection sits on its surface, woven to its neighbours by a lattice of dots and lines, so the whole thing moves as one body. Drag to spin it, scroll or use the slider to size it, click a node and the globe turns to face it. Cyan means running, an amber ring means uncommitted git work. Diamonds are connections (GitHub, Supabase, Stripe, Netlify, Cloudflare, GoHighLevel, Higgsfield, Drive, Calendar, Claude, Grok).
- **Launch locally**: starts that tool's dev server from the registry and opens it. Stop, reveal in Finder, open live, open repo.
- **⌘K**: command palette.
- **Mic**: push to talk. "launch website", "show pipeline", "status", "missions". Anything else goes to the agent.
- **Agent**: pick Grok, Claude, or any OpenAI compatible endpoint in settings. Paste your own key. It is stored only in this browser and sent to the local server per request. The agent sees the whole registry and can launch, focus, and queue missions by emitting action blocks.
- **Missions**: the shared loop between you and your agents. Persisted to `missions.json`. See `sample/AGENTS.md` for the protocol.

Zero dependencies. Python 3.9 standard library, Three.js from CDN.

## Letting an agent drive the screen

`ctl.py` (or `POST /api/cmd`) sends commands to the open hub: select, launch, stop, open, filter, zoom, spin, fit, say, mission, and more. The hub shows who is driving in the top bar. See `GROK.md` for the full list.

## The aura

Four additive layers wrap the brain: a breathing aura field with essence wisps rising off the shell, a fresnel atmosphere at the silhouette, wavy essence bands on tilted orbits, and drifting motes. All of them swell when it listens or speaks. Colors come from `brand.json` (`aura.primary`, `secondary`, `accent`, `mote`).

## White label and selling it

- `brand.json` holds the product name, tagline, owner, the paragraph the AI reads about the business, its voice, and the aura colors. Nothing brand specific is hard coded in the page.
- `sample/` is what a buyer gets: a neutral brand, an 8 tool demo registry, empty missions, a buyer README and AGENTS guide.
- `./package.sh` builds `dist/BRAIN-<date>.zip`. It never ships your registry, missions, brand, calendar or logs, renames the owner tag and the login service, and refuses to build if any private string (names, domains, Supabase refs) slips into the zip.

## Live demo

`./build-site.sh` builds `dist/site/`: the WHOBRAIN look with demo tools and a generic AI context, plus a leak check. Deployed to Netlify site `whobrain` (https://whobrain.netlify.app). On a static host the hub runs in demo mode: browsing, the globe, voice and local commands work; launching tools and the AI chat need `serve.py` on your own machine.

## Your own data stays local

`registry.json`, `missions.json`, `brand.json` and `GROK.md` are git-ignored: they hold the owner's real projects and notes. A fresh clone runs on the demo copies in `sample/` until you create your own.
