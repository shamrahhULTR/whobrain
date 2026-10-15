#!/bin/bash
# Build the public WHOBRAIN demo for static hosting (Netlify) -> brain/dist/site
# Brand comes from brand.json (look only); business context, tools and missions
# come from sample/ so nothing private is published.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/dist/site"
rm -rf "$OUT"; mkdir -p "$OUT"
cp "$HERE/index.html" "$OUT/"
cp -R "$HERE/brand-assets" "$OUT/"
cp "$HERE/sample/registry.json" "$HERE/sample/missions.json" "$OUT/"
python3 - "$HERE" "$OUT" <<'PY'
import json, sys
here, out = sys.argv[1], sys.argv[2]
brand = json.load(open(here + "/brand.json"))
demo = json.load(open(here + "/sample/brand.json"))
# keep the look, drop anything about the owner's business
for k in ("name", "tagline", "logo", "favicon", "theme", "aura", "assistant"):
    if k in brand: demo[k] = brand[k]
demo["context"] = "This is the public WHOBRAIN demo by whosystems. It maps a sample home-service business: sales, marketing and operations tools orbiting one brain."
open(out + "/brand.js", "w").write("window.BRAND = %s;" % json.dumps(demo))
open(out + "/brand.json", "w").write(json.dumps(demo, indent=2))
PY
cat > "$OUT/netlify.toml" <<'TOML'
[build]
  publish = "."
  command = ""

[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "SAMEORIGIN"
    Referrer-Policy = "strict-origin-when-cross-origin"

[[headers]]
  for = "/*.json"
  [headers.values]
    Cache-Control = "no-cache"
TOML
LEAK="$(cat "$HERE/.leakwords" 2>/dev/null || true)"   # private words, kept out of the repo
[ -n "$LEAK" ] || echo "note: no .leakwords file, skipping the private-word check" >&2
if [ -n "$LEAK" ] && grep -R -n -i -E "$LEAK" "$OUT"; then
  echo "LEAK CHECK FAILED" >&2; exit 1
fi
echo "site built: $OUT"; ls -R "$OUT"
