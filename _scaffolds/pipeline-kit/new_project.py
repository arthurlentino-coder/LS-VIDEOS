#!/usr/bin/env python3
"""new_project.py — scaffolda projects/<nome>/edit a partir dos scaffolds (kits + EDL stub).

Monta a estrutura que todo projeto usa, copiando os scripts por-projeto + os kits de
split/faceless + stub de hybrid + edl.json, e mostra a RECEITA de master (via master.py --probe).
Não preenche ranges nem renderiza — só prepara o terreno.

Uso:
  py new_project.py CFP_9 --raw "input/CFP/CFP 9.MOV" --cert CFP --lote CFP
"""
import argparse, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # VIDEOS
KIT  = ROOT / "_scaffolds" / "pipeline-kit"
SPLIT_KIT = ROOT / "_scaffolds" / "split-kit"
FACE_KIT  = ROOT / "_scaffolds" / "faceless-kit"

def copy_into(src: Path, dst: Path, skip=()):
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.name in skip or f.name == "__pycache__": continue
        if f.is_dir(): shutil.copytree(f, dst / f.name, dirs_exist_ok=True)
        else: shutil.copy2(f, dst / f.name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name"); ap.add_argument("--raw", required=True)
    ap.add_argument("--cert", default=None); ap.add_argument("--lote", default=None)
    a = ap.parse_args()
    proj = ROOT / "projects" / a.name
    edit = proj / "edit"; hf = edit / "hf"
    if edit.exists():
        print(f"já existe: {edit} (abortando p/ não sobrescrever)"); return
    (edit / "transcripts").mkdir(parents=True, exist_ok=True)
    (edit / "clips_graded").mkdir(parents=True, exist_ok=True)

    # scripts por-projeto: pipeline-kit/edit/hf/* + zoom_concat/fix_transcript/master
    copy_into(KIT / "edit" / "hf", hf)
    for s in ["zoom_concat.py", "fix_transcript.py", "master.py"]:
        src = KIT / "edit" / s
        if src.exists(): shutil.copy2(src, edit / s)

    # split (split-kit -> hf/split/public, template -> index.html)
    sp = hf / "split" / "public"
    copy_into(SPLIT_KIT, sp, skip=("README.md", "top.mp4", "index.template.html"))
    if (SPLIT_KIT / "index.template.html").exists():
        shutil.copy2(SPLIT_KIT / "index.template.html", sp / "index.html")

    # faceless (faceless-kit -> hf/faceless, template -> index.html)
    fc = hf / "faceless"
    copy_into(FACE_KIT, fc, skip=("README.md", "index.template.html"))
    if (FACE_KIT / "index.template.html").exists():
        shutil.copy2(FACE_KIT / "index.template.html", fc / "index.html")

    # hybrid: só fonts + vendor (o card é autorado)
    hy = hf / "hybrid" / "public"; hy.mkdir(parents=True, exist_ok=True)
    for sub in ("fonts", "vendor"):
        if (FACE_KIT / sub).exists(): shutil.copytree(FACE_KIT / sub, hy / sub, dirs_exist_ok=True)

    # edl.json stub
    raw = a.raw.replace("\\", "/")
    key = a.name
    master = f"{edit.as_posix()}/{a.name.lower()}_master_sdr.mp4"
    cert = a.cert or a.name.rstrip("0123456789_-")
    edl = {
        "version": 1,
        "sources": {key: master},
        "source_original": raw,
        "ranges": [],
        "grade": None,
        "note_orientacao": f"{Path(raw).name} -> master SDR bt709. Legenda/certificacao: {cert}. PREENCHER ranges (start/end/beat/quote).",
        "overlays": [], "subtitles": None, "crossfade_s": 0, "total_duration_s": 0,
    }
    (edit / "edl.json").write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"=== projeto {a.name} criado em {edit} ===")
    print("  hf/: scripts + split/public + faceless + hybrid/public (fonts+vendor)")
    print("  edl.json stub (preencher ranges) · transcripts/ (dropar o Scribe)")
    print("próximos passos:")
    print(f"  1) master:   py edit/master.py \"{raw}\" \"{master}\" --probe   (confira a receita, depois sem --probe)")
    print(f"  2) transcrição -> edit/transcripts/ ; corrigir: py edit/fix_transcript.py --file <..> --cert {cert}")
    print(f"  3) preencher edl.json ranges -> py edit/zoom_concat.py (base_zoom)")
    print(f"  4) autorar comps -> bash _scaffolds/pipeline-kit/build_item.sh projects/{a.name} output/{a.lote or cert}/{a.name} {a.lote or cert} \"{a.name}\"")

if __name__ == "__main__":
    main()
