#!/usr/bin/env python3
"""make_divider.py — gera subs-divider/ a partir de subs-animated/ (determinístico).

A divisória é a MESMA legenda karaokê da subs-animated, só que:
  - posicionada na emenda 50/50 do split  (.cue bottom: Npx -> 885px)
  - caixa branca SÓLIDA                     (.box background rgba(...,0.3) -> 1.0)
Copia a fonte (arial.ttf) junto. Idempotente (sobrescreve).

Sem isso, o build do split fica sem legenda na divisória (os aprovados têm) e,
pior, um build com `set -e` que tente renderizar `subs-divider` MORRE se a pasta
não existir. Rodar ANTES de montar o split.

Uso:
  python make_divider.py --edit projects/CFP_7/edit        # usa hf/subs-animated -> hf/subs-divider
  python make_divider.py --src <dir subs-animated> --dst <dir subs-divider>
"""
import argparse, re, shutil
from pathlib import Path

SEAM_BOTTOM = 885  # px — meio do frame 1920 (topo do split termina em 960)

def convert(src: Path, dst: Path):
    si = src / "index.html"
    if not si.exists():
        raise SystemExit(f"nao achei {si}")
    html = si.read_text(encoding="utf-8")
    # 1) .cue bottom: Npx -> 885px  (primeira regra .cue { ... bottom: Npx })
    html = re.sub(r"(\.cue\s*\{[^}]*?bottom:\s*)\d+px", rf"\g<1>{SEAM_BOTTOM}px", html, count=1, flags=re.S)
    # 2) caixa sólida: rgba(255,255,255,0.3) -> 1.0  (qualquer alpha < 1 no .box)
    html = re.sub(r"(background:\s*rgba\(255,255,255,)[0-9.]+\)", r"\g<1>1.0)", html)
    # 3) título (cosmético)
    html = html.replace("Legenda animada (overlay)", "Legenda na divisória (overlay)")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "index.html").write_text(html, encoding="utf-8")
    # 4) assets ao lado (fonte etc.)
    for f in src.iterdir():
        if f.is_file() and f.name != "index.html":
            shutil.copy2(f, dst / f.name)
    print(f"subs-divider -> {dst}  (bottom={SEAM_BOTTOM}px, box solida)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", default=None, help="dir do projeto (usa hf/subs-animated -> hf/subs-divider)")
    ap.add_argument("--src", default=None)
    ap.add_argument("--dst", default=None)
    a = ap.parse_args()
    if a.edit:
        hf = Path(a.edit) / "hf"
        convert(hf / "subs-animated", hf / "subs-divider")
    elif a.src and a.dst:
        convert(Path(a.src), Path(a.dst))
    else:
        ap.error("passe --edit, ou --src e --dst")

if __name__ == "__main__":
    main()
