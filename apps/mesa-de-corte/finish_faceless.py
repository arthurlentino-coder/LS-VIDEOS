#!/usr/bin/env python3
"""finish_faceless.py — fecho do FACELESS: GATE de certificacao + loudnorm.

  GATE check_cert (faceless/compositions/frames/*.html) -> aborta se cert divergir
  faceless_prenorm.mp4 (render HyperFrames, ja com audio) -> loudnorm two-pass -> <out>

Uso:
  py finish_faceless.py --edit projects/CPROI_6/edit --out "output/C-PRO I/C-PRO I 6_faceless.mp4"
Bypass do gate: SKIP_CERT=1
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# helpers do video-use: env VIDEO_USE_HELPERS, senao <pai de VIDEOS>/claude/video use/helpers
_here = Path(__file__).resolve()
_videos = next((p for p in _here.parents if (p / "input").is_dir()), _here.parents[3])
HELPERS = Path(os.environ.get("VIDEO_USE_HELPERS") or _videos.parent / "claude" / "video use" / "helpers")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prenorm", default=None)
    a = ap.parse_args()
    edit = Path(a.edit).resolve()

    # GATE — checa todos os frames autorais do faceless
    # GATE de certificacao, fail-closed: qualquer falha do gate aborta a finalizacao.
    # Bypass consciente: SKIP_CERT=1.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import check_cert
        fl = ["hf/faceless/index.html"] + [str(p.relative_to(edit)) for p in sorted((edit / "hf" / "faceless" / "compositions" / "frames").glob("*.html"))]
        check_cert.gate(edit, files=fl, label="faceless")
    except SystemExit:
        raise
    except Exception as e:
        if os.environ.get("SKIP_CERT") == "1":
            print(f"[check_cert] gate falhou ({e}) — ignorado por SKIP_CERT=1")
        else:
            sys.exit(f"[check_cert] gate falhou ({e}) — finalizacao abortada (SKIP_CERT=1 p/ forcar)")

    prenorm = Path(a.prenorm) if a.prenorm else edit / "hf" / "faceless_prenorm.mp4"
    if not prenorm.exists():
        sys.exit(f"faltando: faceless_prenorm.mp4 ({prenorm})")
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)

    print("loudnorm two-pass -> saida")
    sys.path.insert(0, str(HELPERS))
    import render  # noqa
    render.apply_loudnorm_two_pass(prenorm, out, preview=False)
    print(f"OK -> {out}")

if __name__ == "__main__":
    main()
