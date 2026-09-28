r"""hf_subs.py — gera um projeto HyperFrames de LEGENDA ANIMADA (overlay transparente)
direto do edl.json + transcripts (tempo por PALAVRA na timeline de saida).

Replica 1:1 a estetica da legenda arredondada (round_subs.py) e adiciona animacao
SINCRONIZADA com a fala:
  - cada palavra aparece no seu tempo real falado (reveal word-synced)
  - frases agrupadas de forma BALANCEADA (sem palavra orfa solta)
  - caixa entra com fade+scale; sai com fade que termina ANTES da proxima cue
    (zero sobreposicao / nunca mostra duas legendas juntas)

Mapeamento de tempo (igual ao build_subs.py / Hard Rule 5):
    out_time = word.start - seg_start + offset ;  offset += seg_dur - crossfade

Geometria por preset (igual ao round_subs.py):
  vertical  (9:16): 1080x1920, Arial 59, pad 33/33, raio 16, box_bottom 1486
  landscape (16:9): 1920x1080, Arial 44, pad 26/22, raio 13, box_bottom 1016

Uso:
  python hf_subs.py --edl <edit/edl.json> --out-dir <edit/hf/subs-animated> \
                    --duration 55.012 --preset vertical
Depois: hf.ps1 lint  ->  hf.ps1 render --format webm -o ..\subs-animated.webm
        -> compor o webm sobre o base.mp4 (compose_hfsubs.py; forca -c:v libvpx-vp9).

REGRA DO PROCESSO: so rodar quando o usuario pedir legenda animada.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

ARIAL_SRC = Path(r"C:\Windows\Fonts\arial.ttf")

PRESETS = {
    "vertical":  dict(W=1080, H=1920, font=59, pad_x=33, pad_y=33, radius=16,
                      box_bottom=1486, line_h=67),
    "landscape": dict(W=1920, H=1080, font=44, pad_x=26, pad_y=22, radius=13,
                      box_bottom=1016, line_h=50),
}

SENTENCE_END = set(".?!")
GAP_BREAK = 0.45          # nova "respiracao" apos silencio >= isso (s)

# palavras fracas que NAO devem terminar uma linha (preposicao/conjuncao/artigo):
# quebrar logo depois delas fica pendurado e le mal. Penalizado no DP.
WEAK_END = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "e", "ou", "que", "se",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos", "por",
    "pra", "para", "com", "sem", "ao", "aos", "sobre", "sob", "ate", "como",
    "mais", "muito", "seu", "sua", "meu", "minha",
}
WEAK_PENALTY = 170        # ~= 13 chars de folga^2; dobra, mas nao impede


# ---------------------------------------------------------------------------
# 1) palavras na timeline de saida (a partir do edl.json + transcripts)
# ---------------------------------------------------------------------------
def words_out_timeline(edl_path: Path, crossfade: float | None = None) -> list[dict]:
    edit = edl_path.parent
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    xfade = float(edl.get("crossfade_s") or 0.0) if crossfade is None else float(crossfade)
    transcripts = edit / "transcripts"

    out: list[dict] = []
    offset = 0.0
    for r in edl["ranges"]:
        src = r["source"]
        seg_start, seg_end = float(r["start"]), float(r["end"])
        seg_dur = seg_end - seg_start
        tr_path = transcripts / f"{src}.json"
        if tr_path.exists():
            tr = json.loads(tr_path.read_text(encoding="utf-8"))
            for w in tr.get("words", []):
                if w.get("type") != "word":
                    continue
                ws, we = w.get("start"), w.get("end")
                txt = (w.get("text") or "").strip()
                if ws is None or we is None or not txt:
                    continue
                if we <= seg_start or ws >= seg_end:
                    continue
                ls = max(seg_start, ws)
                le = min(seg_end, we)
                out.append({
                    "text": txt,
                    "s": max(0.0, ls - seg_start) + offset,
                    "e": max(0.0, le - seg_start) + offset,
                })
        offset += seg_dur - xfade

    out.sort(key=lambda w: w["s"])

    # Funde tokens SO de pontuacao (ex.: o Scribe emite "," como "palavra" separada)
    # na palavra ANTERIOR -> "seguinte" + "," = "seguinte,". Assim nenhuma cue comeca
    # com pontuacao e o karaoke nao "acende" uma virgula sozinha. Se a pontuacao vier
    # antes de qualquer palavra, e descartada.
    merged: list[dict] = []
    for w in out:
        if not any(c.isalnum() for c in w["text"]):
            if merged:
                merged[-1]["text"] += w["text"]
                merged[-1]["e"] = max(merged[-1]["e"], w["e"])
            continue
        merged.append(w)
    return merged


# ---------------------------------------------------------------------------
# 2) agrupar em cues de UMA linha, BALANCEADAS (DP minimiza irregularidade,
#    o que evita "palavra orfa" no fim). Quebra dura em fim-de-frase / silencio.
# ---------------------------------------------------------------------------
def _wrap_group(words: list[dict], max_chars: int) -> list[list[dict]]:
    n = len(words)
    if n == 0:
        return []
    L = [len(w["text"]) for w in words]
    bare = [re.sub(r"[^\wáàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ]", "", w["text"].lower())
            for w in words]

    def width(i: int, j: int) -> int:          # palavras i..j-1
        return sum(L[i:j]) + (j - i - 1)

    INF = float("inf")
    # cost[i] = melhor custo para quebrar words[i:]
    cost = [INF] * (n + 1)
    nxt = [n] * (n + 1)
    cost[n] = 0.0
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            w = width(i, j)
            if w > max_chars and j > i + 1:
                break                            # linha estourou (1 palavra sempre cabe)
            slack = max_chars - w
            c = (slack * slack) + cost[j]        # penaliza TODAS as linhas (anti-orfa)
            if j < n and bare[j - 1] in WEAK_END:  # nao termina linha em palavra fraca
                c += WEAK_PENALTY
            if c < cost[i]:
                cost[i] = c
                nxt[i] = j
    lines, i = [], 0
    while i < n:
        j = nxt[i]
        lines.append(words[i:j])
        i = j
    return lines


def build_cues(words: list[dict], max_chars: int) -> list[dict]:
    # quebra em grupos por fim-de-frase ou silencio
    groups: list[list[dict]] = []
    cur: list[dict] = []
    for k, w in enumerate(words):
        cur.append(w)
        ends_sentence = w["text"][-1] in SENTENCE_END
        gap_next = (words[k + 1]["s"] - w["e"]) if k + 1 < len(words) else 0.0
        if ends_sentence or gap_next >= GAP_BREAK:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    cues: list[dict] = []
    for g in groups:
        for line in _wrap_group(g, max_chars):
            # reforco: nenhuma linha comeca com pontuacao (tira virgula/aspas/reticencias
            # remanescentes no inicio da 1a palavra). Nao mexe no resto nem no fim.
            words = [dict(w) for w in line]
            stripped = re.sub(r"^[^\w]+", "", words[0]["text"], flags=re.UNICODE)
            if stripped:
                words[0]["text"] = stripped
            cues.append({
                "s": round(words[0]["s"], 3),
                "e": round(words[-1]["e"], 3),
                "words": [{"t": round(w["s"], 3), "tx": w["text"]} for w in words],
            })

    # sem sobreposicao: fim de cada cue <= inicio da proxima
    for i in range(len(cues) - 1):
        cues[i]["e"] = min(cues[i]["e"], cues[i + 1]["s"])
        if cues[i]["e"] <= cues[i]["s"]:
            cues[i]["e"] = cues[i]["s"] + 0.25
            cues[i]["e"] = min(cues[i]["e"], cues[i + 1]["s"])
        # reveal de cada palavra nao pode passar do fim da cue
        for wd in cues[i]["words"]:
            wd["t"] = min(wd["t"], cues[i]["e"] - 0.04)
            wd["t"] = max(wd["t"], cues[i]["s"])

    # cues ultra-curtas (ex.: um "E" isolado de 0.10s) TRAVAM no capture do HyperFrames:
    # a animacao de entrada (0.18s) e a de saida (c.e-0.07) colidem e a caixa fica visivel
    # a cena inteira. Garante uma duracao minima de exibicao, sem sobrepor a proxima cue.
    MIN_CUE_DUR = 0.40
    for i in range(len(cues)):
        nxt_s = cues[i + 1]["s"] if i + 1 < len(cues) else None
        want_e = cues[i]["s"] + MIN_CUE_DUR
        if nxt_s is not None:
            want_e = min(want_e, nxt_s)
        if cues[i]["e"] < want_e:
            cues[i]["e"] = round(want_e, 3)
    return cues


# ---------------------------------------------------------------------------
# 3) HTML da composicao
# ---------------------------------------------------------------------------
def build_html(cues: list[dict], dur: float, p: dict) -> str:
    bottom_from_foot = p["H"] - p["box_bottom"]

    cue_divs = []
    for i, c in enumerate(cues):
        spans = " ".join(
            f'<span class="w">{html.escape(w["tx"])}</span>' for w in c["words"]
        )
        cue_divs.append(f'<div class="cue"><div class="box" id="box-{i}">{spans}</div></div>')
    cues_html = "\n      ".join(cue_divs)
    cues_json = json.dumps(cues, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={p['W']}, height={p['H']}" />
    <title>Legenda animada (overlay)</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{
        font-family: 'ArialLocal';
        src: url('arial.ttf') format('truetype');
        font-weight: 400;
      }}
      body {{ margin: 0; background: transparent; }}
      #root {{ position: relative; width: {p['W']}px; height: {p['H']}px; overflow: hidden; background: transparent; }}
      .cue {{
        position: absolute; left: 0; right: 0; bottom: {bottom_from_foot}px;
        display: flex; justify-content: center;
      }}
      .box {{
        opacity: 0;
        display: inline-block; white-space: nowrap;
        font-family: 'ArialLocal', Arial, sans-serif;
        font-size: {p['font']}px; line-height: {p['line_h']}px; font-weight: 400;
        color: #000;
        background: rgba(255,255,255,{p['box_alpha']});
        border-radius: {p['radius']}px;
        padding: {p['pad_y']}px {p['pad_x']}px;
        transform-origin: center bottom;
      }}
      /* karaoke: palavra ainda nao falada fica mais apagada; "acende" no tempo da fala */
      .w {{ display: inline-block; opacity: 0.4; will-change: opacity; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0"
         data-width="{p['W']}" data-height="{p['H']}" data-duration="{dur:.3f}">
      <section id="captions" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="1">
      {cues_html}
      </section>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const CUES = {cues_json};
      CUES.forEach(function (c, i) {{
        const box = document.getElementById('box-' + i);
        const words = box.querySelectorAll('.w');
        // a frase inteira entra CENTRALIZADA (caixa com fade + leve pop), palavras apagadas
        tl.fromTo(box, {{ opacity: 0, scale: 0.94, y: 12 }},
                  {{ opacity: 1, scale: 1, y: 0, duration: 0.18, ease: 'power3.out', overwrite: 'auto' }}, c.s);
        // cada palavra "acende" (apagada -> preto cheio) no instante REAL em que e falada
        c.words.forEach(function (w, j) {{
          tl.fromTo(words[j], {{ opacity: 0.4 }},
                    {{ opacity: 1, duration: 0.14, ease: 'power1.out' }}, w.t);
        }});
        // caixa sai — termina exatamente em c.e (antes da proxima cue): zero sobreposicao
        tl.to(box, {{ opacity: 0, duration: 0.07, ease: 'power1.in', overwrite: 'auto' }}, Math.max(c.s + 0.05, c.e - 0.07));
      }});
      window.__timelines['main'] = tl;
    </script>
  </body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edl", required=True, help="caminho do edl.json do projeto")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--preset", choices=list(PRESETS), default="vertical")
    ap.add_argument("--max-chars", type=int, default=30)
    ap.add_argument("--crossfade", type=float, default=None,
                    help="override do crossfade_s do edl (use 0 p/ corte seco, ex.: transicao por zoom)")
    ap.add_argument("--box-bottom", type=int, default=None,
                    help="override da posicao (y da base da caixa); ex.: split-screen na divisoria")
    ap.add_argument("--box-alpha", type=float, default=0.5,
                    help="opacidade do fundo da caixa (0.5 padrao translucido; 1.0 branco solido)")
    args = ap.parse_args()

    p = dict(PRESETS[args.preset])
    p["box_alpha"] = args.box_alpha
    if args.box_bottom is not None:
        p["box_bottom"] = args.box_bottom
    words = words_out_timeline(Path(args.edl), crossfade=args.crossfade)
    cues = build_cues(words, args.max_chars)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "arial.ttf").exists():
        shutil.copy(ARIAL_SRC, out / "arial.ttf")
    (out / "index.html").write_text(build_html(cues, args.duration, p), encoding="utf-8")
    nwords = sum(len(c["words"]) for c in cues)
    print(f"gerado: {out / 'index.html'} ({len(cues)} cues / {nwords} palavras, "
          f"preset={args.preset}, dur={args.duration:.3f}s)")


if __name__ == "__main__":
    main()
