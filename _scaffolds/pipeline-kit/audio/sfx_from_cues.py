#!/usr/bin/env python3
"""sfx_from_cues.py — gera um sfx.json DIRIGIDO PELA COPY a partir das cues (timing por palavra).

Produz o mesmo tipo de sfx.json que a gente autorava na mão (ver CFP_1/CFP_7 split),
mas automaticamente: casa cada palavra-chave da fala com um efeito da biblioteca e
posiciona no instante REAL em que a palavra é dita.

Entradas:
  --cues  arquivo de cues: ou um cues.js (`window.__cues=[...]`) ou um JSON [{s,e,words:[{t,tx}]}].
  --edl   (opcional) edl.json do projeto — usa os cortes (ranges) p/ whoosh de transição
          e o último range p/ marcar o CTA (riser cresce até lá).
  --out   sfx.json de saída.
  --cta-at (opcional) override do instante do CTA (segundos).
  --seams (opcional) "t1,t2,..." override dos tempos de transição.

Mapa copy→efeito (pt-BR, nichos certificação/finanças). Prioridade decrescente;
dedupe por janela mínima (MIN_GAP) pra não empilhar efeito.

Uso:
  python sfx_from_cues.py --cues faceless/assets/cues.js --edl ../edl.json --out hf/split/sfx.json
"""
import argparse, json, re, unicodedata
from pathlib import Path

MIN_GAP = 0.45          # s mínimos entre 2 efeitos quaisquer
FILE_COOLDOWN = 3.2     # s mínimos p/ repetir o MESMO efeito (evita data triplicar etc.)
RISER = "whoosh-cinematic"   # 5.54s — build até o CTA
RISER_DUR = 5.54
HOOK_ZONE = 6.0         # regra de hook/pergunta só vale nos primeiros X s

def _strip(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

# (regex sobre a palavra SEM acento/minúscula, arquivo, gain, prioridade, nota)
RULES = [
    # CTA — clique/link/vem comigo/garanta
    (r"\b(clica|clique|clicar|link|botao|garant|inscre|cadastr|aqui|agora)\b", "click", 0.44, 95, "CTA"),
    (r"\b(vem|bora|vamos)\b",                                                   "click", 0.38, 80, "chamada"),
    # dinheiro / grana — brilho
    (r"(r\$|reais|mil|grana|salario|salarios|lucro|dinheiro|rico|ganha|fatur)", "sparkle", 0.42, 90, "dinheiro"),
    # número/estatística/%/data — ping (dado) / notification (data)
    (r"\b(dia|julho|agosto|setembro|horas|hoje|amanha)\b",                       "notification", 0.36, 78, "data"),
    (r"(\d|%|por\s*cento|primeiro|melhor|maior)",                               "ping", 0.38, 70, "dado"),
    # certificação / selo — slam
    (r"\b(cfp|anbima|cpa|cpro|certificac|aprovad|aprovac)\b",                   "impact-bass-1", 0.40, 88, "selo/aprovado"),
    # aspiração / virada positiva — shimmer/chime
    (r"\b(topo|chave|conquist|sucesso|autoridade|nivel|liberdade|futuro)\b",    "sparkle", 0.34, 60, "aspiracao"),
    # problema / negação / dor — tom de erro (sutil)
    (r"\b(errad|erro|perde|perder|perca|sozinho|escuro|dificil|medo)\b",        "error", 0.30, 55, "problema"),
    # pergunta / hook — pop (só na zona de hook; evita 'você' solto virar ruído)
    (r"\b(sera|quem|quer|por\s*que|porque|como)\b",                             "pop", 0.30, 40, "hook/pergunta"),
]
HOOK_ONLY = {"hook/pergunta"}  # notas que só valem dentro da HOOK_ZONE

def load_cues(path: Path):
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    m = re.search(r"__cues\s*=\s*(\[.*\])\s*;?\s*$", raw, re.S)
    if m: raw = m.group(1)
    else:
        i = raw.find("["); j = raw.rfind("]")
        if i >= 0 and j > i: raw = raw[i:j+1]
    return json.loads(raw)

def words_from_cues(cues):
    out = []
    for c in cues:
        for w in c.get("words", []):
            if "t" in w and "tx" in w:
                out.append((float(w["t"]), str(w["tx"])))
    out.sort(key=lambda x: x[0])
    return out

def pick(word):
    s = _strip(word)
    best = None
    for rx, f, g, pri, nota in RULES:
        if re.search(rx, s):
            if best is None or pri > best[3]:
                best = (f, g, pri, pri, nota)  # (file,gain,pri,pri,nota)
    if best: return best[0], best[1], best[4]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cues", required=True)
    ap.add_argument("--edl", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cta-at", type=float, default=None)
    ap.add_argument("--seams", default=None)
    a = ap.parse_args()

    cues = load_cues(Path(a.cues))
    words = words_from_cues(cues)
    dur = max((float(c.get("e", 0)) for c in cues), default=0.0)

    events = []  # (t, file, gain, nota)

    # 1) efeitos por palavra (copy)
    last_t = -9
    last_file = {}  # file -> último t (cooldown por efeito)
    for t, w in words:
        hit = pick(w)
        if not hit: continue
        f, g, nota = hit
        if nota in HOOK_ONLY and t > HOOK_ZONE: continue   # hook só no começo
        if t - last_t < MIN_GAP: continue                   # nada colado
        if t - last_file.get(f, -9) < FILE_COOLDOWN: continue  # não repetir o mesmo efeito
        events.append((round(t, 2), f, g, f"{nota}: {w}"))
        last_t = t; last_file[f] = t

    # 2) whoosh de transição nos cortes do EDL (ou --seams)
    seams = []
    cta_at = a.cta_at
    if a.seams:
        seams = [float(x) for x in a.seams.split(",") if x.strip()]
    elif a.edl and Path(a.edl).exists():
        edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
        rs = edl.get("ranges", [])
        acc = 0.0
        for i, r in enumerate(rs):
            seg = float(r["end"]) - float(r["start"])
            if i > 0: seams.append(round(acc, 2))
            acc += seg
            # CTA = início do último range (beat CTA), se não veio override
            if cta_at is None and i == len(rs) - 1:
                cta_at = round(acc - seg, 2)
    last_wh = -9
    for t in sorted(seams):
        if t - last_wh < FILE_COOLDOWN: continue            # não encostar whooshes
        if all(abs(t - e[0]) > 0.3 for e in events):         # nem colar em outro efeito
            events.append((round(t, 2), "whoosh-short", 0.30, "transicao"))
            last_wh = t

    # 3) riser crescendo até o CTA
    if cta_at is None and dur:
        cta_at = round(dur * 0.84, 2)
    if cta_at and cta_at - RISER_DUR > 0.2:
        events.append((round(cta_at - RISER_DUR, 2), RISER, 0.26, "riser -> CTA"))

    events.sort(key=lambda x: x[0])
    out = [{"t": t, "file": f, "gain": g, "nota": n} for (t, f, g, n) in events]
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sfx.json -> {a.out}  ({len(out)} efeitos, cta~{cta_at}s, dur~{dur:.1f}s)")
    for e in out: print(f"  {e['t']:6.2f}  {e['file']:16s} g={e['gain']}  {e['nota']}")

if __name__ == "__main__":
    main()
