# Bio Paper Studio

**Free AI mock test and DPP generator for NEET, IIT JAM, IAT and NEST Biology**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)](#windows-10--11)
[![macOS](https://img.shields.io/badge/macOS-supported-000000?logo=apple)](#mac)
[![Built on Claude Code](https://img.shields.io/badge/Built%20on-Claude%20Code-D97757)](https://claude.com/claude-code)
[![Stars](https://img.shields.io/github/stars/rishavm713-create/bio-paper-studio?style=social)](https://github.com/rishavm713-create/bio-paper-studio/stargazers)

For biology teachers, coaching institutes and students: NEET mock tests, IIT JAM Biotechnology papers, IISER IAT and NISER NEST practice, chapter-wise DPPs from NCERT, with answer keys, solutions and diagrams, plus an AI proofreader for your own question papers.

> If this saves you time, please give it a ⭐. It helps other teachers find it.

**Make biology mock tests and DPPs for IAT, NEST, IIT JAM and NEET in minutes, and proofread your own papers for wrong answer keys, wrong facts and typos.**

You click what you want (exam, mock or DPP, difficulty, number of questions, chapters). A few minutes later you get a print-ready PDF: the paper, then the answer key, then a short solution for every question. You also get a LaTeX file for Overleaf if you want one.

It runs on your own computer and uses [Claude Code](https://claude.com/claude-code), so you need a Claude account (Pro or Max plan).


## How much of the work is automated

| Task | Before (by hand) | With Bio Paper Studio | You still do |
|---|---|---|---|
| Full mock test with key and solutions | 1-2 days | ~10-20 minutes | A 15-minute read-through |
| Chapter DPP (20-30 questions) | 2-4 hours | ~5 minutes | Quick check |
| Proofreading a paper | 1-2 hours | ~3 minutes | Decide on items marked **Check** |
| LaTeX / Overleaf typing | 1-3 hours | Automatic | Nothing |
| Diagrams (pedigrees, graphs, plasmid maps) | 30-60 minutes each | Automatic | Nothing |

Roughly **80-90% of the routine work** of a biology content writer is done for you. The final call on every paper stays with the teacher: read it once before it goes to students.

---

## Install (one step)

### Windows 10 / 11

1. Press **Start**, type **PowerShell** and open it.
2. Paste this line and press **Enter**:

```powershell
irm https://raw.githubusercontent.com/rishavm713-create/bio-paper-studio/main/install.ps1 | iex
```

### Mac

1. Press **Cmd + Space**, type **Terminal** and open it.
2. Paste this line and press **Enter**:

```bash
curl -fsSL https://raw.githubusercontent.com/rishavm713-create/bio-paper-studio/main/install.sh | bash
```

The installer takes about a minute. It:

- installs Python and Claude Code if you don't have them,
- installs the app, with NCERT Biology and past papers already included,
- puts a **Bio Paper Studio** icon on your Desktop.

**First time only:** type `claude` in the same window and sign in with your Claude account. Then double-click **Bio Paper Studio** on the Desktop. (Mac, first time: right-click the icon, then **Open**, then **Open**.)

### Prefer a download?

| What | Link |
|---|---|
| App (Windows + Mac, ~2 MB) | **[Download BioPaperStudio.zip](https://github.com/rishavm713-create/bio-paper-studio/releases/latest/download/BioPaperStudio.zip)** |
| Original PDFs of the references (optional, ~270 MB) | [references-pdfs.zip](https://github.com/rishavm713-create/bio-paper-studio/releases/latest/download/references-pdfs.zip) |

Unzip it, then double-click **Install Bio Paper Studio (Windows).bat** on Windows, or **Install Bio Paper Studio.command** on Mac. If you put `references-pdfs.zip` in the same folder first, the Mac installer adds the PDFs too. You don't need the PDFs: the text versions are already in the app.

---

## Using it

The app opens in your browser at `http://127.0.0.1:8765`. That address works only on your own computer. The first time, choose a PIN; after that, the app asks for it each time.

**Make a paper**

1. Pick the **exam**: IAT, NEST, IIT JAM or NEET.
2. Pick **Mock** (full exam pattern) or **DPP** (practice on chosen chapters).
3. Pick the **difficulty** (Easy, Medium, Hard or Mixed) and the **number of questions**.
4. For a DPP, tick the **chapters**. You can also upload your own NCERT chapter, and it will then be followed exactly.
5. Pick the **output**: PDF, LaTeX, both, or a **student copy** (no answers; the teacher copy with answers is made too).
6. Press **Make paper**. Finished papers appear in the list and are saved in the `BioPapers` folder in your home folder.

**Proofread your own paper**

Upload your paper (PDF, Word, image or pasted text) and press **Proofread**. You get a table of problems, with the costly ones first:

- **Answer-key errors.** A key is marked **Confirmed** only when two separate checks agree. If only one check finds it, it is marked **Check** for you to look at.
- **Wrong facts.** Checked against NCERT 2026-27.
- **Spelling and scientific names.** For example, *Homo sapiens*, units and symbols.
- **Formatting.** Numbering, missing options, and marks totals.
- **Repeats.** Repeated or near-repeated questions.
- **Balance.** Answer letters that are not spread out.

Your paper is never rewritten; you only get a report.

You can also ask Claude Code directly, for example: *"make a NEET DPP on Cell Cycle, 20 questions, hard"*.

---

## What's inside

| Exam | Mock pattern (biology) | Marking |
|---|---|---|
| NEET | 90 MCQ (Botany 45 + Zoology 45) | +4 / −1 |
| IAT (IISER) | 15 MCQ | +4 / −1 |
| NEST | 20 (MCQ + a few multiple-correct) | +3 / −1, MSQ +4 |
| IIT JAM Biotechnology | 50: MCQ 25, MSQ 8, NAT 17 | as per the JAM brochure |
| NEET Chemistry | 45 MCQ | +4 / −1 |

- **No wrong answers by design.**
  - Questions are written from NCERT and past papers.
  - A second, separate solver answers every question *without seeing the key*. Any disagreement is sent to a reviewer, who fixes it before the PDF is made.
  - Automatic checks catch missing keys, duplicate questions and options, bad numeric answers, and answer letters bunched on one option.
- **Real diagrams.** Pedigrees, graphs, bar charts, plasmid maps and data tables are drawn from data. So the picture and the answer always agree, in both the PDF and the LaTeX.
- **Fast.** Big papers are written by up to 6 writers in parallel.
- **References included** (in `references/`):
  - NCERT Biology Class 11 and 12 (2026-27).
  - Past papers: IIT JAM BT 2012-2026, NEST 2017-2026, IAT 2025-2026.
  - Exam profiles with topic weightage and difficulty.
  - One pattern file per exam in `references/exams/` and one chapter list per subject in `references/subjects/`.

  All of it comes from the official websites, listed with their links in [`references/sources.json`](references/sources.json). Any reference that is missing downloads in the background, so you can start your first paper straight away.

---

## Add an exam or subject

No code changes: the app builds its exam list, subjects and chapters from data files.

1. **New subject** (skip if it exists): make `references/subjects/<subject>/subject.json` with `name`, `book` (e.g. `NCERT`), `text_dir` (where the chapter text lives, relative to `references/`), `text_names`, and `chapters`: a list of `{"name", "group", "tags"}` (group is the heading in the app, e.g. `Class 11`; tags are optional, e.g. `organic`). Add each chapter's official PDF link to `references/sources.json` with the same path, and `get_references.py` downloads it.
2. **New exam**: copy `references/exams/neet-chemistry.json` to `references/exams/<exam>.json` and edit it:
   - `name`, `order` (position in the app), `subject_label`, `summary` (short marking text under the button)
   - `sections`: `{"name", "type": "MCQ"|"MSQ"|"NAT", "marks", "count"}`, optional `pool` to limit a section to some chapters
   - `time`, `marking`, `minutes_per_question` (for DPPs and short papers)
   - `subjects`, `chapter_groups` (which chapters the app shows), `pool` (default chapters for a full-syllabus mock), as `{"subject", "group"?, "tag"?}`
   - `style`, `weightage`, `difficulty` (text the writers follow), `papers_prefix` (past papers in `references/papers/` starting with it), optional `profile` (a longer Markdown profile), `sources` (official links only)
3. Restart the app. The new exam appears in step 1; the blind solver, reviewer, "Check" flags and your saved preferences apply to it as to every other exam.

---

## Privacy

- The app listens only on your own computer (`127.0.0.1`), never on the network.
- It is locked behind your PIN.
- Your papers stay in your `BioPapers` folder.
- Papers are generated through your own Claude account.

**Forgot your PIN?** Delete the file `.config/bio-paper/pin` in your home folder, open the app, and set a new one.

## Troubleshooting

| Problem | Fix |
|---|---|
| "claude is not recognized" | Close and reopen PowerShell or Terminal, then type `claude`. |
| No PDF, only an HTML file | Install Google Chrome, or open the HTML file and print it to PDF. Windows uses Edge automatically. |
| Mac says the app "can't be opened" | Right-click the icon, then **Open**, then **Open**. |
| Want a stronger model | Before starting the app, set `BIO_MODEL=opus` (it uses Sonnet by default). |
| Update to the latest version | Run the install line again. Your papers and PIN are kept. |

## Files

```
skill/bio-paper/      the app: SKILL.md (Claude's instructions), render.py (PDF/LaTeX), figures.py (diagrams), app/ (web app)
references/           NCERT and past-paper text, exam profiles, sources.json, get_references.py (re-downloads from official sites)
install.ps1 / .sh     one-step installers
```

## Keywords

NEET biology mock test generator, NEET DPP generator, IIT JAM Biotechnology mock test, IISER IAT biology practice, NISER NEST biology questions, NCERT biology MCQ generator, AI question paper generator, biology question paper proofreader, answer key checker, biology DPP PDF, LaTeX question paper, Overleaf biology paper, free test series maker for teachers, coaching institute content tool, Claude Code skill.

## Credits

Co-created by Rishav Mishra and Anuva.

---

## License

The code is under the MIT License (see [LICENSE](LICENSE)). The files in `references/` belong to their owners (NCERT, IITs, IISERs and NTA). They are included only for personal study and are not covered by the MIT License.

---

**Built with love.** Free and open source, for every biology teacher and student.
