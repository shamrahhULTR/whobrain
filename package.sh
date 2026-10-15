#!/bin/bash
# Build a sellable BRAIN package with none of the owner's private data.
#
#   brain/package.sh            -> brain/dist/BRAIN-<date>.zip
#
# Ships: the hub, server, agent CLI, always-on installer, demo brand/registry,
# empty missions, buyer README and AGENTS guide. Never ships: registry.json,
# missions.json, brand.json, calendar.json, logs, parked experiments.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y-%m-%d)"
OUT="$HERE/dist"
STAGE="$OUT/stage/BRAIN"
rm -rf "$OUT/stage"; mkdir -p "$STAGE/brain"

cp "$HERE/index.html" "$HERE/serve.py" "$HERE/ctl.py" "$HERE/always-on.sh" "$STAGE/brain/"
cp "$HERE/sample/brand.json" "$HERE/sample/registry.json" "$HERE/sample/missions.json" "$STAGE/brain/"
cp "$HERE/sample/README.md" "$HERE/sample/AGENTS.md" "$STAGE/"

# owner-neutral labels for the buyer's copy
chmod +x "$STAGE/brain/always-on.sh"

# leak check: refuse to build if anything private slipped in
LEAK="$(cat "$HERE/.leakwords" 2>/dev/null || true)"   # private words, kept out of the repo
[ -n "$LEAK" ] || echo "note: no .leakwords file, skipping the private-word check" >&2
if [ -n "$LEAK" ] && grep -R -n -i -E "$LEAK|whosystem" "$OUT/stage"; then
  echo "LEAK CHECK FAILED: private strings above. Nothing was packaged." >&2; exit 1
fi
python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" "$STAGE/brain/brand.json" "$STAGE/brain/registry.json" "$STAGE/brain/missions.json"

(cd "$OUT/stage" && rm -f "../BRAIN-$STAMP.zip" && zip -qr "../BRAIN-$STAMP.zip" BRAIN)
rm -rf "$OUT/stage"
echo "packaged: $OUT/BRAIN-$STAMP.zip"
