"""compose_hfsubs.py — compoe o overlay de legenda animada (HyperFrames, webm alpha)
sobre o base.mp4 (sem legenda) e finaliza igual ao processo padrao:
  overlay -> encode CRF 20 yuv420p 30fps -> loudnorm two-pass (-14 LUFS).

Espelha o caminho final do round_subs.py, trocando as PNGs por um unico webm animado.
Saida: VIDEOS/output/IMG_5055_hfsubs.mp4 (versao de comparacao A/B).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os
from pathlib import Path

HF = Path(__file__).resolve().parent          # projects/IMG_5055/edit/hf
EDIT = HF.parent                              # projects/IMG_5055/edit
VIDEOS = EDIT.parents[2]                      # VIDEOS/
# helpers do video-use: env VIDEO_USE_HELPERS, senao <pai de VIDEOS>/claude/video use/helpers
_here = Path(__file__).resolve()
_videos = next((p for p in _here.parents if (p / "input").is_dir()), _here.parents[3])
HELPERS = Path(os.environ.get("VIDEO_USE_HELPERS") or _videos.parent / "claude" / "video use" / "helpers")

ap = argparse.ArgumentParser()
ap.add_argument("--base", default=str(EDIT / "base.mp4"))
ap.add_argument("--overlay", action="append", default=None,
                help="webm alpha p/ compor (pode repetir; empilha na ordem)")
ap.add_argument("--out", default=str(VIDEOS / "output" / "IMG_5055_hfsubs.mp4"))
args = ap.parse_args()

base = Path(args.base)
overlays = [Path(o) for o in (args.overlay or [str(HF / "subs-animated.webm")])]
out = Path(args.out)
prenorm = HF / "_prenorm.mp4"

for o in overlays:
    if not o.exists():
        sys.exit(f"overlay nao encontrado: {o}")

# 1) empilha os webm alpha sobre o base + encode final (mesmos params do round_subs).
# IMPORTANTE: forcar o decoder libvpx-vp9 em CADA overlay — o decoder VP9 nativo do
# ffmpeg DESCARTA o plano alpha (entrega preto nas areas transparentes, cobrindo o video).
inputs = ["-i", str(base)]
for o in overlays:
    inputs += ["-c:v", "libvpx-vp9", "-i", str(o)]
# duracao da BASE — overlays fixos podem ser mais longos (reuso em combos curtos);
# sem isto o overlay segue o input mais longo e congela a cauda (gotcha README §9).
_bd = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=nk=1:nw=1", str(base)],
                     capture_output=True, text=True).stdout.strip()
base_dur = float(_bd)
chain, prev = [], "[0:v]"
for i in range(1, len(overlays) + 1):
    nxt = f"[v{i}]"
    chain.append(f"{prev}[{i}:v]overlay=0:0:format=auto{nxt}")
    prev = nxt
cmd = [
    "ffmpeg", "-y", "-hide_banner", "-nostats", *inputs,
    "-filter_complex", ";".join(chain),
    "-map", prev, "-map", "0:a",
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-pix_fmt", "yuv420p", "-r", "30",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-t", f"{base_dur:.3f}",
    "-movflags", "+faststart", str(prenorm),
]
print(f"compondo {len(overlays)} overlay(s) sobre {base.name} -> {prenorm.name}")
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

# 2) loudnorm two-pass (reaproveita o helper padrao -> paridade total)
sys.path.insert(0, str(HELPERS))
import render  # noqa: E402
print("loudnorm two-pass -> -14 LUFS")
render.apply_loudnorm_two_pass(prenorm, out, preview=False)
prenorm.unlink(missing_ok=True)
print(f"done: {out}")
