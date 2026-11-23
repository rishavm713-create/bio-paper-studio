#!/bin/zsh
# Opens Bio Paper Studio in the browser. Close this window to stop it.
lsof -ti tcp:8765 >/dev/null && { open http://127.0.0.1:8765; exit 0; }
exec python3 ~/.claude/skills/paper-studio/app/server.py
