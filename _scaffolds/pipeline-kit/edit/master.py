#!/usr/bin/env python3
"""master.py — gera o master SDR da bruta escolhendo a receita AUTOMATICAMENTE.

Quase toda cilada de lote é "qual receita de master": HLG/PQ→tonemap SDR, rotação
packet-level→transpose, retrato girado, fps. Isto faz ffprobe da bruta e decide:
  - tonemap  : se color_transfer é HLG (arib-std-b67) ou PQ (smpte2084)  [--tonemap on|off força]
  - transpose: do metadado rotate (-90→1, +90→2, 180→1,1)                [--rotate none|1|2|180 força]
               (brutas "paisagem mas giradas" NÃO têm metadado → passe --rotate 1 na mão)
  - fps      : normaliza p/ --fps (default 30)
Sempre imprime a DECISÃO (confira). `--probe` só mostra a detecção, não encoda.

Uso:
  py master.py "input/CFP/CFP 7.MOV" projects/CFP_7/edit/cfp7_master_sdr.mp4
  py master.py <raw> <out> --rotate 1            # força transpose (retrato girado sem metadado)
  py master.py <raw> <out> --probe               # só detecta
"""
import argparse, json, subprocess, sys
from pathlib import Path

HLG = {"arib-std-b67"}; PQ = {"smpte2084", "smpte2084/pq"}
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

def probe(raw):
    out = subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,color_transfer,color_space:stream_tags=rotate:side_data=rotation",
        "-of","json",str(raw)]).decode()
    j = json.loads(out)["streams"][0]
    rot = j.get("tags", {}).get("rotate")
    if rot is None:
        for sd in j.get("side_data_list", []):
            if "rotation" in sd: rot = sd["rotation"]; break
    try: rot = int(float(rot)) if rot is not None else 0
    except Exception: rot = 0
    return dict(w=j.get("width"), h=j.get("height"),
                trc=j.get("color_transfer",""), csp=j.get("color_space",""), rot=rot)

def decide(info, rotate, tonemap):
    tm = (info["trc"] in HLG or info["trc"] in PQ) if tonemap == "auto" else (tonemap == "on")
    if rotate == "auto":
        r = info["rot"]
        tr = {(-90): "transpose=1", 90: "transpose=2", 180: "transpose=1,transpose=1"}.get(r, "")
    else:
        tr = {"none": "", "1": "transpose=1", "2": "transpose=2", "180": "transpose=1,transpose=1"}[rotate]
    return tm, tr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("out")
    ap.add_argument("--rotate", default="auto", choices=["auto","none","1","2","180"])
    ap.add_argument("--tonemap", default="auto", choices=["auto","on","off"])
    ap.add_argument("--fps", default="30"); ap.add_argument("--crf", default="18")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    info = probe(a.raw)
    tm, tr = decide(info, a.rotate, a.tonemap)
    vf = [p for p in [tr, (TONEMAP if tm else "format=yuv420p"), f"fps={a.fps}"] if p]
    vfs = ",".join(vf)
    print(f"=== master: {Path(a.raw).name} ===")
    print(f"  bruta: {info['w']}x{info['h']} trc={info['trc'] or '-'} csp={info['csp'] or '-'} rotate={info['rot']}")
    print(f"  decisão: tonemap={'SIM' if tm else 'não'}  transpose={tr or 'não'}  fps={a.fps}")
    print(f"  -vf {vfs}")
    if a.probe:
        return
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(a.raw),
           "-vf",vfs,"-c:v","libx264","-crf",a.crf,"-preset","medium",
           "-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
           "-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",str(a.out)]
    subprocess.run(cmd, check=True)
    print(f"  master -> {a.out}")

if __name__ == "__main__":
    main()
