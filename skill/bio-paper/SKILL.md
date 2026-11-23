---
name: paper-studio
description: Make mock test papers and DPPs (daily practice problems) for any exam with a profile in references/exams/ (today IAT, NEST, IIT JAM, NEET biology and NEET chemistry), with answer key and solutions, as a print-ready PDF. Use when asked for a bio mock test, test paper, DPP, practice sheet or question paper for these exams.
---

# Bio Paper: mock tests and DPPs

Makes a biology paper for one of four exams. Output: a PDF (and HTML) with the paper, then the answer key, then solutions.

## 1. Show the picker first (always, before writing anything)

Call AskUserQuestion once with these four questions, so the user picks by clicking. Skip only a question the user already answered in their message. If the request comes from Bio Paper Studio (all choices given), skip the picker entirely and never ask questions.

1. header "Exam", question "Which exam is this paper for?": options IAT, NEST, IIT JAM, NEET (any other exam with a file in `references/exams/`, such as NEET Chemistry, can be typed)
2. header "Type", question "Mock test or DPP?": options "Mock" (full exam pattern), "DPP" (chapter practice)
3. header "Level", question "What difficulty level?": options Easy, Medium, Hard, Mixed (Mixed = 30% easy, 50% medium, 20% hard)
4. header "Questions", question "How many questions?": options "Exam count (Recommended)" (IAT 15, NEST 20, IIT JAM 50, NEET 90; for a DPP, 15), "10", "30", "50". The user can type any other number with "Other".

Then ask a second AskUserQuestion:
- header "Format", question "Which file do you want?": options "PDF (Recommended)", "LaTeX (.tex)" (to edit in Overleaf), "Both", "Student copy" (PDF without answers; also makes the teacher copy). Pass it to render.py as `--format=pdf`, `--format=tex`, `--format=both`, or a second run with `--no-key`.
- Only if DPP: header "Chapters", question "Which chapter(s)?", offering 3–4 likely chapters for that exam and letting them type others. For a Mock, cover the whole syllabus, weighted the way the real exam is.

## 2. Exam patterns (biology part only)

These are defaults. If the user gives a different count or marking, use theirs.

| Exam | Mock Qs | Question types | Marking | Time |
|---|---|---|---|---|
| IAT (IISER) | 15 | Single-correct MCQ, 4 options | +4 / −1 | 45 min |
| NEST | 20 | Mostly single-correct MCQ, a few multiple-correct | Single +3 / −1; multiple +4, no negative | 50 min |
| IIT JAM (Biotech) | 50 | Sec A MCQ 25 (8 × 1 mark, 17 × 2 marks); Sec B MSQ 8 (2 marks); Sec C NAT 17 (8 × 1, 9 × 2) | MCQ −1/3 for 1-mark, −2/3 for 2-mark; MSQ and NAT no negative, no partial marks | 150 min |
| NEET | 90 | Single-correct MCQ, 4 options. Botany 45 + Zoology 45 | +4 / −1 | 90 min |

Syllabus and style:
- **NEET**: NCERT Class 11 and 12 biology, word for word NCERT facts. Include assertion-reason, statement I/II, match-the-column and "how many of the following are correct" items, as recent NEET papers do.
- **IAT**: NCERT 11–12 level, but conceptual and application-based, with some data and experiment questions.
- **NEST**: NCERT 11–12 plus reasoning. Passage- or experiment-based questions, some graph reading.
- **IIT JAM Biotech**: biology at Class 12 and BSc level: cell and molecular biology, biochemistry, genetics, microbiology, immunology and basic biotechnology. NAT questions need a numeric answer (for example genetics ratios, enzyme kinetics or dilution).

Other exams: each `references/exams/<exam>.json` holds that exam's sections, question types, counts, marking, time, style, weightage, difficulty and sources, and lists its subjects; each `references/subjects/<subject>/subject.json` lists the chapters and where the textbook text is. For an exam not in the table above, use its profile file the same way.

For a DPP, use the chosen exam's question types and marking, but only the chosen chapters.

## 2b. References (use them)

`references/ncert/` holds NCERT Biology 2026-27 chapters and `references/papers/` past papers (IIT JAM BT 2012-2026, NEST 2017-2026, IAT 2025-2026), downloaded from the official sites by `references/get_references.py`. Each is a `.md` text file, or a `.pdf` of the same name when the text could not be extracted (read the PDF then). `references/sources.json` lists every file and its official URL. Before writing, read the NCERT chapter text and skim 1-2 past papers of that exam for style. Never copy a past question word for word. IAT and NEST keys say option (a)/A for every question: that is the official convention (options were shuffled in the real exam).

Exam profiles in `references/profiles/` (iat, nest, jam; neet when present) give each exam's topic weightage, styles, traps and a 1-5 difficulty rubric, backtested on the 2026 papers. Read the profile before writing and tag each question `"difficulty": 1-5`. If the teacher gives her own NCERT chapter file, it is the source of truth: follow it over every other reference.

## 3. Writing rules

- Every question must have exactly one correct key (MSQ: one or more), checked against NCERT or a standard text. Never invent facts. If unsure, drop the question and write a different one.
- No repeated questions or near-duplicates inside one paper. Spread questions across subtopics.
- Wrong options must be plausible (common student mistakes), never silly.
- The correct option's position must be spread evenly over A, B, C and D.
- Each solution is 1–3 lines: why the right answer is right, and the key fact. For NEET, add the NCERT class and chapter.
- Figures: never draw or describe pictures freehand. When a question needs one (pedigree, enzyme or growth graph, bar data, plasmid map, data table), add `"figure"` with data only, and `render.py` draws it the same way in the PDF and the LaTeX (TikZ). Kinds and fields are listed at the top of `figures.py`:
  - `{"kind": "pedigree", "members": [{"id": "I-1", "sex": "M", "affected": false, "carrier": true, "spouse": "I-2"}, {"id": "II-1", "sex": "F", "affected": true, "parents": ["I-1", "I-2"]}]}`. List spouses next to each other.
  - `{"kind": "graph", "x": "[S] (mM)", "y": "v", "series": [{"name": "no inhibitor", "points": [[0, 0], [2, 5]]}]}`, `{"kind": "bar", "labels": [...], "values": [...]}`
  - `{"kind": "plasmid", "name": "pBR322", "size": 4361, "features": [{"name": "ampR", "start": 3293, "end": 4153}], "sites": [{"name": "PstI", "pos": 3609}]}`
  - `{"kind": "table", "head": [...], "rows": [[...]]}`
  Work out the answer from the same numbers you put in the figure, so figure and key agree. Use real map positions for named plasmids. For anything else (cell parts, organs), describe it in words.

## 4. Build the file

Write the questions as JSON at `~/BioPapers/<exam>-<mock|dpp>-<topic>-<YYYY-MM-DD>.json`:

```json
{
  "title": "NEET Biology DPP: Cell Cycle",
  "exam": "NEET", "type": "DPP", "level": "Mixed",
  "time": "20 min",
  "marking": "+4 for correct, −1 for wrong, 0 for unattempted",
  "instructions": ["All questions are compulsory.", "Choose one correct option."],
  "sections": [
    {
      "name": "Section A",
      "questions": [
        {"type": "MCQ", "marks": 4, "q": "Question text", "options": ["a", "b", "c", "d"], "answer": "B", "solution": "Why B."},
        {"type": "MSQ", "marks": 2, "q": "...", "options": ["a", "b", "c", "d"], "answer": "A, C", "solution": "..."},
        {"type": "NAT", "marks": 1, "q": "...", "answer": "0.25", "solution": "..."}
      ]
    }
  ]
}
```

A `q` may contain line breaks (`\n`) for statements or match-the-column lists. Then run:

```bash
python3 ~/.claude/skills/paper-studio/render.py ~/BioPapers/<file>.json
```

It writes the `.html` and `.pdf` next to the JSON. In claude.ai (no `~`, no Chrome): write the JSON in the working folder, run `render.py` from this skill's folder, and if it says WeasyPrint is missing run `pip install weasyprint` first; if that fails, make the PDF with the pdf skill (reportlab). Always offer the `.tex` too. Add `--no-key` for a student copy without the answer key and solutions.

Before rendering, proofread your own paper with the checklist in section 6. `render.py` also runs automatic checks and prints `WARN` lines: fix every warning and run it again before replying.

## 6. Proofread mode (her own papers)

Use this when she gives a paper she made (PDF, Word, image or pasted text) and asks to proofread, check or verify it. Do not rewrite her paper. Report problems only.

Work in this order, so nothing is missed:
1. Copy her paper question by question exactly as written (keep her mistakes).
2. Solve every question yourself without looking at her key, then compare. A key is wrong only if your solve and a re-check against NCERT both disagree with it; otherwise mark it "Check".
3. Go through the checklist below for each question, then for the whole paper (repeats, numbering, balance).
Bio Paper Studio does this with several proofreaders in parallel plus a separate blind solver, and marks key errors "Confirmed" when both agree.

Check every question for:
1. **Wrong answer key**: the keyed option is not correct, or a different option is also correct (two correct), or none is correct. Check against NCERT 2026-27 and the files in `references/`.
2. **Wrong facts** in the question or options (names, numbers, examples, terms).
3. **Spelling and scientific names**: genus capital, species small, italics where needed (for example *Homo sapiens*), units, symbols, superscripts and subscripts.
4. **Language**: unclear wording, double negatives, a question that gives away its own answer, a missing "NOT" or "INCORRECT" in bold.
5. **Format**: question numbering skips or repeats, an option missing or labelled twice, an answer key that doesn't line up with the question count, wrong marks total, section counts that don't match the exam pattern.
6. **Repeats**: the same or nearly the same question twice.
7. **Balance**: too many answers on one letter, or one chapter taking too much of the paper.

Reply with a table: Q no. | Problem | Type (key / fact / spelling / format / repeat) | Suggested fix | Source (NCERT class and chapter). Put key and fact errors first, because those are the costly ones. End with a count, for example "3 key errors, 2 fact errors, 5 spelling". If nothing is wrong in a question, don't list it. If you are not sure something is an error, mark it "Check" instead of calling it wrong.

## 7. Reply

Give the PDF path and a one-line summary (exam, type, level, number of questions, chapters, total marks). Send the PDF with SendUserFile if available.

## 8. Bio Paper Studio (the app)

A clickable interface: double-click `Bio Paper Studio.command` on the Desktop, or run `python3 ~/.claude/skills/paper-studio/app/server.py`. It opens http://127.0.0.1:8765 where she picks exam, type, difficulty, number of questions, chapters and file type, or uploads a paper to proofread. It runs Claude Code headless (`claude -p`, Sonnet) with this skill and lists finished papers from `~/BioPapers`.
It is locked with a PIN set on first open (stored hashed in `~/.config/bio-paper/pin`); it listens only on 127.0.0.1, so no other device can reach it, and `~/BioPapers` is readable only by her macOS user. Forgot PIN: delete that file and set a new one.
