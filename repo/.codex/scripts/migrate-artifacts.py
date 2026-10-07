#!/usr/bin/env python3
"""Migrate legacy .codex runtime artifacts into .codex-artifacts."""
from __future__ import annotations
import argparse,re,shutil
from pathlib import Path

def is_handoff_template(p:Path)->bool:
    return bool(re.match(r'^TEMPLATE(?:[-_.].*)?\.md$',p.name,re.I))

def copy(src:Path,dst:Path):
    if not src.is_dir(): return
    dst.mkdir(parents=True,exist_ok=True)
    for p in src.iterdir():
        if is_handoff_template(p): continue
        q=dst/p.name
        if q.exists(): continue
        shutil.copytree(p,q) if p.is_dir() else shutil.copy2(p,q)

def main():
    a=argparse.ArgumentParser(); a.add_argument('--root',type=Path,default=Path.cwd()); a.add_argument('--remove-legacy',action='store_true'); x=a.parse_args()
    root=x.root.resolve(); out=root/'.codex-artifacts'
    for name in ('handoffs','goals','logs'):
        copy(root/'.codex'/name,out/name)
        (out/name).mkdir(parents=True,exist_ok=True)
        if x.remove_legacy and (root/'.codex'/name).exists(): shutil.rmtree(root/'.codex'/name)
    print(out)
    return 0
if __name__=='__main__': raise SystemExit(main())
