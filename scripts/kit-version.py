#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,sys
from pathlib import Path
SEMVER=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$')
def parse(v):
    m=SEMVER.fullmatch(v.strip())
    if not m: raise ValueError(f'not SemVer: {v!r}')
    core=tuple(map(int,m.group(1,2,3))); pre=m.group(4)
    return core,pre
def compare(a,b):
    ac,ap=parse(a); bc,bp=parse(b)
    if ac!=bc:return -1 if ac<bc else 1
    if ap==bp:return 0
    if ap is None:return 1
    if bp is None:return -1
    aa=ap.split('.'); bb=bp.split('.')
    for x,y in zip(aa,bb):
        if x==y:continue
        xn,yn=x.isdigit(),y.isdigit()
        if xn and yn:return -1 if int(x)<int(y) else 1
        if xn!=yn:return -1 if xn else 1
        return -1 if x<y else 1
    return -1 if len(aa)<len(bb) else 1
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('current'); q.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    q=s.add_parser('compare'); q.add_argument('left');q.add_argument('right')
    q=s.add_parser('verify'); q.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    a=p.parse_args()
    try:
        if a.cmd=='compare': print(compare(a.left,a.right)); return 0
        root=a.root.resolve(); v=(root/'VERSION').read_text().strip(); parse(v)
        if a.cmd=='current': print(v); return 0
        ch=(root/'CHANGELOG.md').read_text()
        if not re.search(rf'^## \[{re.escape(v)}\]',ch,re.M): raise ValueError(f'CHANGELOG missing {v}')
        print(v); return 0
    except Exception as e: print(f'version error: {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
