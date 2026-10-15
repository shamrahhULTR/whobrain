#!/usr/bin/env python3
"""WHOBRAIN identity: mark, wordmark, lockups, app icons, social card, logo pack.

Run from anywhere:  python3 brain/brand/_src/gen_whobrain.py
Needs fontTools and Google Chrome (headless) for the PNG/PDF exports.

The mark is a sphere split into two hemispheres (the brain) with the whosystems
signal node breaking out of the upper right. Every negative space in the mark is
one width (CH): the fissure between hemispheres and the ring around the node.
Geometry is computed as plain paths (no masks) so it renders the same in every
browser, design tool, favicon and printer.
"""
import math, os, subprocess
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INK, PAPER, TILE_DARK = "#0C0E0D", "#F5F5F3", "#0C0E0D"
LIME, LIME_DEEP = "#9BE15D", "#5CA92E"
MUTE_DARK, MUTE_LIGHT = "#8C948A", "#6E7370"

# ---------------------------------------------------------------- mark geometry
CX, CY, R = 48.0, 50.0, 27.0      # the sphere
CH = 4.6                          # the one negative-space channel width
NODE_R = 7.0
NODE_ANG = math.radians(48)
NX, NY = CX + R * math.cos(NODE_ANG), CY - R * math.sin(NODE_ANG)
NOTCH = NODE_R + CH               # ring around the node == fissure width

def f(v): return f"{v:.4f}".rstrip("0").rstrip(".")

def mark_paths():
    xl, xr = CX - CH / 2, CX + CH / 2
    dy = math.sqrt(R * R - (CH / 2) ** 2)
    top, bot = CY - dy, CY + dy
    left = f"M{f(xl)} {f(top)}A{f(R)} {f(R)} 0 0 0 {f(xl)} {f(bot)}Z"
    # intersections of sphere and notch circle
    dx, dy2 = NX - CX, NY - CY
    d = math.hypot(dx, dy2)
    a = (R * R - NOTCH * NOTCH + d * d) / (2 * d)
    h = math.sqrt(R * R - a * a)
    ux, uy = dx / d, dy2 / d
    px, py = CX + a * ux, CY + a * uy
    p1 = (px - h * -uy, py - h * ux)   # nearer the top
    p2 = (px + h * -uy, py + h * ux)   # nearer the right
    if p1[1] > p2[1]: p1, p2 = p2, p1
    right = (f"M{f(xr)} {f(top)}A{f(R)} {f(R)} 0 0 1 {f(p1[0])} {f(p1[1])}"
             f"A{f(NOTCH)} {f(NOTCH)} 0 0 0 {f(p2[0])} {f(p2[1])}"
             f"A{f(R)} {f(R)} 0 0 1 {f(xr)} {f(bot)}Z")
    return left, right

LEFT, RIGHT = mark_paths()

def glyph(fg, node):
    return (f'<path fill="{fg}" d="{LEFT}"/><path fill="{fg}" d="{RIGHT}"/>'
            f'<circle cx="{f(NX)}" cy="{f(NY)}" r="{f(NODE_R)}" fill="{node}"/>')

def tile(bg, fg, node):
    return f'<rect width="96" height="96" rx="26" fill="{bg}"/>' + glyph(fg, node)

# glyph bounds (for transparent glyph files)
GX0, GX1 = CX - R, max(CX + R, NX + NODE_R)
GY0, GY1 = min(CY - R, NY - NODE_R), CY + R

# ------------------------------------------------------------------- wordmark
def font(w): return TTFont(os.path.join(HERE, f"InstrumentSans-{w}.ttf"))

def set_type(parts, size, track):
    """parts = [(text, weight)]. Returns list of (path_d, x, scale, part_index), info."""
    x, glyphs, cap, ibox = 0.0, [], 0.0, None
    for pi, (text, wt) in enumerate(parts):
        fo = font(wt); s = size / fo["head"].unitsPerEm
        cmap, hm, gs = fo.getBestCmap(), fo["hmtx"], fo.getGlyphSet()
        cap = max(cap, fo["OS/2"].sCapHeight * s)
        for ch in text:
            g = cmap[ord(ch)]
            pen = SVGPathPen(gs); gs[g].draw(pen)
            if ch == "I":
                bp = BoundsPen(gs); gs[g].draw(bp)
                b = bp.bounds
                ibox = (x + b[0] * s, x + b[2] * s)
            if ch != " ":
                glyphs.append((pen.getCommands(), x, s, pi))
            x += hm[g][0] * s + track * size
    x -= track * size
    return glyphs, {"w": x, "cap": cap, "ibox": ibox}

def type_svg(glyphs, fills):
    return "".join(f'<path fill="{fills[pi]}" transform="translate({x:.3f},0) scale({s:.6f},{-s:.6f})" d="{d}"/>'
                   for d, x, s, pi in glyphs)

WORD_PARTS = [("WHOBRAIN", 700)]   # the whosystems typeface and weight, in caps
WSIZE, WTRACK = 100.0, -0.035   # identical to the whosystems wordmark
WGLYPHS, WINFO = set_type(WORD_PARTS, WSIZE, WTRACK)
STEM = WINFO["ibox"][1] - WINFO["ibox"][0]
DOT_R = STEM * 0.62
DOT_CX = (WINFO["ibox"][0] + WINFO["ibox"][1]) / 2
DOT_CY = -WINFO["cap"] - STEM * 0.62 - DOT_R
W_TOP = DOT_CY - DOT_R

def wordmark(fg, node, dot=True):
    g = type_svg(WGLYPHS, [fg, fg])
    if dot:
        g += f'<circle cx="{DOT_CX:.3f}" cy="{DOT_CY:.3f}" r="{DOT_R:.3f}" fill="{node}"/>'
    return g

ENDORSE = set_type([("BY WHOSYSTEMS", 600)], 100.0, 0.34)

def svgdoc(vb, body, label="WHOBRAIN"):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{label}">\n{body}\n</svg>\n')

def write(name, text):
    with open(os.path.join(OUT, name), "w") as fh: fh.write(text)

# ------------------------------------------------------------------- SVG files
def build_svgs():
    write("whobrain-mark-dark.svg", svgdoc("0 0 96 96", tile(TILE_DARK, PAPER, LIME)))
    write("whobrain-mark-light.svg", svgdoc("0 0 96 96", tile(PAPER, INK, LIME_DEEP)))
    pad = 1.0
    gvb = f"{f(GX0-pad)} {f(GY0-pad)} {f(GX1-GX0+2*pad)} {f(GY1-GY0+2*pad)}"
    write("whobrain-mark-glyph-paper.svg", svgdoc(gvb, glyph(PAPER, LIME)))
    write("whobrain-mark-glyph-ink.svg", svgdoc(gvb, glyph(INK, LIME_DEEP)))

    w, cap = WINFO["w"], WINFO["cap"]
    wvb = f"-2 {W_TOP-2:.3f} {w+4:.3f} {-W_TOP+4:.3f}"
    write("whobrain-wordmark-paper.svg", svgdoc(wvb, wordmark(PAPER, LIME)))
    write("whobrain-wordmark-ink.svg", svgdoc(wvb, wordmark(INK, LIME_DEEP)))

    # horizontal lockup: tile height 120, caps = 40% of tile, centered on tile
    T = 120.0; k = 0.705882; gap = 154.588 - T   # same scale and spacing as the whosystems lockup
    base = T / 2 + cap * k / 2
    for name, bg, fg, node, stroke in [("ink", TILE_DARK, INK, LIME, ""),
                                        ("paper", "#191C1A", PAPER, LIME, ' stroke="rgba(245,245,243,0.14)" stroke-width="1.2"')]:
        tilefg = PAPER
        body = (f'<g transform="scale({T/96:.6f})"><rect width="96" height="96" rx="26" fill="{bg}"{stroke}/>'
                f'{glyph(tilefg, LIME)}</g>'
                f'<g transform="translate({T+gap:.3f},{base:.3f}) scale({k:.6f})">{wordmark(fg, LIME_DEEP if name=="ink" else LIME)}</g>')
        write(f"whobrain-lockup-{name}.svg", svgdoc(f"0 0 {T+gap+w*k:.3f} {T:.3f}", body))

    # stacked lockup with endorsement: mark, wordmark, BY WHOSYSTEMS
    eg, ei = ENDORSE
    for name, fg, node, mute, tbg, tstroke in [
            ("ink", INK, LIME_DEEP, MUTE_LIGHT, TILE_DARK, ""),
            ("paper", PAPER, LIME, MUTE_DARK, "#191C1A", ' stroke="rgba(245,245,243,0.14)" stroke-width="1.2"')]:
        Wd = 600.0; k = Wd / w
        T = 196.0; tx = (Wd - T) / 2
        wy = T + 58 - W_TOP * k       # wordmark top (dot) sits 70 below tile
        ek = (Wd * 0.62) / ei["w"]
        ey = wy + 46 + ei["cap"] * ek
        ex = (Wd - ei["w"] * ek) / 2
        H = ey + 6
        body = (f'<g transform="translate({tx:.3f},0) scale({T/96:.6f})"><rect width="96" height="96" rx="26" fill="{tbg}"{tstroke}/>'
                f'{glyph(PAPER, LIME)}</g>'
                f'<g transform="translate(0,{wy:.3f}) scale({k:.6f})">{wordmark(fg, node)}</g>'
                f'<g transform="translate({ex:.3f},{ey:.3f}) scale({ek:.6f})">{type_svg(eg, [mute])}</g>')
        write(f"whobrain-lockup-stacked-{name}.svg", svgdoc(f"0 0 {Wd:.3f} {H:.3f}", body, "WHOBRAIN by whosystems"))

def raw(name):
    s = open(os.path.join(OUT, name)).read()
    return s.split("?>", 1)[1].strip()

# --------------------------------------------------------- PNG / PDF exports
def chrome(args):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1"] + args,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def shot(html, name, w, h, transparent=False):
    tmp = os.path.join(HERE, "_render.html")
    open(tmp, "w").write(html)
    extra = ["--default-background-color=00000000"] if transparent else []
    chrome(extra + [f"--window-size={w},{h}", f"--screenshot={os.path.join(OUT, name)}", "file://" + tmp])
    os.remove(tmp)

def page(w, h, inner, bg="transparent"):
    return (f'<!doctype html><meta charset=utf-8><style>*{{margin:0}}html,body{{width:{w}px;height:{h}px;'
            f'background:{bg};overflow:hidden}}svg{{display:block}}</style>{inner}')

FONTCSS = "@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');"

def build_pngs():
    md = raw("whobrain-mark-dark.svg")
    for px in (1024, 512, 192, 180, 32):
        shot(page(px, px, md.replace("<svg ", f'<svg width="{px}" height="{px}" ', 1)),
             f"whobrain-icon-{px}.png", px, px, transparent=True)
    # full-bleed square for stores / Discord / social avatars (no rounded corners)
    gp = raw("whobrain-mark-glyph-paper.svg").replace("<svg ", '<svg width="560" height="560" ', 1)
    shot(page(1024, 1024, f'<div style="width:1024px;height:1024px;display:flex;align-items:center;justify-content:center;'
              f'background:radial-gradient(52% 52% at 50% 46%, rgba(155,225,93,.16), rgba(155,225,93,0) 64%), {INK}">{gp}</div>'),
         "whobrain-avatar-1024.png", 1024, 1024)
    # social / OG card
    lk = raw("whobrain-lockup-paper.svg").replace("<svg ", '<svg width="640" ', 1)
    card = f'''<!doctype html><meta charset=utf-8><style>{FONTCSS}*{{margin:0}}
    html,body{{width:1200px;height:630px;overflow:hidden}}
    .c{{width:1200px;height:630px;box-sizing:border-box;padding:0 96px;display:flex;flex-direction:column;justify-content:center;
      font-family:'Instrument Sans',-apple-system,sans-serif;color:{PAPER};
      background:radial-gradient(60% 80% at 82% 18%, rgba(155,225,93,.14), rgba(155,225,93,0) 60%), {INK}}}
    .t{{margin-top:44px;font-size:30px;font-weight:600;letter-spacing:-.01em;max-width:820px;line-height:1.25}}
    .t b{{color:{LIME};font-weight:600}}
    .e{{margin-top:22px;font-size:15px;font-weight:600;letter-spacing:.34em;color:{MUTE_DARK}}}
    </style><div class="c">{lk}<p class="t">One brain over every tool your business runs.<br><b>Launch it, ask it, let it work.</b></p>
    <p class="e">BY WHOSYSTEMS</p></div>'''
    shot(card, "whobrain-social-1200x630.png", 1200, 630)

def build_pack():
    lk_i, lk_p = raw("whobrain-lockup-ink.svg"), raw("whobrain-lockup-paper.svg")
    st_i, st_p = raw("whobrain-lockup-stacked-ink.svg"), raw("whobrain-lockup-stacked-paper.svg")
    m_d, m_l = raw("whobrain-mark-dark.svg"), raw("whobrain-mark-light.svg")
    w_i, w_p = raw("whobrain-wordmark-ink.svg"), raw("whobrain-wordmark-paper.svg")
    # construction diagram: sphere, fissure, node, one channel width
    cons = f'''<svg viewBox="0 0 96 96"><rect width="96" height="96" rx="26" fill="{INK}"/>{glyph("#2A2F2B", "#2A2F2B")}
      <g fill="none" stroke="{LIME}" stroke-width=".35">
        <circle cx="{f(CX)}" cy="{f(CY)}" r="{f(R)}" stroke-dasharray="1.2 1"/>
        <circle cx="{f(NX)}" cy="{f(NY)}" r="{f(NOTCH)}" stroke-dasharray="1.2 1"/>
        <line x1="{f(CX)}" y1="16" x2="{f(CX)}" y2="84" stroke-dasharray="1.2 1"/>
        <line x1="{f(CX)}" y1="{f(CY)}" x2="{f(NX)}" y2="{f(NY)}"/>
      </g><circle cx="{f(CX)}" cy="{f(CY)}" r=".9" fill="{LIME}"/><circle cx="{f(NX)}" cy="{f(NY)}" r=".9" fill="{LIME}"/></svg>'''
    css = f'''{FONTCSS}@page{{size:Letter;margin:0}}
    *{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
    html,body{{margin:0;font-family:'Instrument Sans',-apple-system,sans-serif}}
    .pg{{width:8.5in;height:11in;padding:.75in .85in .95in;page-break-after:always;position:relative;overflow:hidden}}
    .l{{background:{PAPER};color:{INK}}} .d{{background:{INK};color:{PAPER}}}
    .ey{{font-size:8.5pt;letter-spacing:.34em;font-weight:600;opacity:.5;margin:0 0 10px}}
    h1{{font-size:24pt;font-weight:700;letter-spacing:.06em;margin:0 0 4px}}
    .tag{{font-size:10.5pt;opacity:.6;margin:0 0 26px}}
    .cap{{font-size:7.5pt;letter-spacing:.24em;font-weight:600;opacity:.45;margin:0 0 10px}}
    .hero{{display:flex;align-items:center;justify-content:center;border-radius:14px;padding:38px 0;margin:0 0 18px}}
    .l .hero,.l .cell{{background:#ECECE8}} .d .hero,.d .cell{{background:#191C1A}}
    .hero svg{{height:78px}} .row{{display:flex;gap:14px;margin:0 0 18px}}
    .cell{{flex:1;border-radius:12px;display:flex;align-items:center;justify-content:center;min-height:118px;padding:18px}}
    .cell.m svg{{height:78px}} .cell.w svg{{height:30px}} .cell.s svg{{height:112px}} .cell.c svg{{height:128px}}
    .note{{font-size:9pt;line-height:1.6;opacity:.7}} .note b{{opacity:1}}
    .sw{{display:flex;gap:12px}} .chip{{flex:1;border-radius:10px;overflow:hidden;border:1px solid rgba(128,128,128,.18)}}
    .chip i{{display:block;height:54px}} .chip span{{display:block;padding:8px 10px;font-size:8pt;background:#191C1A;color:{PAPER}}}
    .chip b{{display:block;font-size:9pt;font-weight:600}}
    .foot{{position:absolute;left:.85in;right:.85in;bottom:.5in;display:flex;justify-content:space-between;font-size:7.5pt;letter-spacing:.22em;opacity:.4}}
    .sizes{{display:flex;align-items:flex-end;gap:22px}} .sizes svg{{display:block}}'''
    html = f'''<!doctype html><meta charset=utf-8><style>{css}</style>
    <section class="pg l"><p class="ey">IDENTITY · 01</p><h1>WHOBRAIN</h1>
      <p class="tag">One brain over every tool your business runs. A whosystems product.</p>
      <p class="cap">PRIMARY LOCKUP</p><div class="hero">{lk_i}</div>
      <p class="cap">MARK · STACKED LOCKUP</p>
      <div class="row"><div class="cell m">{m_d}</div><div class="cell s">{st_i}</div></div>
      <p class="cap">WORDMARK</p><div class="row"><div class="cell w">{w_i}</div></div>
      <p class="cap">THE IDEA</p>
      <p class="note"><b>A sphere split into two hemispheres</b>: the brain. The <b>signal node</b> is the same green node that
      sits on every whosystems mark, breaking out of the upper right. In the wordmark that node becomes the dot over the I.
      Set in Instrument Sans Bold, the whosystems typeface, with the exact whosystems spacing, set in caps.</p>
      <div class="foot"><span>WHOBRAIN</span><span>A WHOSYSTEMS PRODUCT</span></div></section>
    <section class="pg d"><p class="ey">IDENTITY · 02</p><h1>REVERSED</h1>
      <p class="tag">Use on near black and dark surfaces. This is the primary environment for the product.</p>
      <p class="cap">PRIMARY LOCKUP · REVERSED</p><div class="hero">{lk_p}</div>
      <p class="cap">CONSTRUCTION · STACKED LOCKUP</p>
      <div class="row"><div class="cell c">{cons}</div><div class="cell s">{st_p}</div></div>
      <p class="cap">MINIMUM SIZES</p>
      <div class="row"><div class="cell"><div class="sizes">
        {m_l.replace("<svg ", '<svg width="64" height="64" ', 1)}{m_l.replace("<svg ", '<svg width="32" height="32" ', 1)}
        {m_l.replace("<svg ", '<svg width="16" height="16" ', 1)}</div></div>
        <div class="cell w">{w_p}</div></div>
      <p class="cap">COLOR · SHARED WITH WHOSYSTEMS</p>
      <div class="sw">
        <div class="chip"><i style="background:{INK}"></i><span><b>Ink</b>#0C0E0D</span></div>
        <div class="chip"><i style="background:#191C1A"></i><span><b>Tile</b>#191C1A</span></div>
        <div class="chip"><i style="background:{LIME}"></i><span><b>Signal</b>#9BE15D</span></div>
        <div class="chip"><i style="background:{LIME_DEEP}"></i><span><b>Signal deep</b>#5CA92E</span></div>
        <div class="chip"><i style="background:{PAPER}"></i><span><b>Paper</b>#F5F5F3</span></div></div>
      <p class="note" style="margin-top:16px">One rule holds the mark together: the fissure and the ring around the node are the
      same width. Keep clear space equal to the node's diameter. Minimum 16 px for the mark, 96 px wide for the wordmark.
      Never recolor the node, rotate the mark, or close the fissure.</p>
      <div class="foot"><span>WHOBRAIN</span><span>A WHOSYSTEMS PRODUCT</span></div></section>'''
    tmp = os.path.join(HERE, "_pack.html"); open(tmp, "w").write(html)
    chrome(["--no-pdf-header-footer", "--virtual-time-budget=4000",
            f"--print-to-pdf={os.path.join(OUT, 'whobrain-logo-pack.pdf')}", "file://" + tmp])
    # preview PNGs of both pages for quick review
    for i, sel in enumerate(("l", "d"), 1):
        one = html.replace('<section class="pg ' + ("d" if sel == "l" else "l"), '<section style="display:none" class="pg x')
        open(tmp, "w").write(one)
        chrome(["--virtual-time-budget=4000", "--window-size=816,1056",
                f"--screenshot={os.path.join(HERE, f'preview-{i}.png')}", "file://" + tmp])
    os.remove(tmp)

if __name__ == "__main__":
    build_svgs(); print("svgs ok")
    build_pngs(); print("pngs ok")
    build_pack(); print("pack ok")
    print("node", f(NX), f(NY), "notch", NOTCH, "| word w", round(WINFO["w"], 1), "cap", round(WINFO["cap"], 1))
