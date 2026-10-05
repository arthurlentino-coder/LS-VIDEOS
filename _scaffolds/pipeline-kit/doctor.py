#!/usr/bin/env python3
"""doctor.py — confere o ambiente pra rodar o console + pipeline em QUALQUER máquina.

Checa binários (ffmpeg/ffprobe/node/npx), o HyperFrames, a estrutura do VIDEOS,
os assets (YuNet, fontes, lib de SFX), os helpers do video-use e as chaves de API.
Imprime ✓/⚠/✗ com dica do que instalar/setar. Exit != 0 se faltar algo essencial.

Uso:  py _scaffolds/pipeline-kit/doctor.py
Env overrides: VIDEOS_ROOT, VIDEO_USE_HELPERS, HF_SFX_DIR, ELEVENLABS_API_KEY
"""
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = Path(os.environ.get("VIDEOS_ROOT") or HERE.parents[2])   # _scaffolds/pipeline-kit/.. /.. = VIDEOS
HOME = Path.home()
oks=[]; warns=[]; fails=[]
def ok(m): oks.append(m)
def warn(m): warns.append(m)
def fail(m): fails.append(m)

def have(bin_): return shutil.which(bin_)

# 1) binários essenciais
for b, hint in [("ffmpeg","instale o ffmpeg e ponha no PATH"),
                ("ffprobe","vem com o ffmpeg"),
                ("node","instale o Node.js LTS"),
                ("npx","vem com o Node.js")]:
    p = have(b)
    (ok(f"{b}: {p}") if p else fail(f"{b} AUSENTE no PATH — {hint}"))

# py launcher (Windows) / python3
py = have("py") or have("python") or have("python3")
ok(f"python: {py or sys.executable}")

# 2) HyperFrames (via npx) — rápido, com timeout
if have("npx"):
    try:
        r = subprocess.run(["npx","--no-install","hyperframes","--version"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            ok(f"hyperframes: {r.stdout.strip() or 'ok'}")
        else:
            warn("hyperframes não resolveu via 'npx --no-install' — rode 'npx hyperframes --version' uma vez p/ instalar")
    except Exception:
        warn("não consegui checar hyperframes (rode 'npx hyperframes --version' uma vez)")

# 3) estrutura do VIDEOS
ok(f"VIDEOS root: {ROOT}")
for d in ["input","output","projects","_scaffolds","apps/mesa-de-corte"]:
    (ok(f"dir {d}/") if (ROOT/d).is_dir() else (warn if d in ("input","output","projects") else fail)(f"dir {d}/ ausente em {ROOT}"))
if not (ROOT/"apps/mesa-de-corte/server.py").is_file():
    fail("apps/mesa-de-corte/server.py não encontrado (raiz errada? use VIDEOS_ROOT)")
else:
    ok("console: apps/mesa-de-corte/server.py")

# 4) assets do pipeline
yunet = ROOT/"_scaffolds/pipeline-kit/edit/hf/yunet.onnx"
(ok("YuNet onnx") if yunet.is_file() else warn(f"YuNet ausente ({yunet}) — facecrop do split não roda"))
sfx = Path(os.environ.get("HF_SFX_DIR") or HOME/".claude/skills/hyperframes-media/assets/sfx")
(ok(f"lib de SFX: {sfx}") if (sfx/"pop.mp3").is_file() else warn(f"lib de SFX ausente ({sfx}) — defina HF_SFX_DIR; áudio por copy fica sem efeitos"))

# 5) helpers do video-use (ficam FORA do repo)
helpers = Path(os.environ.get("VIDEO_USE_HELPERS") or ROOT.parent/"claude"/"video use"/"helpers")
(ok(f"video-use helpers: {helpers}") if (helpers/"render.py").is_file() else warn(f"helpers do video-use ausentes ({helpers}) — defina VIDEO_USE_HELPERS; loudnorm/render podem falhar"))

# 6) chaves de API (opcionais, mas necessárias p/ transcrição/TTS)
(ok("ELEVENLABS_API_KEY definido") if os.environ.get("ELEVENLABS_API_KEY") else warn("ELEVENLABS_API_KEY não definido — Scribe/TTS indisponíveis (defina p/ transcrever)"))

print("=== doctor: ambiente do VIDEOS ===")
for m in oks:  print("  ✓", m)
for m in warns: print("  ⚠", m)
for m in fails: print("  ✗", m)
print(f"--- {len(oks)} ok · {len(warns)} aviso · {len(fails)} falha ---")
if fails:
    print("Faltam itens essenciais — veja SETUP.md.")
sys.exit(1 if fails else 0)

if __name__ == "__main__":
    pass
