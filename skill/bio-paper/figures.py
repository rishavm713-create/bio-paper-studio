"""Draw question figures from data (never from free drawing).

A question may carry "figure": {"kind": ..., ...}. Kinds:
  graph    {"x": "label", "y": "label", "series": [{"name": "A", "points": [[x, y], ...]}]}
  bar      {"x": "label", "y": "label", "labels": ["a", "b"], "values": [3, 5]}
  table    {"head": ["Cross", "Ratio"], "rows": [["AaBb x aabb", "1:1:1:1"]]}
  pedigree {"members": [{"id": "I-1", "sex": "M|F|U", "affected": true, "carrier": false,
                         "dead": false, "spouse": "I-2", "parents": ["I-1", "I-2"]}]}
           generation = depth from parents; list spouses next to each other.
  plasmid  {"name": "pBR322", "size": 4361, "features": [{"name": "ampR", "start": 3293, "end": 4153}],
            "sites": [{"name": "EcoRI", "pos": 4359}]}
svg(fig) returns inline SVG for HTML/PDF; tikz(fig) returns LaTeX (pdfLaTeX, tikz only).
"""
import math
from html import escape

# ---- one geometry, two backends -------------------------------------------------
# Shapes in SVG coordinates (y down): ("line", x1, y1, x2, y2, w), ("poly", pts, w, fill),
# ("rect", x, y, w, h, fill), ("circ", cx, cy, r, fill), ("text", x, y, s, anchor, size)


def _graph(f, bars=False):
    W, H, L, B, T, R = 360, 220, 48, 36, 12, 12
    sh = []
    if bars:
        labels, vals = f.get("labels", []), [float(v) for v in f.get("values", [])]
        xs, ys = list(range(len(vals))), vals
        xmin, xmax = -0.5, len(vals) - 0.5
    else:
        pts = [p for s in f.get("series", []) for p in s.get("points", [])]
        xs, ys = [float(p[0]) for p in pts] or [0, 1], [float(p[1]) for p in pts] or [0, 1]
        xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(0.0, min(ys)), max(ys) or 1.0
    if xmax == xmin:
        xmax = xmin + 1
    step = 10 ** math.floor(math.log10((ymax - ymin) / 4 or 1))
    step *= next(m for m in (1, 2, 2.5, 5, 10) if (ymax - ymin) / (step * m) <= 4)
    ymax = ymin + step * 4
    px = lambda x: L + (x - xmin) / (xmax - xmin) * (W - L - R)
    py = lambda y: H - B - (y - ymin) / (ymax - ymin) * (H - B - T)
    sh += [("line", L, T, L, H - B, 1.2), ("line", L, H - B, W - R, H - B, 1.2)]
    for k in range(5):  # y ticks
        y = ymin + (ymax - ymin) * k / 4
        sh += [("line", L - 3, py(y), L, py(y), 0.8), ("text", L - 5, py(y) + 3, f"{y:.3g}", "end", 8)]
    if bars:
        bw = (W - L - R) / max(len(vals), 1) * 0.55
        for i, v in enumerate(vals):
            sh.append(("rect", px(i) - bw / 2, py(v), bw, py(ymin) - py(v), "#999"))
            sh.append(("text", px(i), H - B + 12, str(labels[i]) if i < len(labels) else "", "middle", 8))
    else:
        for k in range(5):
            x = xmin + (xmax - xmin) * k / 4
            sh += [("line", px(x), H - B, px(x), H - B + 3, 0.8), ("text", px(x), H - B + 12, f"{x:.3g}", "middle", 8)]
        for j, s in enumerate(f.get("series", [])):
            p = [(px(float(a)), py(float(b))) for a, b in s.get("points", [])]
            if len(p) > 1:
                sh.append(("poly", p, 1.4, None))
            for x, y in p:
                sh.append(("circ", x, y, 2.2, "#111" if j % 2 == 0 else "#fff"))
            if s.get("name") and p:
                sh.append(("text", p[-1][0] - 2, p[-1][1] - 6, s["name"], "end", 8))
    sh.append(("text", (L + W - R) / 2, H - 6, f.get("x", ""), "middle", 9))
    sh.append(("text", 10, (T + H - B) / 2, f.get("y", ""), "vert", 9))
    return W, H, sh


def _pedigree(f):
    ms = {m["id"]: m for m in f.get("members", [])}
    order = [m["id"] for m in f.get("members", [])]

    def gen(i, seen=()):
        m = ms[i]
        if m.get("parents") and m["parents"][0] in ms and i not in seen:
            return 1 + gen(m["parents"][0], seen + (i,))
        sp = m.get("spouse")
        if sp in ms and ms[sp].get("parents") and i not in seen:
            return gen(sp, seen + (i,))
        return 0
    rows = {}
    for i in order:
        rows.setdefault(gen(i), []).append(i)
    S, G, size = 46, 70, 22
    width = max(len(r) for r in rows.values()) * S + 40
    pos = {}
    for g, ids in rows.items():
        x0 = (width - (len(ids) - 1) * S) / 2
        for k, i in enumerate(ids):
            pos[i] = (x0 + k * S, 24 + g * G)
    sh, h = [], size / 2
    done = set()
    for i in order:  # marriage lines
        sp = ms[i].get("spouse")
        if sp in pos and (sp, i) not in done:
            done.add((i, sp))
            (x1, y), (x2, _) = pos[i], pos[sp]
            sh.append(("line", min(x1, x2) + h, y, max(x1, x2) - h, y, 1.2))
    fam = {}
    for i in order:
        p = ms[i].get("parents")
        if p and all(a in pos for a in p[:2]):
            fam.setdefault(tuple(sorted(p[:2])), []).append(i)
    for (a, b), kids in fam.items():
        mx, py_ = (pos[a][0] + pos[b][0]) / 2, pos[a][1]
        ky = pos[kids[0]][1] - h - 14
        sh.append(("line", mx, py_, mx, ky, 1.2))
        xs = [pos[k][0] for k in kids] + [mx]
        sh.append(("line", min(xs), ky, max(xs), ky, 1.2))
        for k in kids:
            sh.append(("line", pos[k][0], ky, pos[k][0], pos[k][1] - h, 1.2))
    for i in order:
        m, (x, y) = ms[i], pos[i]
        fill = "#111" if m.get("affected") else "#fff"
        sx = str(m.get("sex", "U")).upper()[:1]
        if sx == "M":
            sh.append(("rect", x - h, y - h, size, size, fill))
        elif sx == "F":
            sh.append(("circ", x, y, h, fill))
        else:
            sh.append(("poly", [(x, y - h), (x + h, y), (x, y + h), (x - h, y), (x, y - h)], 1.2, fill))
        if m.get("carrier") and not m.get("affected"):
            sh.append(("circ", x, y, 3.5, "#111"))
        if m.get("dead"):
            sh.append(("line", x - h - 4, y + h + 4, x + h + 4, y - h - 4, 1.2))
        sh.append(("text", x, y + h + 12, i, "middle", 8))
    return width, 24 + max(rows) * G + 36, sh


def _plasmid(f):
    W = H = 260
    cx, cy, r, size = W / 2, H / 2, 80, float(f.get("size", 1)) or 1
    ang = lambda p: 2 * math.pi * float(p) / size - math.pi / 2
    pt = lambda p, rr: (cx + rr * math.cos(ang(p)), cy + rr * math.sin(ang(p)))
    sh = [("circ", cx, cy, r, None)]
    for ft in f.get("features", []):
        a, b = float(ft["start"]), float(ft["end"])
        if b < a:
            b += size
        n = max(int((b - a) / size * 60), 2)
        arc = [pt(a + (b - a) * k / n, r) for k in range(n + 1)]
        sh.append(("poly", arc, 6, None))
        mid = pt((a + b) / 2, r - 18)
        sh.append(("text", mid[0], mid[1] + 3, ft.get("name", ""), "middle", 8))
    for s in f.get("sites", []):
        p1, p2, p3 = pt(s["pos"], r - 4), pt(s["pos"], r + 10), pt(s["pos"], r + 20)
        sh.append(("line", p1[0], p1[1], p2[0], p2[1], 1))
        sh.append(("text", p3[0], p3[1] + 3, f"{s.get('name','')} ({s['pos']})", "end" if p3[0] < cx - 5 else "start" if p3[0] > cx + 5 else "middle", 8))
    sh.append(("text", cx, cy - 2, f.get("name", ""), "middle", 10))
    sh.append(("text", cx, cy + 12, f"{f.get('size', '')} bp", "middle", 8))
    return W, H, sh


KINDS = {"graph": _graph, "bar": lambda f: _graph(f, bars=True), "pedigree": _pedigree, "plasmid": _plasmid}


def _shapes(fig):
    return KINDS[fig["kind"]](fig)


def svg(fig):
    if fig.get("kind") == "table":
        head = "".join(f"<th>{escape(str(c))}</th>" for c in fig.get("head", []))
        rows = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in fig.get("rows", []))
        return f"<table class='fig'><tr>{head}</tr>{rows}</table>"
    W, H, sh = _shapes(fig)
    o = [f"<svg class='fig' viewBox='0 0 {W:.0f} {H:.0f}' width='{W:.0f}' height='{H:.0f}' "
         "xmlns='http://www.w3.org/2000/svg' font-family='Georgia,serif' stroke='#111' fill='none'>"]
    for s in sh:
        k = s[0]
        if k == "line":
            o.append(f"<line x1='{s[1]:.1f}' y1='{s[2]:.1f}' x2='{s[3]:.1f}' y2='{s[4]:.1f}' stroke-width='{s[5]}'/>")
        elif k == "poly":
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in s[1])
            o.append(f"<polyline points='{pts}' stroke-width='{s[2]}' fill='{s[3] or 'none'}'/>")
        elif k == "rect":
            o.append(f"<rect x='{s[1]:.1f}' y='{s[2]:.1f}' width='{s[3]:.1f}' height='{s[4]:.1f}' fill='{s[5]}'/>")
        elif k == "circ":
            o.append(f"<circle cx='{s[1]:.1f}' cy='{s[2]:.1f}' r='{s[3]:.1f}' fill='{s[4] or 'none'}'/>")
        elif k == "text":
            tr = f" transform='rotate(-90 {s[1]:.1f} {s[2]:.1f})'" if s[4] == "vert" else ""
            anc = "middle" if s[4] == "vert" else s[4]
            o.append(f"<text x='{s[1]:.1f}' y='{s[2]:.1f}' font-size='{s[5]}' text-anchor='{anc}' "
                     f"fill='#111' stroke='none'{tr}>{escape(str(s[3]))}</text>")
    return "".join(o) + "</svg>"


def tikz(fig, tex):
    """tex: the caller's LaTeX escaper."""
    if fig.get("kind") == "table":
        n = len(fig.get("head", [])) or len((fig.get("rows") or [[]])[0])
        o = [r"\par\smallskip\begin{center}\begin{tabular}{|" + "c|" * n + r"}\hline"]
        if fig.get("head"):
            o.append(" & ".join(r"\textbf{" + tex(str(c)) + "}" for c in fig["head"]) + r"\\\hline")
        o += [" & ".join(tex(str(c)) for c in r) + r"\\\hline" for r in fig.get("rows", [])]
        return "\n".join(o + [r"\end{tabular}\end{center}"])
    W, H, sh = _shapes(fig)
    u = 0.028  # cm per svg unit
    P = lambda x, y: f"({x * u:.2f},{(H - y) * u:.2f})"
    col = lambda c: "black" if c == "#111" else "gray!60" if c == "#999" else "white"
    o = [r"\par\smallskip\begin{center}\begin{tikzpicture}[line cap=round]"]
    for s in sh:
        k = s[0]
        if k == "line":
            o.append(f"\\draw[line width={s[5] * 0.6:.2f}pt] {P(s[1], s[2])} -- {P(s[3], s[4])};")
        elif k == "poly":
            path = " -- ".join(P(x, y) for x, y in s[1])
            o.append((f"\\filldraw[fill={col(s[3])}" if s[3] else "\\draw[") + f",line width={s[2] * 0.6:.2f}pt] {path};")
        elif k == "rect":
            o.append(f"\\filldraw[fill={col(s[5])}] {P(s[1], s[2] + s[4])} rectangle {P(s[1] + s[3], s[2])};")
        elif k == "circ":
            o.append((f"\\filldraw[fill={col(s[4])}]" if s[4] else "\\draw") + f" {P(s[1], s[2])} circle ({s[3] * u:.2f});")
        elif k == "text":
            anc = {"end": "east", "start": "west"}.get(s[4], "center")
            rot = ",rotate=90" if s[4] == "vert" else ""
            sz = r"\scriptsize" if s[5] <= 8 else r"\footnotesize"
            o.append(f"\\node[anchor={anc}{rot},inner sep=1pt] at {P(s[1], s[2] - s[5] * 0.35)} {{{sz} {tex(str(s[3]))}}};")
    return "\n".join(o + [r"\end{tikzpicture}\end{center}"])


def check(fig):
    """Return a problem string or ''."""
    k = fig.get("kind")
    if k not in list(KINDS) + ["table"]:
        return f"unknown figure kind {k!r}"
    try:
        if k == "pedigree":
            ids = {m["id"] for m in fig.get("members", [])}
            for m in fig["members"]:
                for p in (m.get("parents") or []) + ([m["spouse"]] if m.get("spouse") else []):
                    if p not in ids:
                        return f"pedigree member {m['id']} points to missing {p}"
        if k == "table" and fig.get("head"):
            if any(len(r) != len(fig["head"]) for r in fig.get("rows", [])):
                return "table row length differs from header"
        _shapes(fig) if k != "table" else None
    except Exception as e:  # noqa: BLE001
        return f"figure data broken: {e}"
    return ""
