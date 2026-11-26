#!/bin/bash
# Bio Paper Studio - one-step installer for macOS (and Linux).
# Run in Terminal:  curl -fsSL https://raw.githubusercontent.com/rishavm713-create/bio-paper-studio/main/install.sh | bash
# Or double-click "Install Bio Paper Studio.command" in the downloaded folder.
set -e
REPO=rishavm713-create/bio-paper-studio
SKILL="$HOME/.claude/skills/paper-studio"
say() { printf '\n== %s\n' "$1"; }

say "1/5 Python"
if ! python3 -c 'import sys; assert sys.version_info >= (3, 8)' 2>/dev/null; then
  if command -v brew >/dev/null; then brew install python3
  else echo "Python 3 is missing. On a Mac run:  xcode-select --install  (or get it from https://www.python.org/downloads/), then run this again."; exit 1; fi
fi
echo "Python found: $(python3 --version)"

say "2/5 Claude Code"
export PATH="$HOME/.local/bin:$PATH"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
command -v claude >/dev/null && echo "Claude Code found." || echo "Claude Code did not install. Get it from https://claude.com/claude-code"

say "3/5 App files"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
if [ ! -f "$SRC/skill/bio-paper/render.py" ]; then
  TMP="$(mktemp -d)"
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP"
  SRC="$TMP/bio-paper-studio-main"
fi
mkdir -p "$SKILL" "$HOME/BioPapers"
cp -R "$SRC/skill/bio-paper/." "$SKILL/"       # keeps your own extra references
mkdir -p "$SKILL/references"
for f in "$SRC/references/"*; do               # NCERT and past papers come from the official sites (step 4)
  case "${f##*/}" in ncert|papers) ;; *) cp -R "$f" "$SKILL/references/" ;; esac
done
[ -f "$SRC/note.txt" ] && mkdir -p "$HOME/.config/bio-paper" && cp "$SRC/note.txt" "$HOME/.config/bio-paper/note.txt"

say "4/5 References (downloading from the official websites in the background)"
python3 "$SKILL/references/get_references.py" > "$SKILL/references/download-log.txt" 2>&1 &

say "5/5 Desktop shortcut"
if [ -d "$HOME/Desktop" ]; then
  cp "$SRC/Bio Paper Studio.command" "$HOME/Desktop/Paper Studio.command" && chmod +x "$HOME/Desktop/Paper Studio.command"
fi
[ "$(uname)" = Darwin ] && [ ! -d "/Applications/Google Chrome.app" ] && echo "Tip: install Google Chrome for PDFs (without it you get an HTML file to print)."

printf '\nDone.\nFirst time only: open Terminal, type  claude  and sign in with your Claude account.\n'
echo "Then double-click 'Paper Studio' on the Desktop (first time: right-click > Open > Open)."
