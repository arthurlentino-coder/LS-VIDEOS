#!/usr/bin/env python3
"""QA automático de um lote — varre TODOS os .mp4 em output/<lote>/ (qualquer layout:
flat tipo CPROR_1.mp4/CPROR_1_split.mp4 OU por subpasta normal/split/hybrid/faceless)
e sinaliza só os vídeos suspeitos. Uso: py qa_lote.py <lote> [fmt ...]
Formato inferido pelo sufixo (_split/_hybrid/_faceless; sem sufixo = normal) ou pela subpasta.

Checagens (ffmpeg, rápido):
  duração   — formatos do mesmo combo devem bater (pega fim-da-fala cortado por -shortest)
  loudness  — dentro de -14 ±1.5 LUFS
  preto     — frame realmente preto (pix_th baixo p/ não pegar o navy do faceless)
  mudo      — sem faixa de áudio, ou silêncio longo (>4s)
  formato   — 1080x1920, ~30fps
"""
import subprocess, sys, re, statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]          # VIDEOS
FMTS = ["normal","split","hybrid","faceless"]
LUFS_LO, LUFS_HI = -15.5, -12.5
DUR_TOL = 0.4

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode("utf-8","ignore")

def probe(v):
    out = run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
        "stream=width,height,r_frame_rate","-show_entries","format=duration","-of","default=nw=1",str(v)])
    w=h=dur=None; fps=None
    for ln in out.splitlines():
        if ln.startswith("width="): w=int(ln.split("=")[1])
        elif ln.startswith("height="): h=int(ln.split("=")[1])
        elif ln.startswith("r_frame_rate="):
            a,b=ln.split("=")[1].split("/"); fps=(float(a)/float(b)) if float(b) else None
        elif ln.startswith("duration="):
            try: dur=float(ln.split("=")[1])
            except: pass
    aout = run(["ffprobe","-v","error","-select_streams","a","-show_entries","stream=codec_type","-of","csv=p=0",str(v)])
    has_audio = "audio" in aout
    return w,h,fps,dur,has_audio

def analyze(v):
    out = run(["ffmpeg","-hide_banner","-nostats","-i",str(v),
        "-vf","scale=320:-2,blackdetect=d=0.12:pix_th=0.05:pic_th=0.98",
        "-af","silencedetect=noise=-50dB:d=4,ebur128","-f","null","-"])
    lufs = None
    m = re.findall(r"I:\s*(-?[0-9.]+)\s*LUFS", out)
    if m: lufs = float(m[-1])
    blacks = re.findall(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)", out)
    sil = re.findall(r"silence_duration:\s*([0-9.]+)", out)
    return lufs, blacks, sil

def classify(v):
    """(combo, fmt) a partir do nome/subpasta — genérico p/ qualquer lote."""
    name = v.stem
    for f in ("split", "hybrid", "faceless"):
        if name.endswith("_" + f):
            return name[:-(len(f) + 1)], f
    p = v.parent.name
    fmt = p if p in FMTS else "normal"
    return name, fmt

def main():
    if len(sys.argv) < 2: print(__doc__); return
    lote = sys.argv[1]; only = set(sys.argv[2:])
    base = ROOT/"output"/lote
    if not base.is_dir(): print("sem pasta de saída:", base); return
    combo_durs = defaultdict(dict)
    reports = {}   # video -> [flags]
    files = sorted(p for p in base.rglob("*.mp4") if "_trash" not in p.parts)
    if only: files = [v for v in files if classify(v)[1] in only]
    print(f"QA {lote} — {len(files)} vídeos\n")
    for i,v in enumerate(files):
        name = v.stem
        combo, fmt = classify(v)
        flags = []
        w,h,fps,dur,has_audio = probe(v)
        if (w,h) != (1080,1920): flags.append(f"dimensão {w}x{h}")
        if fps and abs(fps-30) > 1: flags.append(f"fps {fps:.1f}")
        if dur: combo_durs[combo][fmt] = dur
        if not has_audio: flags.append("SEM áudio")
        lufs, blacks, sil = analyze(v)
        if lufs is None: flags.append("loudness ilegível")
        elif not (LUFS_LO <= lufs <= LUFS_HI): flags.append(f"loudness {lufs:.1f} LUFS")
        for (bs,be) in blacks:
            flags.append(f"preto {float(bs):.1f}-{float(be):.1f}s")
        for sd in sil:
            if float(sd) >= 4: flags.append(f"silêncio {float(sd):.1f}s")
        if flags: reports[name] = flags
        if (i+1) % 20 == 0: print(f"  ...{i+1}/{len(files)}", flush=True)
    # cross-check de duração por combo
    for combo, ds in combo_durs.items():
        if len(ds) < 2: continue
        ref = max(ds.values())
        for fmt, dv in ds.items():
            if ref - dv > DUR_TOL:
                reports.setdefault(f"{combo}_{fmt}", []).append(f"duração {dv:.1f}s (combo ~{ref:.1f}s, {ref-dv:.1f}s curto)")
    # relatório
    print(f"\n{'='*46}\nRESULTADO QA {lote}")
    ok = len(files) - len(reports)
    print(f"✓ {ok} ok  |  ⚠ {len(reports)} com aviso\n")
    for name in sorted(reports):
        print(f"⚠ {name} — {'; '.join(reports[name])}")
    if not reports: print("Nenhum problema encontrado. 🎉")
    # salva
    rep = base/"_qa_report.txt"
    rep.write_text(f"QA {lote}: {ok} ok, {len(reports)} avisos\n\n" +
        "\n".join(f"{n} — {'; '.join(fl)}" for n,fl in sorted(reports.items())), "utf-8")
    print(f"\nrelatório salvo em {rep}")

if __name__=="__main__": main()
