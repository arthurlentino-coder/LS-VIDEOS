#!/usr/bin/env python3
"""Picker do pool de b-roll por tags.
  py pick_broll.py <tag> [tag...]        -> melhor clipe (caminho absoluto)
  py pick_broll.py --top N <tag> [...]   -> N melhores com score
  py pick_broll.py --list                -> lista tudo com tags
  py pick_broll.py --json <tag> [...]    -> {file, score, orient, desc} do melhor
Score = nº de tags casadas; empate -> mais curto (mais versátil).
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
POOL = json.loads((ROOT/"broll.json").read_text("utf-8"))["clips"]

def score(clip, qtags):
    ct = set(t.lower() for t in clip["tags"])
    return sum(1 for q in qtags if q.lower() in ct)

def ranked(qtags):
    scored = [(score(c, qtags), -c.get("dur", 99), c) for c in POOL]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(s, c) for s, negd, c in scored]

def apath(c): return str((ROOT/c["file"]).resolve())

def main():
    a = sys.argv[1:]
    if not a or a[0] == "--list":
        for c in POOL: print(f"{c['file']:28} [{c['orient']:9}] {', '.join(c['tags'])}")
        return
    if a[0] == "--top":
        n = int(a[1]); qtags = a[2:]
        for s, c in ranked(qtags)[:n]:
            if s: print(f"{s}  {apath(c)}  ({c['desc']})")
        return
    if a[0] == "--json":
        qtags = a[1:]; s, c = ranked(qtags)[0]
        print(json.dumps({"file": apath(c), "score": s, "orient": c["orient"],
                          "w": c["w"], "h": c["h"], "desc": c["desc"]}, ensure_ascii=False))
        return
    qtags = a
    s, c = ranked(qtags)[0]
    print(apath(c))

if __name__ == "__main__": main()
