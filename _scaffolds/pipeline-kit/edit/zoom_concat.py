"""zoom_concat.py — TESTE: troca o crossfade dos cortes por um ZOOM que SEGURA,
ALTERNANDO in/out a cada corte (pra nao ir sempre apertando o enquadramento).

A cada corte a cena da um zoom rapido (ZOOM_T s, ease smoothstep) e FICA PARADA
ate o proximo corte. A direcao alterna: corte 1 = in, corte 2 = out, corte 3 = in...
Como alterna, cada segmento COMECA no nivel onde o anterior parou -> sem salto de
escala no corte, so o movimento suave (LOW=1.0 <-> HIGH=1+PUNCH):
  seg0 1.0 | corte->in 1.0->1.12 segura | corte->out 1.12->1.0 segura | corte->in ...
Corte seco (sem dissolve) -> a transicao e o proprio movimento de zoom.

Reaproveita render.extract_all_segments (mesma extracao/tonemap/scale/fps/fades).
Saida: edit/base_zoom.mp4 (SEM legenda — so pra avaliar o feel do zoom).

IMPORTANTE: corte seco remove o overlap de 130ms do xfade, entao a legenda
precisa ser re-sincronizada com crossfade=0 (feito depois, se aprovado).
"""
from __future__ import annotations

import json
import subprocess
import sys
import os
from pathlib import Path

# helpers do video-use: env VIDEO_USE_HELPERS, senao <pai de VIDEOS>/claude/video use/helpers
_here = Path(__file__).resolve()
_videos = next((p for p in _here.parents if (p / "input").is_dir()), _here.parents[3])
HELPERS = Path(os.environ.get("VIDEO_USE_HELPERS") or _videos.parent / "claude" / "video use" / "helpers")
sys.path.insert(0, str(HELPERS))
import render  # noqa: E402

EDIT = Path(__file__).resolve().parent

# defaults (sobrescreviveis por CLI: --mode --punch --hold --zoom-t --start-dir --out)
DEF_PUNCH = 0.12       # 12% de ampliacao (HIGH = 1+PUNCH); no MODE="masked" e o PICO no corte
DEF_HOLD = 0.06        # (MODE="masked") nivel de zoom SEGURADO nos trechos "zoom" (1+HOLD)
DEF_ZOOM_T = 0.22      # tempo do movimento de zoom (s); no "masked" e a meia-transicao no corte
DEF_START_DIR = "in"   # direcao do 1o segmento/corte; alterna a cada segmento seguinte
DEF_MODE = "static"    # "smooth": zoom LENTO e suave (ease in/out) ao longo do corte
                       #           inteiro, alternando in/out, continuo |
                       # "static": o corte JA entra no novo zoom (sem animacao) — jump-cut |
                       # "animated": zoom rapido depois do corte e segura


def probe_dims(p: Path) -> tuple[int, int]:
    import re
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "default=nw=1", str(p)],
        capture_output=True, text=True, check=True).stdout
    nums = [int(x) for x in re.findall(r"(?:width|height)=(\d+)", out)]
    return nums[0], nums[1]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default=DEF_MODE, choices=["smooth", "static", "animated", "cut", "masked", "seam"])
    ap.add_argument("--punch", type=float, default=DEF_PUNCH)
    ap.add_argument("--hold", type=float, default=DEF_HOLD)
    ap.add_argument("--zoom-t", type=float, default=DEF_ZOOM_T)
    ap.add_argument("--start-dir", default=DEF_START_DIR, choices=["in", "out"])
    ap.add_argument("--mblur", action="store_true", help="motion blur no zoom (sobreamostra + tmix)")
    ap.add_argument("--mblur-os", type=int, default=4, help="fator de sobreamostragem do motion blur")
    ap.add_argument("--out", default=str(EDIT / "base_zoom.mp4"))
    args = ap.parse_args()
    MODE, PUNCH, ZOOM_T, START_DIR, HOLD = args.mode, args.punch, args.zoom_t, args.start_dir, args.hold
    MBLUR, OS = args.mblur, max(2, args.mblur_os)
    out_path = Path(args.out)

    edl = json.loads((EDIT / "edl.json").read_text(encoding="utf-8"))
    # reaproveita clips_graded se ja extraidos (evita re-extrair em cada teste)
    clips = EDIT / "clips_graded"
    expect = [clips / f"seg_{i:02d}_{r['source']}.mp4" for i, r in enumerate(edl["ranges"])]
    if all(p.exists() for p in expect):
        print("clips_graded ja existe — reaproveitando (pulando extracao)")
        segs = expect
    else:
        segs = render.extract_all_segments(edl, EDIT, preview=False)
    n = len(segs)
    W, H = probe_dims(segs[0])

    # smoothstep saturado: Sc = 0 em t=0, sobe ate 1 em ZOOM_T e SEGURA em 1 depois.
    # cada segmento move de z0 -> z1: Z = z0 + (z1-z0)*Sc. scale animado (eval=frame +
    # variavel t) amplia; crop central estatico devolve WxH. Aspas simples = virgulas
    # literais (nao quebram o filtergraph).
    T = ZOOM_T
    S = f"(t/{T})*(t/{T})*(3-2*(t/{T}))"
    Sc = f"if(gt(t,{T}),1,{S})"
    LOW, HIGH = 1.0, 1.0 + PUNCH
    CROP = f"crop={W}:{H}:(in_w-{W})/2:(in_h-{H})/2,setsar=1,format=yuv420p"

    def static_filter(Z: float) -> str:
        if abs(Z - 1.0) < 1e-6:
            return "setsar=1,format=yuv420p"      # nivel normal: passa direto
        return f"scale=w=iw*{Z:.4f}:h=ih*{Z:.4f}:flags=bicubic,{CROP}"

    def animated_filter(z0: float, z1: float) -> str:
        Z = f"{z0:.4f}+({z1 - z0:.4f})*({Sc})"
        return f"scale=w='iw*({Z})':h='ih*({Z})':eval=frame:flags=bicubic,{CROP}"

    def smooth_filter(z0: float, z1: float, dur: float) -> str:
        # zoom LENTO z0->z1 ao longo do clip inteiro, ease in/out (smoothstep de t/dur)
        P = f"clip(t/{dur:.4f},0,1)"
        Sm = f"({P})*({P})*(3-2*({P}))"
        Z = f"{z0:.4f}+({z1 - z0:.4f})*({Sm})"
        return f"scale=w='iw*({Z})':h='ih*({Z})':eval=frame:flags=bicubic,{CROP}"

    def cut_filter(cut_before: bool, cut_after: bool, dur: float) -> str:
        # ZOOM PUNCH so no corte: pico de zoom na fronteira do corte, ease, e NORMAL no
        # meio. Th = meia-duracao da transicao (cada lado). cut_before: clip comeca no
        # pico e abre ate normal (ease-out). cut_after: clip fecha ate o pico antes do
        # corte (ease-in). Isso "atravessa" o corte com um zoom in->out, mascarando-o.
        Th = ZOOM_T
        terms = []
        if cut_before:                              # rampa no inicio: pico(t=0) -> 0 em Th
            p = f"clip(t/{Th:.4f},0,1)"
            terms.append(f"(1-(({p})*({p})*(3-2*({p}))))")
        if cut_after:                               # rampa no fim: 0 -> pico(t=dur)
            q = f"clip((t-{dur - Th:.4f})/{Th:.4f},0,1)"
            terms.append(f"(({q})*({q})*(3-2*({q})))")
        if not terms:
            return "setsar=1,format=yuv420p"        # sem cortes adjacentes: normal
        Z = f"1+{PUNCH:.4f}*({'+'.join(terms)})"
        return f"scale=w='iw*({Z})':h='ih*({Z})':eval=frame:flags=bicubic,{CROP}"

    def masked_filter(Lc: float, dur: float, cb: bool, ca: bool) -> str:
        # PICO de zoom (1+PUNCH) CENTRADO no corte (mascara o salto), assentando no
        # nivel segurado Lc. cb: metade pos-corte (pico->Lc). ca: metade pre-corte
        # (Lc->pico). Continuidade: os dois lados do corte no PICO -> sem salto de escala,
        # e o movimento rapido acontece EM CIMA do corte.
        Th = ZOOM_T
        peak = 1.0 + PUNCH
        amp = peak - Lc
        terms = [f"{Lc:.4f}"]
        if cb:
            p = f"clip(t/{Th:.4f},0,1)"
            terms.append(f"({amp:.4f})*(1-(({p})*({p})*(3-2*({p}))))")
        if ca:
            q = f"clip((t-{dur - Th:.4f})/{Th:.4f},0,1)"
            terms.append(f"({amp:.4f})*(({q})*({q})*(3-2*({q})))")
        if len(terms) == 1 and abs(Lc - 1.0) < 1e-6:
            return "setsar=1,format=yuv420p"
        Z = "+".join(terms)
        return f"scale=w='iw*({Z})':h='ih*({Z})':eval=frame:flags=bicubic,{CROP}"

    def seam_filter(Lp: float, Lc: float, Ln: float, dur: float, cb: bool, ca: bool) -> str:
        # transicao MONOTONICA (um sentido so) centrada no corte: o trecho vai do
        # meio-caminho com o vizinho anterior (t=0) ate Lc, e de Lc ate o meio-caminho
        # com o proximo (t=dur). Como encontra o vizinho no ponto medio, o corte fica
        # continuo (sem salto) e o movimento (zoom in OU out, nunca os dois) passa EM
        # CIMA do corte -> mascara, sem "ir e voltar".
        # Curvas com velocidade MAXIMA NO CORTE (mascara): saindo do corte desacelera
        # (ease-out, (1-p)^2); chegando no corte acelera (ease-in, p^2).
        Th = ZOOM_T
        terms = [f"{Lc:.4f}"]
        if cb:
            p = f"clip(t/{Th:.4f},0,1)"
            d = (Lp - Lc) / 2.0
            terms.append(f"({d:.4f})*(1-({p}))*(1-({p}))")
        if ca:
            q = f"clip((t-{dur - Th:.4f})/{Th:.4f},0,1)"
            d = (Ln - Lc) / 2.0
            terms.append(f"({d:.4f})*({q})*({q})")
        if len(terms) == 1 and abs(Lc - 1.0) < 1e-6:
            return "setsar=1,format=yuv420p"
        Z = "+".join(terms)
        return f"scale=w='iw*({Z})':h='ih*({Z})':eval=frame:flags=bicubic,{CROP}"

    durs = [float(r["end"]) - float(r["start"]) for r in edl["ranges"]]
    sf, dirs = [None] * n, []                 # sf[i] = filtro de video do segmento i
    if MODE == "cut":
        # zoom punch SO no corte; normal no meio de cada trecho
        for i in range(n):
            cb, ca = (i > 0), (i < n - 1)
            sf[i] = cut_filter(cb, ca, durs[i]); dirs.append(("punch", cb, ca))
    elif MODE == "seam":
        # transicao monotonica (um sentido) centrada no corte; niveis alternam
        # (1+HOLD nos "zoom", 1.0 nos "normal"). START_DIR="in" -> comeca no zoom.
        levels = [(1.0 + HOLD) if ((i % 2 == 0) == (START_DIR == "in")) else 1.0 for i in range(n)]
        for i in range(n):
            Lp = levels[i - 1] if i > 0 else levels[i]
            Ln = levels[i + 1] if i < n - 1 else levels[i]
            cb, ca = (i > 0), (i < n - 1)
            sf[i] = seam_filter(Lp, levels[i], Ln, durs[i], cb, ca); dirs.append(("seam", round(levels[i], 3)))
    elif MODE == "masked":
        # PICO de zoom em cima de cada corte (mascara), assentando no nivel alternado
        levels = [(1.0 + HOLD) if ((i % 2 == 0) == (START_DIR == "in")) else 1.0 for i in range(n)]
        for i in range(n):
            cb, ca = (i > 0), (i < n - 1)
            sf[i] = masked_filter(levels[i], durs[i], cb, ca); dirs.append(("masked", round(levels[i], 3)))
    elif MODE == "smooth":
        # todos os segmentos se movem, alternando; comeca onde o anterior parou
        for i in range(n):
            is_in = (i % 2 == 0) == (START_DIR == "in")
            z0, z1 = (LOW, HIGH) if is_in else (HIGH, LOW)
            sf[i] = smooth_filter(z0, z1, durs[i]); dirs.append(("in" if is_in else "out", round(z0, 3), round(z1, 3)))
    elif MODE == "static":
        sf[0] = "setsar=1,format=yuv420p"
        for i in range(1, n):
            is_in = (i % 2 == 1) == (START_DIR == "in")
            level = HIGH if is_in else LOW
            sf[i] = static_filter(level); dirs.append(("tight" if is_in else "normal", round(level, 3)))
    else:  # animated: cada trecho SEGURA um nivel alternando (seg0 = START_DIR), transicao SUAVE no corte
        levels = [HIGH if ((i % 2 == 0) == (START_DIR == "in")) else LOW for i in range(n)]
        for i in range(n):
            tgt = levels[i]
            if i == 0:
                sf[i] = static_filter(tgt); dirs.append(("start", round(tgt, 3)))
            else:
                sf[i] = animated_filter(levels[i - 1], tgt); dirs.append(("ease", round(levels[i - 1], 3), round(tgt, 3)))

    # montagem — com MOTION BLUR opcional: sobreamostra o zoom (fps alto) e media os
    # frames (tmix). Como as fontes sao 30fps, so o MOVIMENTO DO ZOOM borra (o sujeito,
    # duplicado dentro da janela, fica nitido). Depois decima de volta pro fps de saida.
    fps_int = int(round(float(render.OUTPUT_FPS)))
    parts = []
    if MBLUR:
        hi = fps_int * OS
        for i in range(n):
            parts.append(f"[{i}:v]fps={hi},{sf[i]}[vz{i}]")
        concat_in = "".join(f"[vz{i}][{i}:a]" for i in range(n))
        parts.append(f"{concat_in}concat=n={n}:v=1:a=1[vc][a]")
        parts.append(f"[vc]tmix=frames={OS},fps={fps_int}[v]")
    else:
        for i in range(n):
            parts.append(f"[{i}:v]{sf[i]}[vz{i}]")
        concat_in = "".join(f"[vz{i}][{i}:a]" for i in range(n))
        parts.append(f"{concat_in}concat=n={n}:v=1:a=1[v][a]")
    filter_complex = ";".join(parts)

    inputs: list[str] = []
    for p in segs:
        inputs += ["-i", str(p)]

    out = out_path
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", render.OUTPUT_FPS,
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(out),
    ]
    print(f"[{MODE}] concat punch={PUNCH*100:.0f}% -> {out.name}")
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print("FFMPEG ERRO:\n" + "\n".join(r.stderr.strip().splitlines()[-15:]))
        sys.exit(1)

    # timestamps das junções na NOVA timeline (corte seco)
    cum = 0.0
    js = []
    for i, r in enumerate(edl["ranges"]):
        cum += float(r["end"]) - float(r["start"])
        if i < n - 1:
            js.append(round(cum, 2))
    print(f"done: {out}  | cortes em: {js} s  | zoom por corte: {dirs}")


if __name__ == "__main__":
    main()
