#!/usr/bin/env python3
"""reconcile_durations.py — alinha a duração de TODAS as composições à base real.

Depois do base_zoom.mp4 pronto, mede a duração real e ajusta `data-duration` (e a
chamada *Kit.build({duration})`) de cada comp pra bater com a base. Substitui o
`sed -i "s/<dur_scaffold>/<dur_base>/g"` que eu fazia na mão (e errava).

Só mexe em DURAÇÃO (atributos de duração + build duration). NÃO toca tempos de cena.
Para "esticar o CTA" use a flag --cta-extend (apenas reporta o alvo; a extensão de
cena continua manual por ser específica de cada comp).

Comps cobertas (se existirem):
  hf/subs-animated/index.html, hf/subs-divider/index.html,
  hf/split/public/index.html, hf/hybrid/public/index.html, hf/faceless/index.html

Uso:
  python reconcile_durations.py --edit projects/CFP_7/edit
  python reconcile_durations.py --edit projects/CFP_7/edit --dur 18.0   # força alvo
"""
import argparse, re, subprocess
from pathlib import Path

COMPS = [
    "hf/subs-animated/index.html",
    "hf/subs-divider/index.html",
    "hf/split/public/index.html",
    "hf/hybrid/public/index.html",
    "hf/faceless/index.html",
]

def probe(mp4: Path) -> float:
    return float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(mp4)]
    ).decode().strip())

def fmt(x: float) -> str:
    # 3 casas, sem zeros à toa, mas sempre >=1 decimal (18.0->"18.0"; 18.75->"18.75"; 20.333333->"20.333")
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    if "." not in s: s += ".0"
    return s

def patch(path: Path, dur: str) -> int:
    html = path.read_text(encoding="utf-8")
    n = 0
    # data-duration="..."
    html, c = re.subn(r'(data-duration=")[0-9.]+(")', rf'\g<1>{dur}\g<2>', html); n += c
    # *Kit.build({ ... duration: N ... })  e  build({duration:N,...})
    html, c = re.subn(r'(\bduration:\s*)[0-9.]+', rf'\g<1>{dur}', html); n += c
    path.write_text(html, encoding="utf-8")
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--dur", type=float, default=None, help="alvo (default = base_zoom real)")
    ap.add_argument("--cta-extend", type=float, default=None, help="só reporta alvo+T (extensão de cena é manual)")
    a = ap.parse_args()
    edit = Path(a.edit)
    base = edit / "base_zoom.mp4"
    dur = a.dur if a.dur is not None else probe(base)
    ds = fmt(dur)
    print(f"alvo de duração: {ds}s" + (f"  (base {base.name})" if a.dur is None else "  (forçado)"))
    for rel in COMPS:
        p = edit / rel
        if p.exists():
            n = patch(p, ds)
            print(f"  {rel}: {n} campo(s)")
    if a.cta_extend:
        print(f"[cta-extend] alvo com cauda = {fmt(dur + a.cta_extend)}s — estenda a última cena/card manualmente até lá.")

if __name__ == "__main__":
    main()
