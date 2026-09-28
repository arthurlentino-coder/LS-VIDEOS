#!/usr/bin/env python3
"""finish_hybrid.py — fecho do HYBRID em 1 comando, com GATE de certificacao.

  GATE check_cert (hybrid/public/index.html)  -> aborta se 'CPA' num CPRO-I etc.
  hybrid_motion.mp4 (video+cards, SEM audio) + audio da base_zoom_seam  (hybrid_av)
  -> overlay karaoke subs-animated.webm  -> loudnorm two-pass -14 LUFS -> <out>

Uso:
  py finish_hybrid.py --edit projects/CPROI_6/edit --out "output/C-PRO I/C-PRO I 6_hybrid.mp4"
Bypass do gate: SKIP_CERT=1
"""
from __future__ import annotations
import argparse, os, subprocess, sys
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

def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--motion", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--overlay", default=None)
    ap.add_argument("--sem-legenda", action="store_true")
    a = ap.parse_args()
    edit = Path(a.edit).resolve()

    # GATE
    # GATE de certificacao, fail-closed: qualquer falha do gate aborta a finalizacao.
    # Bypass consciente: SKIP_CERT=1.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import check_cert
        check_cert.gate(edit, files=["hf/hybrid/public/index.html"], label="hybrid")
    except SystemExit:
        raise
    except Exception as e:
        if os.environ.get("SKIP_CERT") == "1":
            print(f"[check_cert] gate falhou ({e}) — ignorado por SKIP_CERT=1")
        else:
            sys.exit(f"[check_cert] gate falhou ({e}) — finalizacao abortada (SKIP_CERT=1 p/ forcar)")

    motion = Path(a.motion) if a.motion else edit / "hf" / "hybrid_motion.mp4"
    base = Path(a.base) if a.base else edit / "base_zoom_seam.mp4"
    overlay = Path(a.overlay) if a.overlay else edit / "hf" / "subs-animated.webm"
    av = edit / "hf" / "hybrid_av.mp4"
    prenorm = edit / "hf" / "_hybrid_prenorm.mp4"
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)

    for p, nome in [(motion, "hybrid_motion.mp4"), (base, "base_zoom_seam.mp4")]:
        if not p.exists():
            sys.exit(f"faltando: {nome} ({p})")

    print("[1/3] mux hybrid_motion + audio da base -> hybrid_av.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", motion, "-i", base,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-shortest", av])

    src = av
    if not a.sem_legenda and overlay.exists():
        print("[2/3] overlay karaoke (subs-animated.webm) -> prenorm")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", av,
             "-c:v", "libvpx-vp9", "-i", overlay,
             "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto[v]",
             "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast",
             "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", prenorm])
        src = prenorm
    else:
        print("[2/3] sem legenda karaoke (pulei o overlay)")

    print("[3/3] loudnorm two-pass -> saida")
    sys.path.insert(0, str(HELPERS))
    import render  # noqa
    render.apply_loudnorm_two_pass(src, out, preview=False)
    for tmp in (av, prenorm):
        try: tmp.unlink(missing_ok=True)
        except Exception: pass
    print(f"OK -> {out}")

if __name__ == "__main__":
    main()
