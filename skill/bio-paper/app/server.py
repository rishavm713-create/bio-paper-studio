#!/usr/bin/env python3
"""Bio Paper Studio: a local web interface for the bio-paper skill.
Run: python3 ~/.claude/skills/paper-studio/app/server.py   (opens http://127.0.0.1:8765)
Only listens on this computer. Papers are written to ~/BioPapers.
Big papers are written by several Claude Code writers in parallel, then one reviewer checks and renders.
"""
import base64, hashlib, hmac, io, json, secrets, sys, os, random, re, shutil, subprocess, tempfile, threading, time, uuid, webbrowser, zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SKILL_MD = os.path.join(SKILL, "SKILL.md")
RENDER = os.path.join(SKILL, "render.py")
OUT = os.path.expanduser("~/BioPapers")
PINF = os.path.expanduser("~/.config/bio-paper/pin")
TOKEN = secrets.token_hex(24)


def pin_hash(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200000).hex()


def pin_ok(pin):
    salt, h = open(PINF).read().split(":")
    return hmac.compare_digest(pin_hash(pin, bytes.fromhex(salt)), h)


def pin_set(pin):
    os.makedirs(os.path.dirname(PINF), mode=0o700, exist_ok=True)
    salt = os.urandom(16)
    fd = os.open(PINF, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(salt.hex() + ":" + pin_hash(pin, salt))
INBOX = os.path.join(OUT, "inbox")
CLAUDE = shutil.which("claude") or next((c for c in (
    "/opt/homebrew/bin/claude", "/usr/local/bin/claude", os.path.expanduser("~/.local/bin/claude"),
    os.path.expanduser("~/.local/bin/claude.exe"), os.path.expanduser("~/AppData/Roaming/npm/claude.cmd"))
    if os.path.exists(c)), "claude")
PY = sys.executable or "python3"
MODEL = os.environ.get("BIO_MODEL", "sonnet")
MAXW = 6  # parallel writers
TYPES, LEVELS, FORMATS = {"Mock", "DPP"}, {"Easy", "Medium", "Hard", "Mixed"}, {"pdf", "tex", "both"}
JOBS = {}

REFS = next((r for r in (os.path.join(SKILL, "references"), os.path.join(os.path.dirname(os.path.dirname(SKILL)), "references"))
             if os.path.isdir(os.path.join(r, "exams"))), os.path.join(SKILL, "references"))


def load_profiles():
    """Exams come from references/exams/*.json and subjects from references/subjects/<name>/subject.json:
    adding an exam or subject is data only."""
    subjects, exams = {}, {}
    sdir, edir = os.path.join(REFS, "subjects"), os.path.join(REFS, "exams")
    for n in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        f = os.path.join(sdir, n, "subject.json")
        if os.path.isfile(f):
            with open(f, encoding="utf-8") as fh:
                subjects[n] = json.load(fh)
    for n in sorted(os.listdir(edir)) if os.path.isdir(edir) else []:
        if n.endswith(".json"):
            with open(os.path.join(edir, n), encoding="utf-8") as fh:
                e = json.load(fh)
            e["layout"] = [(x["name"], x["type"], x["marks"], x["count"]) for x in e["sections"]]
            exams[e["name"]] = e
    return subjects, dict(sorted(exams.items(), key=lambda kv: kv[1].get("order", 99)))


SUBJECTS, EXAMS = load_profiles()


def pick(selectors):
    """Chapter names matching [{"subject", "group"?, "tag"?}, ...], in selector order, then book order."""
    out = []
    for sel in selectors:
        for c in SUBJECTS.get(sel["subject"], {}).get("chapters", []):
            if sel.get("group", c["group"]) == c["group"] and (not sel.get("tag") or sel["tag"] in c.get("tags", [])) \
                    and c["name"] not in out:
                out.append(c["name"])
    return out


def chapter_groups(ex):
    """[(group label, [chapters])] for the app's chapter chips."""
    groups = {}
    for sel in ex["chapter_groups"]:
        for c in SUBJECTS.get(sel["subject"], {}).get("chapters", []):
            if sel.get("group", c["group"]) == c["group"]:
                groups.setdefault(c["group"], []).append(c["name"])
    return list(groups.items())


FOCUS = ["basic facts, definitions and examples", "processes and mechanisms", "application, data and tricky statements",
         "exceptions, comparisons and assertion-reason", "match-the-column and figure-based (pedigree, graph, table, plasmid map as figure data)", "experiments and numericals"]


def clean(s, n=400):
    return re.sub(r"[^\w\s.,:;()&/+\-'’]", "", str(s))[:n].strip()


def scale(layout, count):
    base = sum(g[3] for g in layout)
    ns = [round(g[3] * count / base) for g in layout]
    while sum(ns) != count:
        if sum(ns) < count:
            ns[max(range(len(ns)), key=lambda k: layout[k][3] - ns[k])] += 1
        else:
            ns[max(range(len(ns)), key=lambda k: ns[k])] -= 1
    return [(g[0], g[1], g[2], n) for g, n in zip(layout, ns) if n > 0]


def chapter_pool(section, d):
    if d["chapters"]:
        return d["chapters"]
    ex = EXAMS[d["exam"]]
    sec = next((x for x in ex["sections"] if x["name"] == section and x.get("pool")), None)
    return pick(sec["pool"] if sec else ex["pool"])


def plan(d):
    """Split a paper into parts that writers can do in parallel."""
    ex = EXAMS[d["exam"]]
    layout = ex["layout"]
    if d["type"] == "DPP" and not ex.get("dpp_keep_sections"):
        merged = {}
        for _, t, m, n in layout:
            merged[(t, m)] = merged.get((t, m), 0) + n
        layout = [("Questions", t, m, n) for (t, m), n in merged.items()]
    groups = scale(layout, d["count"])
    if d["count"] <= 12:  # small paper: one writer per question type, not per mark group
        merged = {}
        for s, t, m, n in groups:
            _, _, m0, n0 = merged.get(t, (s, t, m, 0))
            merged[t] = (s, t, max(m, m0), n0 + n)
        groups = list(merged.values())
    size = max(8, -(-d["count"] // MAXW))
    parts = []
    for s, t, m, n in groups:
        k = -(-n // size)
        for i in range(k):
            parts.append({"section": s, "type": t, "marks": m, "n": n // k + (1 if i < n % k else 0)})
    by = {}
    for p in parts:
        by.setdefault(p["section"], []).append(p)
    for s, ps in by.items():
        pool = chapter_pool(s, d)
        for i, p in enumerate(ps):
            if len(pool) >= len(ps):
                p["chapters"] = pool[i::len(ps)]
            else:
                p["chapters"], p["focus"] = pool, FOCUS[i % len(FOCUS)]
            if p["type"] == "MCQ":
                letters = list("ABCD" * (p["n"] // 4 + 1))[:p["n"]]
                random.shuffle(letters)
                p["answers"] = letters
    for i, p in enumerate(parts, 1):
        p["id"] = i
        p["label"] = f"{p['section']} · {p['n']} {p['type']}" + (f" · {p['marks']}m" if ex.get("marks_in_label") else "")
    return parts


def writer_prompt(d, p, path):
    mix = " (30% easy, 50% medium, 20% hard)" if d["level"] == "Mixed" else ""
    ex = EXAMS[d["exam"]]
    out = [f"You write one part of a {ex['subject_label'].lower()} {d['exam']} {d['type']}. Read {SKILL_MD} sections 2 and 3 "
           "(exam style and writing rules) and follow them exactly. Do not ask questions. Do not render anything.",
           f"Write exactly {p['n']} {p['type']} questions, {p['marks']} marks each, difficulty {d['level']}{mix}.",
           "Chapters for this part (cover them, weighted the way the real exam weights them): " + "; ".join(p["chapters"])]
    if ex.get("style"):
        out.append(f"{d['exam']} style: {ex['style']}")
    sub = next((SUBJECTS[n] for n in ex["subjects"] if SUBJECTS.get(n, {}).get("text_dir")), None)
    papers = (f"skim 1 or 2 past papers in {REFS}/papers/ whose names start with '{ex['papers_prefix']}' "
              "for the real exam style. ") if ex.get("papers_prefix") else ""
    if sub:
        book = sub.get("book", "NCERT")
        out.append(f"Before writing, read the {book} text for your chapters in {REFS}/{sub['text_dir']}/ (files are "
                   f"named {sub['text_names']}; if a .md is missing, read the .pdf of the same name)"
                   + (f" and {papers}" if papers else ". ") + f"Base every fact on {book}. Never copy a past question word for word.")
    elif papers:
        out.append("Before writing, " + papers + "Never copy a past question word for word.")
    prof = os.path.join(REFS, ex["profile"]) if ex.get("profile") else ""
    if os.path.isfile(prof):
        out.append(f"Read the exam profile {prof} first: match its topic weightage, question styles and trap "
                   "patterns, and use its difficulty rubric (1-5). Easy = mostly 1-2, Medium = mostly 3, "
                   "Hard = mostly 4-5, Mixed = the real exam mix. Add \"difficulty\": <1-5> to every question.")
    elif ex.get("weightage") or ex.get("difficulty"):
        out.append(f"Topic weightage: {ex.get('weightage', '')} Difficulty rubric (1-5): {ex.get('difficulty', '')} "
                   "Easy = mostly 1-2, Medium = mostly 3, Hard = mostly 4-5. Add \"difficulty\": <1-5> to every question.")
    if d.get("source"):
        out.append(f"The teacher gave her own NCERT chapter file: {d['source']}. Read it first. It is the source of "
                   "truth: base every question and solution only on it, and where any other reference disagrees, follow it.")
    if p.get("focus"):
        out.append(f"Other writers cover the same chapters, so focus on: {p['focus']}.")
    if p.get("answers"):
        out.append("The correct option for your questions, in order, must be: " + ", ".join(p["answers"]) + ".")
    if p["type"] == "NAT":
        out.append("NAT questions have no options and a single numeric answer (a range like '0.24 to 0.26' is allowed).")
    if p["type"] == "MSQ":
        out.append("MSQ answers have one or more correct options, written like 'A, C'. Vary how many are correct.")
    if d.get("notes"):
        out.append("Extra request from the teacher: " + d["notes"])
    out.append(f'Save ONLY this JSON to {path}: {{"questions": [{{"type": "{p["type"]}", "marks": {p["marks"]}, '
               '"q": "...", "options": ["...", "...", "...", "..."], "answer": "B", "solution": "..."}]}. '
               "Then reply DONE.")
    return "\n".join(out)


def reviewer_prompt(d, path, warns, short, fmt, student):
    out = [f"Follow the rules in {SKILL_MD}. Do not ask questions.",
           f"{path} is a complete {d['exam']} {d['type']} written in parts by several writers. Proofread every question "
           "with the section 6 checklist: wrong answer keys, two correct options, wrong facts, spelling and scientific "
           "names, near-duplicate questions across parts, solutions that disagree with the key. Fix every problem "
           "directly in the JSON (rewrite a duplicate as a new question on the same chapter). Keep the number of "
           "questions, their types and marks, and keep each MCQ's answer letter unless the key is wrong."]
    if short:
        out.append("Some parts came back short. Add these missing questions in the right section: " + "; ".join(short))
    out.append("Automatic check output:\n" + ("\n".join(warns) if warns else "no warnings"))
    out.append("Save the fixed JSON to the same file. Do not render it (the app does that). "
               "Reply with one short line saying what you fixed.")
    return "\n\n".join(out)


def norm_ans(a):
    return ",".join(sorted(re.findall(r"[A-D]", str(a).upper()))) or str(a).strip().lower()


def blind_prompt(src, out):
    return (f"Follow the rules in {SKILL_MD}. Do not ask questions. {src}\n\n"
            "Solve every question yourself, as a careful topper would, using NCERT and references/ when unsure. "
            "Do NOT look at any answer key, solutions or keyed answers in the paper; cover them. "
            f'Save only a JSON object to {out}, question number to your answer, for example {{"1": "B", "2": "A, C", "3": "0.25"}}. '
            "Reply with one line.")


def compare(keys, mine):
    """Rows where the blind solver disagrees with the key."""
    bad = []
    for k, v in keys.items():
        m = mine.get(str(k))
        if m is not None and norm_ans(m) != norm_ans(v):
            bad.append((str(k), str(v), str(m)))
    return bad


def clean_env():
    return {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE"))}


SIGNED_IN = False


def signed_in():
    """True when Claude Code can run here; checked once, before the first job, so a missing sign-in fails fast."""
    global SIGNED_IN
    if SIGNED_IN or os.environ.get("ANTHROPIC_API_KEY"):
        return True
    try:
        r = subprocess.run([CLAUDE, "auth", "status"], env=clean_env(), capture_output=True, text=True, timeout=30)
        SIGNED_IN = json.loads(r.stdout).get("loggedIn", True) is not False
    except (OSError, ValueError, subprocess.TimeoutExpired):
        SIGNED_IN = True  # older Claude Code without `auth status`: let the job try
    return SIGNED_IN


PREFS = os.path.join(os.path.dirname(PINF), "preferences.md")   # what the teacher asked to change, kept across papers
MY_STYLE = os.path.join(OUT, "my-style")                         # her own finished papers/solutions, used as style examples
LEARN_TAGS = ("part ", "write ", "solve ", "review")


def teacher_notes():
    """Standing instructions learned from the teacher, added to every writing, solving and review call."""
    out = []
    try:
        with open(PREFS, encoding="utf-8") as f:
            p = f.read().strip()[-6000:]
        if p:
            out.append("The teacher's standing preferences from earlier papers. Follow every one of them; "
                       "a newer line wins over an older one:\n" + p)
    except OSError:
        pass
    if os.path.isdir(MY_STYLE) and any(not n.startswith(".") for n in os.listdir(MY_STYLE)):
        out.append(f"{MY_STYLE} holds the teacher's own finished papers and solutions. Read one or two of them first "
                   "and match their question style, solution layout, length and tone (never copy their questions).")
    return ("\n\n" + "\n\n".join(out)) if out else ""


UPDATE_MSG = ("Your Claude Code is too old to run Bio Paper Studio safely. Update Claude Code (run  claude update  in "
              "Terminal or PowerShell), then try again.")
RESTRICTED = False
MAX_BYTES = 20_000_000  # largest .docx text or model output the app will read


def has_restricted():
    """The safety flags need a recent Claude Code; without them no job runs."""
    global RESTRICTED
    if not RESTRICTED:
        try:
            r = subprocess.run([CLAUDE, "--help"], env=clean_env(), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
            RESTRICTED = "--restricted" in r.stdout
        except (OSError, subprocess.TimeoutExpired):
            return False
    return RESTRICTED


@contextmanager
def scratch_dir():
    """A fresh work folder for one Claude call: the only place that call can write."""
    d = os.path.realpath(tempfile.mkdtemp(prefix="bps-"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def read_output(path):
    """Text of the one file a call was asked to write, or None."""
    if os.path.islink(path) or not os.path.isfile(path) or os.path.getsize(path) > MAX_BYTES:
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def read_json(path):
    t = read_output(path)
    if t is None:
        raise OSError("no output")
    return json.loads(t)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def docx_text(data):
    """Plain text of a .docx (italics as *x*, super/subscript as ^{x} _{x}): the model has no Python to open it."""
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z, z.open("word/document.xml") as f:
            xml = f.read(MAX_BYTES + 1)
        if len(xml) > MAX_BYTES:
            raise ValueError
        head = xml.decode("utf-8-sig")
        if "<!DOCTYPE" in head or "<!ENTITY" in head:
            raise ValueError
        root = ET.fromstring(xml)
    except (zipfile.BadZipFile, KeyError, ValueError, ET.ParseError, RuntimeError, NotImplementedError, OSError):
        raise ValueError("Could not read this Word file. Save it as PDF and try again.")
    lines = []
    for para in root.iter(W + "p"):
        bits = []  # [style, text]
        for run in (e for e in para.iter() if e.tag in (W + "r", M + "r")):
            text = "".join((e.text or "") if e.tag in (W + "t", M + "t") else
                           "\t" if e.tag == W + "tab" else "\n" if e.tag == W + "br" else "" for e in run)
            pr = run.find(W + "rPr")
            it = pr.find(W + "i") if pr is not None else None
            va = pr.find(W + "vertAlign") if pr is not None else None
            style = (it is not None and it.get(W + "val") not in ("0", "false", "off"),
                     {"superscript": "^", "subscript": "_"}.get(va.get(W + "val")) if va is not None else None)
            if bits and bits[-1][0] == style:
                bits[-1][1] += text
            elif text:
                bits.append([style, text])
        line = ""
        for (ital, va), text in bits:
            if va:
                text = va + "{" + text + "}"
            if ital and text.strip():
                text = text.replace(text.strip(), "*" + text.strip() + "*", 1)
            line += text
        if para.find(f"{W}pPr/{W}numPr") is not None:
            line = "#. " + line
        lines.append(line)
    if not any(x.strip() for x in lines):
        raise ValueError("No text found in this Word file. Save it as PDF and try again.")
    return ("(Text extracted from a Word file. *x* = italics. #. = a list item whose automatic number or letter is "
            "not shown, so do not report numbering for these. Pictures are missing.)\n\n" + "\n".join(lines))


def save_upload(data, name, prefix):
    """Save an uploaded file to the inbox; .docx is turned into text. Raises ValueError with a message for the user."""
    name = re.sub(r"[^\w.\-]", "_", os.path.basename(str(name)))[-80:]
    raw = base64.b64decode(str(data).split(",")[-1])
    if name.lower().endswith(".doc"):
        raise ValueError("Old .doc files cannot be read. Save it as .docx or PDF and try again.")
    if name.lower().endswith(".docx"):
        raw, name = docx_text(raw).encode("utf-8"), name + ".txt"
    os.makedirs(INBOX, exist_ok=True)
    path = os.path.join(INBOX, time.strftime(prefix + "%H%M%S-") + name)
    with open(path, "wb") as f:
        f.write(raw)
    return path


def run_claude(job, prompt, scratch, tag):
    """One Claude Code call: no shell, reads the skill and references, writes only inside `scratch`."""
    read = [SKILL, REFS]
    if tag.startswith(LEARN_TAGS):
        prompt += teacher_notes()
        if os.path.isdir(MY_STYLE) and MY_STYLE in prompt:
            read.append(MY_STYLE)
    env = clean_env()
    if os.environ.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [CLAUDE, "-p", "--model", MODEL, "--output-format", "stream-json", "--verbose",
           "--restricted", "--strict-mcp-config", "--tools", "Read,Write,Edit,Glob,Grep", "--permission-mode", "dontAsk",
           "--allowedTools", "Edit(./**)", "--no-session-persistence", "--disable-slash-commands",
           "--add-dir", *dict.fromkeys(os.path.realpath(r) for r in read)]  # takes several values: keep it last
    result = ""
    try:
        p = subprocess.Popen(cmd, cwd=scratch, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        p.stdin.write(prompt)
        p.stdin.close()
    except OSError as e:
        return 1, f"Could not start Claude Code: {e}"
    for raw in p.stdout:
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    inp = c.get("input", {})
                    what = inp.get("file_path") or inp.get("command") or ""
                    job["log"].append(f"[{tag}] {c['name']} {os.path.basename(str(what))[:70]}")
        elif ev.get("type") == "result":
            result = ev.get("result", "")
    p.wait()
    return p.returncode, result


def load_part(path, p):
    try:
        qs = read_json(path)["questions"]
        return [q for q in qs if isinstance(q, dict) and q.get("q")]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def outputs(base, fmt, student):
    names = []
    if fmt in ("pdf", "both"):
        names.append(base + ".pdf")
    if fmt in ("tex", "both"):
        names.append(base + ".tex")
    if student:
        names.append(base + "-student.pdf")
    return [os.path.basename(n) for n in names if os.path.exists(n)]


def generate(jid, d):
    job = JOBS[jid]
    parts = plan(d)
    job["parts"] = [{"label": p["label"], "status": "waiting"} for p in parts]

    def write(i):
        p, js = parts[i], job["parts"][i]
        for attempt in range(2):
            js["status"] = "writing" if attempt == 0 else "retrying"
            with scratch_dir() as s:
                dd = dict(d)
                if d.get("source"):
                    dd["source"] = shutil.copy(d["source"], s)
                path = os.path.join(s, f"part{p['id']}.json")
                run_claude(job, writer_prompt(dd, p, path), s, f"part {p['id']}")
                qs = load_part(path, p)
            if len(qs) >= p["n"]:
                js["status"] = "done"
                return qs[:p["n"]]
        js["status"] = "short" if qs else "failed"
        return qs

    job["stage"] = f"Writing {len(parts)} parts in parallel"
    with ThreadPoolExecutor(MAXW) as ex:
        results = list(ex.map(write, range(len(parts))))

    sections, short = {}, []
    for p, qs in zip(parts, results):
        for q in qs:
            q.update(type=p["type"], marks=p["marks"])
        sections.setdefault(p["section"], []).extend(qs)
        if len(qs) < p["n"]:
            short.append(f"{p['n'] - len(qs)} {p['type']} ({p['marks']} marks) in {p['section']} on {', '.join(p['chapters'][:4])}")
    if not any(sections.values()):
        job.update(status="error", stage="Failed", result="No writer finished. Check that Claude Code is signed in: "
                   "open Terminal, run `claude`, sign in, then try again.")
        return

    ex_ = EXAMS[d["exam"]]
    topic = "Full Syllabus" if not d["chapters"] else ", ".join(d["chapters"][:3]) + (" and more" if len(d["chapters"]) > 3 else "")
    paper = {"title": f"{d['exam']} {ex_['subject_label']} {'Mock Test' if d['type'] == 'Mock' else 'DPP'}: {topic}",
             "exam": d["exam"], "type": d["type"], "level": d["level"],
             "time": ex_["time"] if d["type"] == "Mock" and d["count"] == sum(g[3] for g in ex_["layout"])
             else f"{max(10, round(d['count'] * ex_.get('minutes_per_question', 1.1)))} min",
             "marking": ex_["marking"],
             "instructions": ["All questions are compulsory.", "Read each question carefully before answering."],
             "sections": [{"name": k, "questions": v} for k, v in sections.items()]}
    name = f"{slug(d['exam'])}-{d['type'].lower()}-{slug(topic)}-{time.strftime('%Y-%m-%d')}"
    path, n = os.path.join(OUT, name + ".json"), 2
    while os.path.exists(path):
        path, n = os.path.join(OUT, f"{name}-{n}.json"), n + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(paper, f, ensure_ascii=False, indent=1)

    import importlib.util
    spec = importlib.util.spec_from_file_location("render", RENDER)
    render = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(render)
    warns = render.check(paper)

    job["stage"] = "Solving the paper blind (without the key)"
    job["parts"].append({"label": "Blind solver", "status": "writing"})
    keys, blind = {}, json.loads(json.dumps(paper))
    n = 0
    for sec in blind["sections"]:
        for q in sec["questions"]:
            n += 1
            keys[str(n)] = q.pop("answer", "")
            q.pop("solution", None)
    with scratch_dir() as s:
        bpath, bans = os.path.join(s, "blind.json"), os.path.join(s, "blind-answers.json")
        write_json(bpath, blind)
        rc, _ = run_claude(job, blind_prompt(f"The paper is {bpath} (questions are numbered in order from 1).", bans),
                           s, "blind")
        job["parts"][-1]["status"] = "done" if rc == 0 else "failed"
        try:
            for qn, k, m in compare(keys, read_json(bans)):
                warns.append(f"Q{qn}: blind solver answered {m} but the key says {k}. Re-solve it: fix the key, "
                             "or rewrite the question so only one answer is right")
        except (OSError, ValueError, AttributeError):
            warns.append("blind solve did not finish: check every key yourself")

    job["stage"] = "Checking every question and making the files"
    job["parts"].append({"label": "Reviewer", "status": "writing"})
    with scratch_dir() as s:
        copy = shutil.copy(path, s)
        dd = dict(d)
        if d.get("source"):
            dd["source"] = shutil.copy(d["source"], s)
        rc, res = run_claude(job, reviewer_prompt(dd, copy, warns, short, d["format"], d["student"]), s, "review")
        job["parts"][-1]["status"] = "done" if rc == 0 else "failed"
        try:  # keep the app's own paper unless the edited questions are complete and renderable
            fixed = dict(paper, sections=read_json(copy)["sections"])
            if sum(len(x["questions"]) for x in fixed["sections"]) < sum(len(x["questions"]) for x in paper["sections"]):
                raise ValueError("questions missing")
            render.check(fixed)
            render.build(fixed)
            write_json(path, fixed)
        except Exception as err:  # any malformed model JSON
            job["log"].append(f"[review] edited paper rejected ({type(err).__name__}); kept the unreviewed one")
            res = (res or "") + "\n\nThe reviewer's file was not usable, so this paper is unreviewed: check it yourself."
    base = os.path.splitext(path)[0]
    for extra in ([f"--format={d['format']}"], ["--no-key"] if d["student"] else None):
        if extra:
            r = subprocess.run([PY, RENDER, path] + extra, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            left = [ln[5:] for ln in r.stdout.splitlines() if ln.startswith("WARN ")]
            if left and extra[0] != "--no-key":
                res = (res or "") + "\n\nStill flagged by the checker: " + "; ".join(left[:8])
    files = outputs(base, d["format"], d["student"])
    job.update(files=files, result=res, status="done" if files else "error",
               stage="Done" if files else "Could not make the files")


def load_render():
    import importlib.util
    spec = importlib.util.spec_from_file_location("render", RENDER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TYPE_RANK = {"key": 0, "fact": 1, "repeat": 2, "format": 3, "spelling": 4, "language": 5}


def extract_prompt(src, out):
    return (f"Follow the rules in {SKILL_MD}. Do not ask questions. {src}\n\n"
            "Copy her paper into JSON exactly as written: same wording, same spelling mistakes, same numbering, "
            "same options and keyed answers. Do NOT correct, improve or reorder anything; the copy must keep every "
            "error so it can be found. Mark italics with *...*. Use the section 4 JSON format, and give every question "
            '"no" (her question number as a string). Put her answer key into "answer" (leave "" if missing) and her '
            'solution into "solution" if she gave one. For figures, put a short description into "q". '
            f"Save only the JSON to {out}. Reply with one line: number of questions found.")


def chunk_prompt(src, cpath, out, allq):
    return (f"Follow the rules in {SKILL_MD}, section 6 'Proofread mode'. Do not ask questions.\n\n"
            f"{cpath} holds some questions copied from her paper (field \"no\" is her question number). The original "
            f"is: {src[:300]}. Check ONLY these questions, against NCERT 2026-27 and references/ (read the matching "
            "NCERT chapter text before judging a fact). For each question: solve it yourself first, then compare with "
            "her key; check every option for a second correct answer; check facts, numbers, scientific names and "
            "italics, units, wording (missing bold NOT/INCORRECT, double negatives, giveaways) and format. "
            "If a spelling or italics problem might be a copying slip, confirm it in the original before reporting.\n"
            f"The other questions in the paper (to catch repeats): {allq[:6000]}\n\n"
            f'Save only a JSON list to {out}: [{{"q": "12", "type": "key|fact|spelling|language|format|repeat", '
            '"problem": "...", "fix": "...", "source": "NCERT XI Ch 8", "right": "C", "sure": true}]. '
            '"right" only for key problems (the correct answer). "sure": false when you are not certain. '
            "Leave out questions with no problem. Save [] if all are fine. Reply with one line.")


def paper_source(path, text, scratch):
    if path:
        return f"Her paper is the file {shutil.copy(path, scratch)}."
    return "Her paper is pasted below.\n\n" + text


def proofread(jid, d):
    job = JOBS[jid]
    path = d.get("path")
    text = "" if path else d["text"][:60000]
    report = os.path.join(OUT, f"proofread-{time.strftime('%Y-%m-%d-%H%M%S')}.md")

    # 1. exact copy of her paper as JSON
    job["stage"] = "Reading her paper question by question"
    job["parts"] = [{"label": "Reader", "status": "writing"}]
    with scratch_dir() as s:
        xpath = os.path.join(s, "paper.json")
        run_claude(job, extract_prompt(paper_source(path, text, s), xpath), s, "read")
        try:
            paper = read_json(xpath)
            qs = [q for s_ in paper["sections"] for q in s_["questions"]]
            assert qs
        except (OSError, ValueError, KeyError, TypeError, AssertionError):
            qs = None
    if not qs:
        job["parts"][0]["status"] = "failed"
        return proofread_single(job, path, text, report)
    job["parts"][0]["status"] = "done"
    for i, q in enumerate(qs, 1):
        q["no"] = str(q.get("no") or i)
    nos = [q["no"] for q in qs]

    # 2. automatic checks (format, exact repeats, balance) + near-repeat scan
    auto = []
    for w in load_render().check(paper):
        if "difficulty" in w or "no solution" in w:
            continue
        auto.append(re.sub(r"^Q(\d+)", lambda m: "Q" + nos[int(m.group(1)) - 1] if int(m.group(1)) <= len(nos) else m.group(0), w))
    import difflib
    texts = [" ".join(str(q.get("q", "")).lower().split()) for q in qs]
    for b in range(len(qs)):
        for a in range(b):
            if len(texts[b]) > 40 and texts[a] != texts[b] and difflib.SequenceMatcher(None, texts[a], texts[b]).ratio() > 0.9:
                auto.append(f"Q{nos[b]}: nearly the same question as Q{nos[a]}")
                break

    # 3. parallel chunk proofreaders + blind solver
    size = max(8, -(-len(qs) // 6))
    chunks = [qs[i:i + size] for i in range(0, len(qs), size)]
    allq = " | ".join(f"Q{q['no']}: {str(q.get('q', ''))[:80]}" for q in qs)
    job["stage"] = f"Proofreading {len(qs)} questions in {len(chunks)} parts, and solving the paper blind"
    job["parts"] += [{"label": f"Proofreader Q{c[0]['no']}-Q{c[-1]['no']}", "status": "writing"} for c in chunks]
    job["parts"].append({"label": "Blind solver", "status": "writing"})
    keys, blind = {}, json.loads(json.dumps(paper))
    for s_ in blind["sections"]:
        for q in s_["questions"]:
            keys[str(q.get("no"))] = q.pop("answer", "")
            q.pop("solution", None)
    keys = {k: v for k, v in keys.items() if str(v).strip()}
    found = {}  # output name -> parsed JSON, kept after each scratch folder is gone

    def keep(name, out):
        try:
            found[name] = read_json(out)
        except (OSError, ValueError):
            pass

    def chunk(i, c):
        with scratch_dir() as s:
            cpath, out = os.path.join(s, f"chunk{i}.json"), os.path.join(s, f"rows{i}.json")
            write_json(cpath, c)
            r, _ = run_claude(job, chunk_prompt(paper_source(path, text, s), cpath, out, allq), s, f"proof{i + 1}")
            keep(i, out)
        job["parts"][i + 1]["status"] = "done" if r == 0 and i in found else "failed"

    def solve():
        with scratch_dir() as s:
            bpath, bans = os.path.join(s, "blind.json"), os.path.join(s, "blind-answers.json")
            write_json(bpath, blind)
            r, _ = run_claude(job, blind_prompt(f'The paper is {bpath}; use each question\'s "no" as its number.', bans),
                              s, "blind")
            keep("blind", bans)
        job["parts"][-1]["status"] = "done" if r == 0 and "blind" in found else "failed"
    ts = [threading.Thread(target=chunk, args=(i, c)) for i, c in enumerate(chunks)] + [threading.Thread(target=solve)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    # 4. merge and cross-check
    rows, missing = [], []
    for i, c in enumerate(chunks):
        if isinstance(found.get(i), list):
            rows += [r for r in found[i] if isinstance(r, dict)]
        else:
            missing.append(f"Q{c[0]['no']}-Q{c[-1]['no']}")
    mine = {str(k): v for k, v in found["blind"].items()} if isinstance(found.get("blind"), dict) else None
    keyrows = {}
    for r in rows:
        r["q"] = str(r.get("q", "")).lstrip("Qq ")
        r["status"] = "Error" if r.get("sure", True) else "Check"
        if r.get("type") == "key" and mine is not None and r["q"] in mine:
            b = norm_ans(mine[r["q"]])
            if r.get("right") and b == norm_ans(r["right"]):
                r["status"], r["note"] = "Confirmed", "blind solve agrees"
            elif b == norm_ans(keys.get(r["q"], "")):
                r["status"], r["note"] = "Check", "blind solve agrees with her key"
        if r.get("type") == "key":
            keyrows[r["q"]] = r
    if mine is not None:
        for qn, k, m in compare(keys, mine):
            if qn not in keyrows:
                rows.append({"q": qn, "type": "key", "status": "Check", "problem": f"Her key is {k}; an independent solve got {m}",
                             "fix": "Re-solve this one by hand", "source": "", "note": "blind solve only"})
    order = {n: i for i, n in enumerate(nos)}
    rows.sort(key=lambda r: ({"Confirmed": 0, "Error": 1, "Check": 2}.get(r["status"], 3),
                             TYPE_RANK.get(r.get("type"), 9), order.get(r["q"], 999)))
    cell = lambda x: str(x or "").replace("|", "/").replace("\n", " ")
    md = [f"# Proofread report: {os.path.basename(path) if path else 'pasted paper'}", "",
          f"{len(qs)} questions read. Each was checked by a proofreader, and every key was also solved blind by a "
          "second Claude. **Confirmed** = both agree it is wrong. **Check** = not certain, look yourself.", "",
          "| Q no. | Status | Type | Problem | Suggested fix | Source |", "|---|---|---|---|---|---|"]
    md += [f"| {cell(r['q'])} | {r['status']}{' (' + r['note'] + ')' if r.get('note') else ''} | {cell(r.get('type'))} | "
           f"{cell(r.get('problem'))} | {cell(r.get('fix'))}{' Right answer: ' + cell(r['right']) if r.get('right') else ''} | "
           f"{cell(r.get('source'))} |" for r in rows]
    if auto:
        md += ["", "**Automatic checks:**", ""] + [f"- {w}" for w in auto]
    cnt = {}
    for r in rows:
        cnt[r.get("type", "other")] = cnt.get(r.get("type", "other"), 0) + 1
    md += ["", "**Count:** " + (", ".join(f"{v} {k}" for k, v in sorted(cnt.items(), key=lambda kv: TYPE_RANK.get(kv[0], 9)))
                                 or "no problems found") + f"; {len(auto)} automatic."]
    if missing:
        md.append(f"\n**Not checked (a part failed):** {', '.join(missing)}. Run the proofread again for these.")
    if mine is None:
        md.append("\n**Blind solve did not finish**, so keys were checked only once.")
    res = "\n".join(md)
    with open(report, "w", encoding="utf-8") as f:
        f.write(res)
    ok = not missing and mine is not None
    job.update(result=res, files=[os.path.basename(report)], status="done",
               stage="Done" if ok else "Done, but some parts failed (see report)")


def proofread_single(job, path, text, report):
    """Fallback when her paper could not be copied into JSON: one full pass."""
    job["stage"] = "Proofreading (single pass)"
    job["parts"].append({"label": "Proofreader", "status": "writing"})
    with scratch_dir() as s:
        out = os.path.join(s, "report.md")
        prompt = (f"Follow the rules in {SKILL_MD}, section 'Proofread mode'. Do not ask questions. {paper_source(path, text, s)}\n\n"
                  "Solve every question yourself before comparing with her key, and check every option for a second correct answer. "
                  f"Reply only with the proofread table and the count line, in Markdown, and save the same report to {out}.")
        rc, res = run_claude(job, prompt, s, "proofread")
        md = read_output(out)
    if md:
        with open(report, "w", encoding="utf-8") as f:
            f.write(md)
    job["parts"][-1]["status"] = "done" if rc == 0 else "failed"
    job.update(result=res or "Claude Code stopped with an error. Run `claude` once in a terminal (Windows: PowerShell) and sign in.",
               files=[os.path.basename(report)] if os.path.exists(report) else [],
               status="done" if rc == 0 else "error", stage="Done" if rc == 0 else "Failed")


def list_papers():
    items = {}
    for f in os.listdir(OUT):
        b, ext = os.path.splitext(f)
        if ext in (".pdf", ".tex", ".md", ".zip") and not f.startswith("."):
            key = b.removesuffix("-student")
            it = items.setdefault(key, {"name": key, "files": [], "t": 0})
            it["files"].append(f)
            it["t"] = max(it["t"], os.path.getmtime(os.path.join(OUT, f)))
    return sorted(items.values(), key=lambda x: -x["t"])[:40]


def safe(job):
    return {k: v for k, v in job.items() if k != "thread"}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authed(self):
        return f"bps={TOKEN}" in [c.strip() for c in self.headers.get("Cookie", "").split(";")]

    def do_GET(self):
        path = unquote(self.path.split("?")[0])
        if path == "/":
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self.send(200, f.read(), "text/html; charset=utf-8")
        if path == "/api/exams":  # pattern data only, nothing private
            return self.send(200, [{"name": k, "n": sum(g[3] for g in e["layout"]), "summary": e.get("summary", ""),
                                    "subject": e["subject_label"], "default": bool(e.get("default")),
                                    "groups": chapter_groups(e)} for k, e in EXAMS.items()])
        if path == "/api/auth":
            note = os.path.join(os.path.dirname(PINF), "note.txt")  # private dedication, never in the repo
            msg = open(note, encoding="utf-8-sig").read()[:300] if os.path.isfile(note) else ""
            return self.send(200, {"set": os.path.isfile(PINF), "ok": self.authed(), "note": msg})
        if not self.authed():
            return self.send(401, {"error": "locked"})
        if path == "/api/papers":
            return self.send(200, list_papers())
        if path.startswith("/api/job/"):
            job = JOBS.get(path[9:])
            return self.send(200, safe(job)) if job else self.send(404, {"error": "no job"})
        if path.startswith("/files/"):
            full = os.path.join(OUT, os.path.basename(path[7:]))
            if not os.path.isfile(full):
                return self.send(404, "not found", "text/plain")
            ctype = {".pdf": "application/pdf", ".tex": "text/plain; charset=utf-8",
                     ".md": "text/plain; charset=utf-8", ".zip": "application/zip"}.get(os.path.splitext(full)[1], "application/octet-stream")
            with open(full, "rb") as f:
                return self.send(200, f.read(), ctype)
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self.send(403, {"error": "forbidden"})
        try:
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        except ValueError:
            return self.send(400, {"error": "bad json"})
        if self.path == "/api/login":
            pin = str(d.get("pin", ""))
            if not os.path.isfile(PINF):
                if not re.fullmatch(r"\d{4,8}", pin):
                    return self.send(400, {"error": "PIN must be 4 to 8 digits"})
                pin_set(pin)
            elif not pin_ok(pin):
                time.sleep(1.5)
                return self.send(403, {"error": "wrong PIN"})
            self.send_response(200)
            self.send_header("Set-Cookie", f"bps={TOKEN}; HttpOnly; SameSite=Strict; Path=/")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "11")
            self.end_headers()
            return self.wfile.write(b'{"ok":true}')
        if self.path == "/api/feedback" and self.authed():
            text = " ".join(str(d.get("text", "")).split())[:1000]
            if not text:
                return self.send(400, {"error": "Write what should change first"})
            os.makedirs(os.path.dirname(PREFS), exist_ok=True)
            with open(PREFS, "a", encoding="utf-8") as f:
                f.write(f"- {time.strftime('%Y-%m-%d')}: {text}\n")
            return self.send(200, {"ok": True})
        if not self.authed():
            return self.send(401, {"error": "locked"})
        if self.path == "/api/generate":
            if d.get("exam") not in EXAMS or d.get("type") not in TYPES or d.get("level") not in LEVELS \
                    or d.get("format", "pdf") not in FORMATS:
                return self.send(400, {"error": "bad choice"})
            try:
                d["count"] = int(d.get("count", 0))
                if not 1 <= d["count"] <= 200:
                    raise ValueError
            except ValueError:
                return self.send(400, {"error": "questions must be 1 to 200"})
            src = None
            if d.get("sourcedata"):
                try:
                    src = save_upload(d["sourcedata"], d.get("sourcename", "chapter"), "src-")
                except ValueError as e:
                    return self.send(400, {"error": str(e)})
            raw_src = src
            d = {"exam": d["exam"], "type": d["type"], "level": d["level"], "count": d["count"],
                 "chapters": [clean(c, 80) for c in d.get("chapters", [])][:20], "format": d.get("format", "pdf"),
                 "student": bool(d.get("student")), "notes": clean(d.get("notes", ""), 600), "source": raw_src}
            if d["type"] == "DPP" and not d["chapters"] and d["source"]:
                d["chapters"] = ["the chapter in the teacher's file"]
            if d["type"] == "DPP" and not d["chapters"]:
                return self.send(400, {"error": "pick at least one chapter for a DPP"})
            target = generate
        elif self.path == "/api/proofread":
            if not d.get("filedata") and not d.get("text", "").strip():
                return self.send(400, {"error": "add a file or paste the paper"})
            if d.get("filedata"):
                try:
                    d["path"] = save_upload(d["filedata"], d.get("filename", "paper"), "")
                except ValueError as e:
                    return self.send(400, {"error": str(e)})
            else:
                d.pop("path", None)  # never take a file path from the request
            target = proofread
        else:
            return self.send(404, {"error": "unknown"})
        if not has_restricted():
            return self.send(400, {"error": UPDATE_MSG})
        if not signed_in():
            return self.send(400, {"error": "Claude Code is not signed in on this computer. Open Terminal (Mac) or "
                                            "PowerShell (Windows), type  claude  and sign in, then try again."})
        jid = uuid.uuid4().hex[:10]
        JOBS[jid] = {"id": jid, "kind": self.path[5:], "status": "running", "stage": "Starting", "log": [],
                     "parts": [], "result": "", "files": [], "start": time.time()}
        threading.Thread(target=target, args=(jid, d), daemon=True).start()
        self.send(200, {"id": jid})


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(MY_STYLE, exist_ok=True)
    os.chmod(OUT, 0o700)
    url = f"http://127.0.0.1:{PORT}"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:  # already running: just open it
        webbrowser.open(url)
        sys.exit(0)
    print("Bio Paper Studio running at", url, "(close this window to stop)")
    if os.environ.get("NO_BROWSER") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    srv.serve_forever()
