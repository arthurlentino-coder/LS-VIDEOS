#!/usr/bin/env python3
"""dress_item.py — passo de ÁUDIO PADRÃO do build: veste os 4 formatos de um item.

Para um item (base = <outbase>.mp4 + _split/_hybrid/_faceless):
  - gera UM sfx.json dirigido pela copy (sfx_from_cues) a partir das cues do faceless;
  - escolhe o mood automático pela copy (trilha.pick_mood);
  - aplica bed (mood) + SFX (copy) + loudnorm -14 em cada formato (vídeo é COPIADO, só o áudio muda).

Regra do SPLIT: o finish_split já assa SFX event-synced no _split, então aqui o split
leva BED-ONLY (não duplica efeito). Normal/Hybrid/Faceless levam bed + SFX por copy.

Uso:
  python dress_item.py --edit projects/CFP_7/edit --outbase output/CFP/CFP_7
  python dress_item.py --edit ... --outbase ... --mood energico   # força mood
  python dress_item.py --edit ... --outbase ... --only faceless    # só um formato
"""
import argparse, shutil, sys
from pathlib import Path

HF = Path(__file__).resolve().parent     # audio/ (tem trilha.py e sfx_from_cues.py)
sys.path.insert(0, str(HF))
import trilha
import sfx_from_cues

SUFFIX = {"normal": "", "split": "_split", "hybrid": "_hybrid", "faceless": "_faceless"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--outbase", required=True, help="prefixo (ex. output/CFP/CFP_7)")
    ap.add_argument("--mood", default="auto")
    ap.add_argument("--only", default=None, choices=list(SUFFIX.keys()))
    ap.add_argument("--bed-vol", type=float, default=None)
    a = ap.parse_args()

    edit = Path(a.edit)
    cues = edit / "hf" / "faceless" / "assets" / "cues.js"
    if not cues.exists():
        raise SystemExit(f"sem cues: {cues}")

    # 1) sfx.json por copy (uma vez)
    sfx_json = edit / "hf" / "sfx_copy.json"
    sys.argv = ["sfx_from_cues", "--cues", str(cues), "--edl", str(edit/"edl.json"), "--out", str(sfx_json)]
    sfx_from_cues.main()

    # 2) mood automático
    mood = a.mood
    if mood == "auto":
        mood = trilha.pick_mood(trilha._load_cues_text(cues)); print(f"[mood auto] -> {mood}")
    if a.bed_vol is not None:
        _orig = trilha.apply
        def _apply(v, b, o, ev, bed_vol=a.bed_vol, cta_at=None): return _orig(v, b, o, ev, bed_vol=a.bed_vol, cta_at=cta_at)
        trilha.apply = _apply

    # 3) vestir cada formato
    fmts = [a.only] if a.only else ["normal", "split", "hybrid", "faceless"]
    for fmt in fmts:
        out = Path(a.outbase + SUFFIX[fmt] + ".mp4")
        if not out.exists():
            print(f"  [skip] {out.name} nao existe"); continue
        tmp = out.with_suffix(".dress.mp4")
        bed_only = (fmt == "split")   # split ja tem SFX event-synced do finish
        trilha.dress(out, tmp, mood, None if bed_only else sfx_json, cues)
        shutil.move(str(tmp), str(out))
        print(f"  [{fmt}] vestido ({'bed-only' if bed_only else 'bed+sfx'}) -> {out.name}")
    print(f"dress_item OK: {a.outbase} (mood={mood})")

if __name__ == "__main__":
    main()
