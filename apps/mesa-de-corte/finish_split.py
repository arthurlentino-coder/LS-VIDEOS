#!/usr/bin/env python3
"""finish_split.py — fecho do SPLIT em 1 comando.

Corrente: split_motion.mp4 (render da composição, SEM áudio)
  -> mux com o áudio de voz da base_zoom_seam.mp4         (split_av.mp4)
  -> overlay da legenda karaokê na divisória subs-divider.webm (split_capt.mp4)
  -> sfx_mix.py (mistura SFX de sfx.json + loudnorm two-pass -14 LUFS)
  -> <out>.mp4

Uso:
  py finish_split.py --edit projects/CPROR_5/edit --out "output/CPRO R/CPROR_5_split.mp4"
Opcionais: --divider (default hf/subs-divider.webm) --sfx (default hf/split/sfx.json)
           --sem-legenda  (pula o overlay da divisória)
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

# UTF-8 robusto (loudnorm imprime "→"; console cp1252 quebraria). Vale p/ este
# processo E p/ os filhos (py sfx_mix.py herda PYTHONIOENCODING).
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True, help="pasta edit do projeto (ex.: projects/CPROR_5/edit)")
    ap.add_argument("--out", required=True, help="mp4 de saída (ex.: output/CPRO R/CPROR_5_split.mp4)")
    ap.add_argument("--motion", default=None, help="override do split_motion.mp4")
    ap.add_argument("--base", default=None, help="override da base_zoom_seam.mp4")
    ap.add_argument("--divider", default=None, help="override do subs-divider.webm")
    ap.add_argument("--sfx", default=None, help="override do sfx.json")
    ap.add_argument("--sem-legenda", action="store_true", help="não sobrepor a legenda da divisória")
    a = ap.parse_args()

    edit = Path(a.edit).resolve()

    # GATE de certificacao: barra 'CPA' num video CPRO-I etc. (bypass: SKIP_CERT=1)
    # GATE de certificacao, fail-closed: qualquer falha do gate aborta a finalizacao.
    # Bypass consciente: SKIP_CERT=1.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import check_cert
        check_cert.gate(edit, files=["hf/split/public/index.html"], label="split")
    except SystemExit:
        raise
    except Exception as e:
        if os.environ.get("SKIP_CERT") == "1":
            print(f"[check_cert] gate falhou ({e}) — ignorado por SKIP_CERT=1")
        else:
            sys.exit(f"[check_cert] gate falhou ({e}) — finalizacao abortada (SKIP_CERT=1 p/ forcar)")

    motion = Path(a.motion) if a.motion else edit / "hf" / "split_motion.mp4"
    base = Path(a.base) if a.base else edit / "base_zoom_seam.mp4"
    divider = Path(a.divider) if a.divider else edit / "hf" / "subs-divider.webm"
    sfx = Path(a.sfx) if a.sfx else edit / "hf" / "split" / "sfx.json"
    sfxmix = edit / "hf" / "sfx_mix.py"
    av = edit / "hf" / "split_av.mp4"
    capt = edit / "hf" / "split_capt.mp4"
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    for p, nome in [(motion, "split_motion.mp4"), (base, "base_zoom_seam.mp4")]:
        if not p.exists():
            sys.exit(f"faltando: {nome} ({p})")

    # 1) mux vídeo do split + áudio de voz da base
    print("[1/3] mux split_motion + áudio da base -> split_av.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", motion, "-i", base,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-shortest", av])

    # 2) overlay legenda karaokê na divisória (opcional)
    src = av
    if not a.sem_legenda and divider.exists():
        print("[2/3] overlay legenda divisória (subs-divider.webm) -> split_capt.mp4")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", av,
             "-c:v", "libvpx-vp9", "-i", divider,
             "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
             "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "copy", capt])
        src = capt
    else:
        print("[2/3] sem legenda de divisória (pulei o overlay)")

    # 3) SFX + loudnorm via o sfx_mix.py do projeto
    if sfx.exists() and sfxmix.exists():
        print("[3/3] sfx_mix (SFX + loudnorm -14) -> saída")
        run(["py", sfxmix, "--video", src, "--cues", sfx, "--out", out])
    else:
        # fallback: só loudnorm two-pass (sem SFX)
        print("[3/3] sem sfx.json/sfx_mix — só loudnorm")
        from finish_hybrid import HELPERS  # mesma resolucao portavel
        HELPERS = str(HELPERS)
        sys.path.insert(0, HELPERS)
        import render  # noqa
        render.apply_loudnorm_two_pass(src, out, preview=False)

    print(f"OK -> {out}")


if __name__ == "__main__":
    main()
