#!/usr/bin/env python3
"""Inject an automatically discovered open handoff into a new Codex session."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess, sys

def resolve(cwd: Path) -> dict | None:
    try:
        root = subprocess.check_output(["git","rev-parse","--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL, timeout=2).strip()
    except Exception:
        return None
    script=Path(root)/".codex"/"scripts"/"resolve-handoff.py"
    if not script.is_file(): return None
    try:
        p=subprocess.run([sys.executable,str(script),"--cwd",root,"--json"],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=5,check=False)
        return json.loads(p.stdout) if p.stdout.strip() else None
    except Exception: return None

def main()->int:
    try: payload=json.load(sys.stdin)
    except Exception: return 0
    if payload.get("agent_id"): return 0
    result=resolve(Path(str(payload.get("cwd") or ".")).expanduser())
    if not result or not result.get("selected"): return 0
    path=result["selected"]
    context=(f"Workflow handoff auto-discovery: an OPEN handoff matches this worktree: {path} ({result.get('confidence','')}: {result.get('reason','')}). If the user's objective is implementation, fixing, addressing review feedback, or continuing the deferred investigation, read this handoff before broad exploration and do not redo the broad review. Re-verify findings against current HEAD. If the objective is unrelated, ignore the handoff. When all actionable items are completed or obsolete, mark it consumed with: python3 .codex/scripts/handoff-status.py consume {path}")
    print(json.dumps({"suppressOutput":True,"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":context}})); return 0
if __name__=="__main__": raise SystemExit(main())
