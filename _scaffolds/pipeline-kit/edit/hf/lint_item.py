#!/usr/bin/env python3
"""lint_item.py — checagem pré-render de 1 item (pega as ciladas recorrentes).

Verifica, sem renderizar nada:
  [comps]     as composições dos 4 formatos existem (+ subs-animated/subs-divider)
  [divider]   subs-divider existe (senão o build com set -e morre / split sai sem divisória)
  [duração]   data-duration das comps batem entre si (±0.2) e ~ base_zoom (±0.4, se houver)
  [cert]      edl.json note_orientacao cita o token de certificação (gate do finish infere dele)
  [cues]      faceless/assets/cues.js é UTF-8 limpo (sem mojibake U+FFFD)
  [ordem]     faceless carrega illos-kit.js ANTES de kit.js

Saída: relatório OK/WARN/FAIL. Exit code != 0 se houver FAIL.
Uso:  python lint_item.py --edit projects/CFP_7/edit [--cert CFP] [--cta-extended]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

def dur_of(html: Path):
    m = re.search(r'data-duration="([0-9.]+)"', html.read_text(encoding="utf-8", errors="replace"))
    return float(m.group(1)) if m else None

def probe(mp4: Path):
    try:
        return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=nw=1:nk=1",str(mp4)]).decode().strip())
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--cert", default=None, help="token de cert esperado (default: inferido do nome do projeto)")
    ap.add_argument("--cta-extended", action="store_true", help="item com CTA esticado (duração > base é OK)")
    a = ap.parse_args()
    edit = Path(a.edit); hf = edit / "hf"
    fails = []; warns = []; oks = []
    def ok(m): oks.append(m)
    def warn(m): warns.append(m)
    def fail(m): fails.append(m)

    comps = {
        "subs-animated": hf/"subs-animated/index.html",
        "subs-divider":  hf/"subs-divider/index.html",
        "split":         hf/"split/public/index.html",
        "hybrid":        hf/"hybrid/public/index.html",
        "faceless":      hf/"faceless/index.html",
    }
    # [comps] + [divider]
    for name, p in comps.items():
        if p.exists(): ok(f"[comps] {name}")
        elif name == "subs-divider": fail(f"[divider] FALTA subs-divider — rode make_divider.py (build com set -e morre)")
        else: fail(f"[comps] FALTA {name}: {p}")

    # [duração]
    durs = {n: dur_of(p) for n, p in comps.items() if p.exists() and dur_of(p) is not None}
    if durs:
        lo, hi = min(durs.values()), max(durs.values())
        if hi - lo <= 0.2: ok(f"[duração] comps alinhadas (~{hi:.2f}s)")
        else: fail(f"[duração] divergem {lo:.2f}..{hi:.2f}s: " + ", ".join(f"{n}={d}" for n,d in durs.items()))
        base = edit/"base_zoom.mp4"; bd = probe(base) if base.exists() else None
        if bd:
            diff = hi - bd
            if a.cta_extended:
                ok(f"[duração] base {bd:.2f}s (CTA esticado p/ {hi:.2f}s, +{diff:.2f})")
            elif abs(diff) <= 0.4: ok(f"[duração] bate com base ({bd:.2f}s)")
            else: warn(f"[duração] comps {hi:.2f}s vs base {bd:.2f}s (Δ{diff:+.2f}) — rode reconcile_durations.py (ou --cta-extended)")
    # [cert]
    edl = edit/"edl.json"
    cert = a.cert or re.sub(r"[_\-0-9].*$", "", edit.parent.name) or edit.parent.name
    if edl.exists():
        note = (json.loads(edl.read_text(encoding="utf-8")).get("note_orientacao") or "")
        if cert and re.search(re.escape(cert), note, re.I): ok(f"[cert] note cita '{cert}'")
        else: fail(f"[cert] note_orientacao NÃO cita '{cert}' → gate do finish não infere a cert. Adicione ao note.")
    else:
        warn("[cert] sem edl.json")
    # [cues]
    cues = hf/"faceless/assets/cues.js"
    if cues.exists():
        raw = cues.read_bytes()
        try:
            txt = raw.decode("utf-8")
            if "�" in txt: fail("[cues] cues.js tem U+FFFD (mojibake) — regrave em UTF-8")
            else: ok("[cues] cues.js UTF-8 limpo")
        except UnicodeDecodeError:
            fail("[cues] cues.js NÃO é UTF-8 válido")
    else:
        warn("[cues] sem faceless/assets/cues.js")
    # [ordem] faceless scripts
    fp = comps["faceless"]
    if fp.exists():
        h = fp.read_text(encoding="utf-8", errors="replace")
        i_illos, i_kit = h.find("illos-kit.js"), h.find("kit.js")
        if i_illos != -1 and i_kit != -1 and i_illos < i_kit: ok("[ordem] illos-kit.js antes de kit.js")
        elif i_illos == -1: warn("[ordem] faceless sem illos-kit.js (ok se não usa ILLOS)")
        else: fail("[ordem] illos-kit.js DEPOIS de kit.js → ILLOS indefinidas")

    print(f"=== lint {edit} (cert={cert}) ===")
    for m in oks:  print("  ✓", m)
    for m in warns: print("  ⚠", m)
    for m in fails: print("  ✗", m)
    print(f"--- {len(oks)} ok · {len(warns)} aviso · {len(fails)} falha ---")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
