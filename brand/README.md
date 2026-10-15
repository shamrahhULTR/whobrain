# WHOBRAIN brand assets

A whosystems product. Same family DNA (Instrument Sans Bold, ink / paper / signal green),
its own mark: a sphere split into two hemispheres (the brain) with the whosystems
signal node breaking out of the upper right.

## Which file to use

| Need | File |
|------|------|
| Logo on a dark background | `whobrain-lockup-paper.svg` |
| Logo on a light background | `whobrain-lockup-ink.svg` |
| Logo with "BY WHOSYSTEMS" (endorsed) | `whobrain-lockup-stacked-paper.svg` / `-ink.svg` |
| Wordmark only | `whobrain-wordmark-paper.svg` (dark bg) / `-ink.svg` (light bg) |
| App tile / avatar (SVG) | `whobrain-mark-dark.svg` (default) / `-light.svg` |
| Mark with no tile, transparent | `whobrain-mark-glyph-paper.svg` (dark bg) / `-ink.svg` (light bg) |
| App icon PNGs | `whobrain-icon-1024.png`, `-512`, `-192`, `-180` (apple-touch), `-32` (favicon) |
| Square avatar (Discord, X, stores) | `whobrain-avatar-1024.png` |
| Link preview / OG image | `whobrain-social-1200x630.png` |
| Send to a designer or printer | `whobrain-logo-pack.pdf` |

All type is outlined to paths, so nothing depends on the font being installed.

## Colors

| Token | Hex | Use |
|-------|-----|-----|
| Ink | `#0C0E0D` | backgrounds, type on light |
| Tile | `#191C1A` | the mark tile on dark surfaces |
| Signal | `#9BE15D` | the node, on dark |
| Signal deep | `#5CA92E` | the node, on light |
| Paper | `#F5F5F3` | type and mark on dark |

## Type

Instrument Sans Bold, ALL CAPS, letter spacing -0.035em: the exact whosystems wordmark
setting, in caps. The lime node is the dot over the I.

## Rules

- The fissure and the ring around the node are the same width. Never close the fissure.
- Never recolor the node, rotate the mark, or reset the wordmark in another font or weight.
- Clear space equal to the node's diameter. Minimum 16 px for the mark, 96 px wide for the wordmark.
- No em dashes in copy next to the logo.

## Regenerate

```
python3 brain/brand/_src/gen_whobrain.py
```

Needs fontTools and Google Chrome (headless). Writes every SVG, PNG and the PDF.
