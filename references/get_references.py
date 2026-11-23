"""Download NCERT Biology chapters and past exam papers from their official websites,
onto your own computer, for your own study use. Nothing copyrighted is stored in this repo.

    python get_references.py            # into ~/.claude/skills/paper-studio/references
    python get_references.py <folder>   # somewhere else

Each source in sources.json is saved as .pdf; if `pypdf` is installed, the text is also saved as .md
(the app reads either). Files you already have are skipped, so you can re-run it any time.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), ".claude", "skills", "bio-paper", "references")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

try:
    from pypdf import PdfReader
except ImportError:  # optional: lets text PDFs become .md text
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--quiet", "pypdf"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import site, importlib
        sys.path.append(site.getusersitepackages()); importlib.invalidate_caches()
        from pypdf import PdfReader
    except Exception:  # noqa: BLE001
        PdfReader = None


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": url.rsplit("/", 1)[0] + "/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise ValueError("the site did not send a PDF")
    with open(path, "wb") as f:
        f.write(data)


def to_text(pdf, md, url):
    if not PdfReader:
        return False
    try:
        text = "\n\n".join((p.extract_text() or "") for p in PdfReader(pdf).pages)
    except Exception:  # noqa: BLE001 - a broken PDF just stays a PDF
        return False
    if len(text.strip()) < 500:  # scanned paper: keep the PDF, Claude reads it directly
        return False
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"Source: {url}\n\n{text}")
    return True


def main():
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as f:
        sources = json.load(f)
    ok, failed = 0, []
    for rel, url in sorted(sources.items()):
        md = os.path.join(DEST, rel)
        pdf = md[:-3] + ".pdf"
        os.makedirs(os.path.dirname(md), exist_ok=True)
        if os.path.exists(md) or os.path.exists(pdf):
            ok += 1
            continue
        for attempt in range(3):
            try:
                fetch(url, pdf)
                to_text(pdf, md, url)
                ok += 1
                print("ok  ", rel)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    failed.append((rel, url, str(e)[:80]))
                    print("FAIL", rel, "-", str(e)[:80])
                time.sleep(2)
    print(f"\n{ok} of {len(sources)} references ready in {DEST}")
    if failed:
        print("Could not download these (the site may be down or have moved the file). Download them in a browser "
              "and save each as the .pdf name shown, or drop the chapter into the app's 'Your NCERT chapter' box:")
        for rel, url, _ in failed:
            print(f"  {rel[:-3]}.pdf  <-  {url}")


if __name__ == "__main__":
    main()
