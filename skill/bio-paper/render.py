#!/usr/bin/env python3
"""Render a bio-paper JSON into print-ready HTML and PDF.
Usage: render.py paper.json [--no-key] [--format=pdf|tex|both]
"""
import html, json, os, subprocess, sys

import pathlib, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures
CHROME = next((c for c in (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    shutil.which("google-chrome") or "", shutil.which("chromium") or "") if c and os.path.exists(c)), "")
CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11.5pt; color: #111; line-height: 1.4; }
h1 { text-align: center; font-size: 17pt; margin: 0 0 4px; }
.meta { display: flex; justify-content: space-between; border-top: 2px solid #111; border-bottom: 2px solid #111;
        padding: 5px 0; margin: 6px 0 10px; font-size: 10.5pt; }
.instr { font-size: 10pt; margin: 0 0 12px; padding-left: 18px; }
h2 { font-size: 12.5pt; background: #eee; padding: 3px 6px; margin: 14px 0 8px; }
.q { margin: 0 0 11px; break-inside: avoid; }
.qt { white-space: pre-wrap; }
.tag { font-size: 9pt; color: #555; }
.opts { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 18px; margin: 4px 0 0 22px; }
.nat { margin: 4px 0 0 22px; color: #555; }
.key { page-break-before: always; }
table { border-collapse: collapse; width: 100%; font-size: 10.5pt; margin-bottom: 12px; }
td, th { border: 1px solid #999; padding: 3px 5px; text-align: center; }
.figw { margin: 6px 0 4px 22px; break-inside: avoid; }
.fig { max-width: 100%; }
table.fig { width: auto; margin: 0; }
.sol { margin: 0 0 7px; break-inside: avoid; }
"""


def esc(s):
    return html.escape(str(s))


def build(p, with_key=True):
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(p['title'])}</title>"
           f"<style>{CSS}</style></head><body>"]
    qs = [q for s in p["sections"] for q in s["questions"]]
    total = sum(q.get("marks", 0) for q in qs)
    out.append(f"<h1>{esc(p['title'])}</h1>")
    out.append(f"<div class='meta'><span>{esc(p.get('exam',''))} · {esc(p.get('type',''))} · "
               f"Level: {esc(p.get('level',''))}</span><span>Questions: {len(qs)}</span>"
               f"<span>Max marks: {total:g}</span><span>Time: {esc(p.get('time',''))}</span></div>")
    instr = list(p.get("instructions", []))
    if p.get("marking"):
        instr.append("Marking: " + p["marking"])
    if instr:
        out.append("<ol class='instr'>" + "".join(f"<li>{esc(i)}</li>" for i in instr) + "</ol>")
    n = 0
    for s in p["sections"]:
        out.append(f"<h2>{esc(s['name'])}</h2>")
        for q in s["questions"]:
            n += 1
            tag = f"[{esc(q.get('type','MCQ'))}, {q.get('marks',''):g} mark{'s' if q.get('marks',1) != 1 else ''}]"
            out.append(f"<div class='q'><b>Q{n}.</b> <span class='tag'>{tag}</span> <span class='qt'>{esc(q['q'])}</span>")
            if q.get("figure"):
                out.append("<div class='figw'>" + figures.svg(q["figure"]) + "</div>")
            if q.get("options"):
                out.append("<div class='opts'>" + "".join(
                    f"<div>({chr(65+i)}) {esc(o)}</div>" for i, o in enumerate(q["options"])) + "</div>")
            else:
                out.append("<div class='nat'>Answer: ____________</div>")
            out.append("</div>")
    if with_key:
        out.append("<div class='key'><h1>Answer Key</h1><table><tr>")
        for i, q in enumerate(qs, 1):
            out.append(f"<td><b>{i}</b><br>{esc(q['answer'])}</td>")
            if i % 10 == 0 and i < len(qs):
                out.append("</tr><tr>")
        out.append("</tr></table><h2>Solutions</h2>")
        for i, q in enumerate(qs, 1):
            out.append(f"<div class='sol'><b>Q{i}. ({esc(q['answer'])})</b> {esc(q.get('solution',''))}</div>")
        out.append("</div>")
    out.append("</body></html>")
    return "".join(out)


TEX_MAP = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
           "−": "$-$", "–": "--", "—": "---", "→": r"$\rightarrow$", "←": r"$\leftarrow$", "⇌": r"$\rightleftharpoons$",
           "×": r"$\times$", "°": r"$^\circ$", "≥": r"$\geq$", "≤": r"$\leq$", "±": r"$\pm$", "≈": r"$\approx$",
           "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$", "λ": r"$\lambda$", "μ": r"$\mu$",
           "·": r"$\cdot$", "‘": "`", "’": "'", "“": "``", "”": "''", "²": r"$^2$", "³": r"$^3$", "₂": r"$_2$"}


def tex(s):
    s = "".join(TEX_MAP.get(c, c) for c in str(s))
    return s.replace("\n", r"\\ ")


def build_tex(p, with_key=True):
    qs = [q for s in p["sections"] for q in s["questions"]]
    total = sum(q.get("marks", 0) for q in qs)
    o = [r"""% Compiles with pdfLaTeX (Overleaf default). Upload this file to overleaf.com and press Recompile.
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=16mm]{geometry}
\usepackage{enumitem,tabularx,array,tikz}
\setlength{\parindent}{0pt}
\newcommand{\opts}[4]{\par\smallskip\begin{tabularx}{\linewidth}{@{\hspace{1.5em}}X X}(A) #1 & (B) #2\\ (C) #3 & (D) #4\end{tabularx}}
\begin{document}
"""]
    o.append(r"\begin{center}{\Large\bfseries " + tex(p["title"]) + r"}\end{center}" + "\n")
    o.append(r"\hrule\smallskip " + f"{tex(p.get('exam',''))} $\\cdot$ {tex(p.get('type',''))} $\\cdot$ Level: {tex(p.get('level',''))}"
             + r"\hfill " + f"Questions: {len(qs)} \\hfill Max marks: {total:g} \\hfill Time: {tex(p.get('time',''))}"
             + r"\smallskip\hrule\medskip" + "\n")
    instr = list(p.get("instructions", [])) + (["Marking: " + p["marking"]] if p.get("marking") else [])
    if instr:
        o.append(r"\begin{enumerate}[nosep,leftmargin=*]\small" + "".join(r"\item " + tex(i) for i in instr) + r"\end{enumerate}" + "\n")
    n = 0
    for s in p["sections"]:
        o.append(r"\section*{" + tex(s["name"]) + "}\n")
        for q in s["questions"]:
            n += 1
            o.append(r"\noindent\textbf{Q" + str(n) + ".} {\\footnotesize[" + tex(q.get("type", "MCQ"))
                     + f", {q.get('marks', ''):g} marks]}} " + tex(q["q"]))
            if q.get("figure"):
                o.append(figures.tikz(q["figure"], tex))
            opts = q.get("options") or []
            if len(opts) == 4:
                o.append(r"\opts{" + "}{".join(tex(x) for x in opts) + "}")
            elif opts:
                o.append(r"\begin{enumerate}[label=(\Alph*),nosep]" + "".join(r"\item " + tex(x) for x in opts) + r"\end{enumerate}")
            else:
                o.append(r"\par\hspace{1.5em}Answer: \rule{4cm}{0.4pt}")
            o.append(r"\par\medskip" + "\n")
    if with_key:
        o.append(r"\newpage\begin{center}{\Large\bfseries Answer Key}\end{center}" + "\n")
        o.append(r"\begin{tabular}{|" + "c|" * 10 + r"}\hline" + "\n")
        for i in range(0, len(qs), 10):
            row = qs[i:i + 10]
            o.append(" & ".join(f"\\textbf{{{i+j+1}}}: {tex(q['answer'])}" for j, q in enumerate(row))
                     + " &" * (10 - len(row)) + r"\\\hline" + "\n")
        o.append(r"\end{tabular}" + "\n" + r"\section*{Solutions}" + "\n")
        for i, q in enumerate(qs, 1):
            o.append(f"\\textbf{{Q{i}. ({tex(q['answer'])})}} {tex(q.get('solution',''))}\\par\\smallskip\n")
    o.append(r"\end{document}" + "\n")
    return "".join(o)


def check(p):
    """Automatic proofreading for human-type errors. Returns warning lines."""
    warns, seen, keys = [], {}, {}
    qs = [q for s in p["sections"] for q in s["questions"]]
    for i, q in enumerate(qs, 1):
        t, opts, ans = q.get("type", "MCQ"), q.get("options") or [], str(q.get("answer", "")).strip()
        norm = " ".join(q.get("q", "").lower().split())
        if not norm:
            warns.append(f"Q{i}: empty question text")
        elif norm in seen:
            warns.append(f"Q{i}: same question as Q{seen[norm]}")
        seen.setdefault(norm, i)
        if not ans:
            warns.append(f"Q{i}: no answer key")
        if not q.get("solution"):
            warns.append(f"Q{i}: no solution")
        if q.get("figure") and figures.check(q["figure"]):
            warns.append(f"Q{i}: {figures.check(q['figure'])}")
        if t in ("MCQ", "MSQ"):
            if len(opts) != 4:
                warns.append(f"Q{i}: has {len(opts)} options, expected 4")
            if len({o.strip().lower() for o in opts}) != len(opts):
                warns.append(f"Q{i}: two options are the same")
            letters = [a.strip().upper() for a in ans.split(",") if a.strip()]
            bad = [a for a in letters if a not in "ABCD"[:len(opts)] or len(a) != 1]
            if bad:
                warns.append(f"Q{i}: answer '{ans}' is not a valid option letter")
            if t == "MCQ" and len(letters) != 1:
                warns.append(f"Q{i}: MCQ must have exactly one answer, got '{ans}'")
            if t == "MCQ" and len(letters) == 1:
                keys[letters[0]] = keys.get(letters[0], 0) + 1
        elif t == "NAT":
            try:
                float(ans.replace(" ", "").split("to")[0])
            except ValueError:
                warns.append(f"Q{i}: NAT answer '{ans}' is not a number")
    lv = [q.get("difficulty") for q in qs if isinstance(q.get("difficulty"), (int, float))]
    want = {"Easy": (1, 2.4), "Medium": (2.5, 3.5), "Hard": (3.6, 5)}.get(p.get("level"))
    if want and len(lv) >= 5 and not want[0] <= sum(lv) / len(lv) <= want[1]:
        warns.append(f"Average difficulty {sum(lv)/len(lv):.1f} does not fit level {p['level']}: adjust questions")
    n = sum(keys.values())
    if n >= 8:
        for k, c in sorted(keys.items()):
            if c > n * 0.4:
                warns.append(f"Answer {k} is used {c} of {n} times: spread the answers more evenly")
    return warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    src = os.path.abspath(os.path.expanduser(args[0]))
    with open(src, encoding="utf-8") as f:
        paper = json.load(f)
    warns = check(paper)
    for w in warns:
        print("WARN", w)
    print(f"Checks: {len(warns)} warning(s)")
    with_key = "--no-key" not in sys.argv
    base = os.path.splitext(src)[0] + ("" if with_key else "-student")
    fmt = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--format=")), "pdf")
    if fmt in ("tex", "both"):
        with open(base + ".tex", "w", encoding="utf-8") as f:
            f.write(build_tex(paper, with_key))
        print("LaTeX:", base + ".tex")
        if fmt == "tex":
            return
    with open(base + ".html", "w", encoding="utf-8") as f:
        f.write(build(paper, with_key))
    print("HTML:", base + ".html")
    if CHROME:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--use-mock-keychain",
                        f"--print-to-pdf={base}.pdf", pathlib.Path(base + ".html").resolve().as_uri()],
                       check=True, capture_output=True)
        print("PDF:", base + ".pdf")
    else:
        try:  # no Chrome (for example claude.ai): try WeasyPrint
            from weasyprint import HTML
            HTML(base + ".html").write_pdf(base + ".pdf")
            print("PDF:", base + ".pdf")
        except Exception:
            print("No Chrome or WeasyPrint: run `pip install weasyprint` and retry, or open the HTML and print to PDF.")


if __name__ == "__main__":
    main()
