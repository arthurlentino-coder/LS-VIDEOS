#!/usr/bin/env python3
"""doctor.py — confere (e opcionalmente INSTALA) o ambiente do VIDEOS em qualquer máquina.

  py _scaffolds/pipeline-kit/doctor.py           # só diagnostica (✓/⚠/✗)
  py _scaffolds/pipeline-kit/doctor.py --fix      # tenta instalar o que falta e re-checa

--fix instala sozinho: pacotes Python (opencv/onnxruntime/numpy/librosa/requests/yt-dlp),
aquece o HyperFrames (npx), e tenta ffmpeg/Node via winget. NÃO automatiza (precisa de você):
mídia (input/), helpers do video-use (fora do repo) e ELEVENLABS_API_KEY.
Env overrides: VIDEOS_ROOT, VIDEO_USE_HELPERS, HF_SFX_DIR.
"""
import argparse, importlib.util, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = Path(os.environ.get("VIDEOS_ROOT") or HERE.parents[2])
HOME = Path.home()
PYPKGS = ["opencv-python-headless", "onnxruntime", "numpy", "librosa", "requests", "yt-dlp"]
PYMODS = {"cv2": "opencv-python-headless", "onnxruntime": "onnxruntime", "numpy": "numpy"}

def have(b): return shutil.which(b)
def run(cmd, timeout=600):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)

def fix(args):
    print("=== doctor --fix: instalando o que dá ===")
    # 1) pacotes Python
    print("  pip install (pacotes Python)…")
    rc, out = run([sys.executable, "-m", "pip", "install", "--quiet", *PYPKGS])
    print("    " + ("ok" if rc == 0 else "FALHOU: " + out.strip().splitlines()[-1] if out.strip() else "FALHOU"))
    # 2) HyperFrames (aquece/baixa via npx)
    if have("npx"):
        print("  npx hyperframes (baixando CLI)…")
        rc, out = run(["npx", "-y", "hyperframes", "--version"], timeout=300)
        print("    " + ("ok: " + out.strip().splitlines()[-1] if rc == 0 and out.strip() else "aviso (rode 'npx hyperframes --version' manual)"))
    # 3) ffmpeg / node via winget (se faltarem)
    if have("winget"):
        if not have("ffmpeg"):
            print("  winget install ffmpeg…")
            rc, _ = run(["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                         "--accept-source-agreements", "--accept-package-agreements"], timeout=600)
            print("    " + ("ok (reabra o terminal p/ o PATH)" if rc == 0 else "FALHOU — instale o ffmpeg manual"))
        if not have("node"):
            print("  winget install Node.js LTS…")
            rc, _ = run(["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS",
                         "--accept-source-agreements", "--accept-package-agreements"], timeout=600)
            print("    " + ("ok (reabra o terminal p/ o PATH)" if rc == 0 else "FALHOU — instale o Node manual"))
    else:
        print("  winget ausente — instale ffmpeg e Node manualmente se faltarem")
    print("--- re-checando ---\n")

def check():
    oks=[]; warns=[]; fails=[]
    ok=oks.append; warn=warns.append; fail=fails.append
    for b, hint in [("ffmpeg","instale o ffmpeg no PATH"),("ffprobe","vem com o ffmpeg"),
                    ("node","instale o Node.js LTS"),("npx","vem com o Node.js")]:
        p=have(b); (ok(f"{b}: {p}") if p else fail(f"{b} AUSENTE — {hint}"))
    ok(f"python: {have('py') or sys.executable}")
    # pacotes python
    for mod, pkg in PYMODS.items():
        (ok(f"py:{mod}") if importlib.util.find_spec(mod) else warn(f"py:{mod} ausente — pip install {pkg} (ou --fix)"))
    # hyperframes
    if have("npx"):
        rc, out = run(["npx","--no-install","hyperframes","--version"], timeout=30)
        (ok(f"hyperframes: {out.strip().splitlines()[-1]}") if rc==0 and out.strip() else warn("hyperframes não resolveu — rode --fix ou 'npx hyperframes --version'"))
    # estrutura
    ok(f"VIDEOS root: {ROOT}")
    for d in ["input","output","projects","_scaffolds","apps/mesa-de-corte"]:
        (ok(f"dir {d}/") if (ROOT/d).is_dir() else (warn if d in ("input","output","projects") else fail)(f"dir {d}/ ausente"))
    (ok("console: server.py") if (ROOT/"apps/mesa-de-corte/server.py").is_file() else fail("server.py não achado (raiz errada? use VIDEOS_ROOT)"))
    # assets
    (ok("YuNet onnx") if (ROOT/"_scaffolds/pipeline-kit/edit/hf/yunet.onnx").is_file() else warn("YuNet ausente — facecrop do split não roda"))
    sfx = Path(os.environ.get("HF_SFX_DIR") or HOME/".claude/skills/hyperframes-media/assets/sfx")
    (ok(f"lib de SFX: {sfx}") if (sfx/"pop.mp3").is_file() else warn(f"lib de SFX ausente ({sfx}) — defina HF_SFX_DIR"))
    helpers = Path(os.environ.get("VIDEO_USE_HELPERS") or ROOT.parent/"claude"/"video use"/"helpers")
    (ok(f"video-use helpers: {helpers}") if (helpers/"render.py").is_file() else warn(f"helpers do video-use ausentes ({helpers}) — instale (SETUP.md §3) e/ou defina VIDEO_USE_HELPERS"))
    (ok("ELEVENLABS_API_KEY") if os.environ.get("ELEVENLABS_API_KEY") else warn("ELEVENLABS_API_KEY não definido — transcrição indisponível"))
    return oks, warns, fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    if a.fix:
        fix(a)
    oks, warns, fails = check()
    print("=== doctor: ambiente do VIDEOS ===")
    for m in oks:  print("  ✓", m)
    for m in warns: print("  ⚠", m)
    for m in fails: print("  ✗", m)
    print(f"--- {len(oks)} ok · {len(warns)} aviso · {len(fails)} falha ---")
    if fails: print("Faltam itens essenciais — veja SETUP.md (ou rode com --fix).")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
