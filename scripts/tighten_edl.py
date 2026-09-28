"""tighten_edl.py — gera EDL 'apertado' (corta respiros) por vídeo do lote PERPETUOS.
Mantém a fala, remove silêncios > BREAK entre palavras deixando ~PAD de cada lado,
e usa crossfade curto (dissolve) em toda junção. keepspans = trechos limpos já
definidos (sem banter/gagueira/erro). Uso: tighten_edl.py <KEY> [BREAK] [PAD] [XF]
"""
import json, sys
PROJ = r"C:/Users/betat/Desktop/VIDEOS/projects"
IN = r"C:/Users/betat/Desktop/VIDEOS/input/PERPETUOS"

# trechos LIMPOS por vídeo (banter/gagueira/erro já excluídos)
KEEP = {
 "PERP_CPA_1":  [(18.80,41.61),(43.66,105.40)],
 "PERP_CPA_2":  [(4.35,87.60)],
 "PERP_CPRO_I_1":[(35.72,126.70)],
 "PERP_CPRO_I_2":[(4.42,57.00),(59.30,104.00)],
 "PERP_CPRO_R_1":[(5.75,16.30),(20.34,118.50)],
 "PERP_CPRO_R_2":[(3.30,93.30)],
 "PERP_CFP_1":  [(6.70,50.95),(55.88,81.00),(82.62,87.10)],  # +corte repetição final "eu quero te ajudar a ter"
 "PERP_CFP_2":  [(5.90,35.35),(36.75,97.90)],                # +corte repetição ~30s "e quem consegue se"
}

def words(key):
    d = json.load(open(f"{PROJ}/{key}/edit/transcripts/{key}.json", encoding="utf-8"))
    return [w for w in d["words"] if w.get("type") == "word"]

def tighten(key, BREAK=0.45, PAD=0.14):
    ws = words(key); ranges = []
    for (a, b) in KEEP[key]:
        seg = [w for w in ws if w["start"] >= a-0.001 and w["end"] <= b+0.001]
        if not seg: continue
        cur = max(a, seg[0]["start"]-PAD); prev = seg[0]["end"]
        for w in seg[1:]:
            if w["start"]-prev > BREAK:
                ranges.append((round(cur,2), round(prev+PAD,2)))
                cur = w["start"]-PAD
            prev = w["end"]
        ranges.append((round(cur,2), round(min(b, prev+PAD),2)))
    return ranges

def main():
    key = sys.argv[1]
    BREAK = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    PAD = float(sys.argv[3]) if len(sys.argv) > 3 else 0.14
    XF = float(sys.argv[4]) if len(sys.argv) > 4 else 0.09
    r = tighten(key, BREAK, PAD)
    edl = {"version": 1,
           "sources": {key: f"{PROJ}/{key}/edit/upright.mp4"},
           "source_original": f"{IN}/{key}.MP4",
           "ranges": [{"source": key, "start": a, "end": b} for a, b in r],
           "crossfade_s": XF, "grade": None,
           "note": f"apertado BREAK={BREAK} PAD={PAD} xfade={XF}; respiros cortados"}
    out = f"{PROJ}/{key}/edit/edl.json"
    open(out, "w", encoding="utf-8").write(json.dumps(edl, indent=2, ensure_ascii=False))
    tot = sum(b-a for a, b in r)
    print(f"{key}: {len(r)} ranges, {tot:.1f}s (xfade {XF}s -> ~{tot-(len(r)-1)*XF:.1f}s) -> {out}")

if __name__ == "__main__":
    main()
