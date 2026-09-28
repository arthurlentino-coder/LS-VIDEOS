"""sfx_mix.py — mixa SFX (biblioteca local) sobre o audio de um video ja pronto,
posicionando cada efeito no tempo (adelay) e normalizando o resultado (loudnorm -14).

Reusavel por projeto. Le um mapa de cues JSON: [{"t": segundos, "file": "whoosh-short", "gain": 0.45}, ...].
Biblioteca padrao: hyperframes-media/assets/sfx/*.mp3.

Uso:
  python sfx_mix.py --video <final.mp4> --cues sfx.json --out <final_sfx.mp4>
"""
import argparse
import json
import subprocess
import sys
import os
from pathlib import Path

SFX_DIR = Path(os.environ.get("HF_SFX_DIR") or Path.home() / ".claude" / "skills" / "hyperframes-media" / "assets" / "sfx")
# helpers do video-use: env VIDEO_USE_HELPERS, senao <pai de VIDEOS>/claude/video use/helpers
_here = Path(__file__).resolve()
_videos = next((p for p in _here.parents if (p / "input").is_dir()), _here.parents[3])
HELPERS = Path(os.environ.get("VIDEO_USE_HELPERS") or _videos.parent / "claude" / "video use" / "helpers")

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--cues", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--sfx-dir", default=str(SFX_DIR))
args = ap.parse_args()

video = Path(args.video)
cues = json.loads(Path(args.cues).read_text(encoding="utf-8"))
sfx_dir = Path(args.sfx_dir)
out = Path(args.out)
prenorm = out.parent / (out.stem + "_prenorm.mp4")

inputs = ["-i", str(video)]
for c in cues:
    p = sfx_dir / (c["file"] + ".mp3")
    if not p.exists():
        sys.exit(f"SFX nao encontrado: {p}")
    inputs += ["-i", str(p)]

parts = []
labels = []
for i, c in enumerate(cues, start=1):
    d = int(round(float(c["t"]) * 1000))
    g = float(c.get("gain", 0.5))
    # estereo, atrasado pro tempo do cue, com ganho
    parts.append(f"[{i}:a]aformat=channel_layouts=stereo,adelay={d}|{d},volume={g}[s{i}]")
    labels.append(f"[s{i}]")
n = len(cues)
# mixa a voz original [0:a] com todos os SFX (sem re-normalizar; loudnorm depois cuida)
mix_in = "[0:a]" + "".join(labels)
parts.append(f"{mix_in}amix=inputs={n+1}:duration=first:normalize=0:dropout_transition=0[mix]")
fc = ";".join(parts)

cmd = [
    "ffmpeg", "-y", "-hide_banner", "-nostats", *inputs,
    "-filter_complex", fc,
    "-map", "0:v", "-c:v", "copy",
    "-map", "[mix]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", str(prenorm),
]
print(f"mixando {n} SFX sobre {video.name} -> {prenorm.name}")
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

sys.path.insert(0, str(HELPERS))
import render  # noqa: E402
print("loudnorm two-pass -> -14 LUFS")
render.apply_loudnorm_two_pass(prenorm, out, preview=False)
prenorm.unlink(missing_ok=True)
print(f"done: {out}")
