#!/usr/bin/env python3
"""fix_transcript.py — corrige erros recorrentes do Scribe no transcript (lote-aware).

O Scribe erra sempre os mesmos nomes de certificação (CPRO-I→"CPOR", CPRO-R→"CPROR/CPRA-R/CPR",
ANBIMA→"AMBIMA"…) e às vezes datas. Isto automatiza as correções conhecidas com PREVIEW.

Corrige os TOKENS em words[] (as cues/legendas vêm daí) e regenera o campo `text`.
- `--cert <CPRO-I|CPRO-R|CFP|CPA|ANBIMA>`: mapeia os garbles conhecidos daquela família → o token certo.
- `--rules <extra.json>`: regras custom por vídeo/lote: {"regex (token inteiro, i)": "troca"} — ex. datas.
- Sem `--apply` = DRY-RUN (só mostra o diff). Com `--apply` grava (backup .bak).

Uso:
  py fix_transcript.py --file "projects/CPRO_I_1/edit/transcripts/..json" --cert CPRO-I
  py fix_transcript.py --file ... --cert CFP --rules fixes.json --apply
"""
import argparse, json, re, shutil
from pathlib import Path

# garbles conhecidos por família (fullmatch no "core" do token, sem pontuação, case-insensitive)
GARBLES = {
    "CPRO-I": [r"cpor", r"c[\-\s]?pro[\-\s]?i", r"dc[\-\s]?pro[\-\s]?i", r"cproi"],
    "CPRO-R": [r"cproro?", r"cpra[\-\s]?r", r"cpr", r"c[\-\s]?pro[\-\s]?re", r"cprore", r"dc[\-\s]?pro[\-\s]?r", r"cpror"],
    "CFP":    [r"cfp", r"c\.?f\.?p\.?"],
    "CPA":    [r"cpa"],
    "ANBIMA": [r"ambima", r"ambina", r"anbyma", r"ambi+ma"],
}
CORE = re.compile(r"^(\W*)(.*?)(\W*)$", re.S)   # (pontuação-pré, core, pontuação-pós)

def fix_token(tok, cert, extra):
    pre, core, post = CORE.match(tok).groups()
    # 1) regras custom (token inteiro)
    for rx, repl in extra.items():
        if re.fullmatch(rx, tok, re.I):
            return repl
    # 2) cert garbles no core
    if cert and core:
        for rx in GARBLES.get(cert, []):
            if re.fullmatch(rx, core, re.I):
                if core == cert:   # já certo (só caixa) — evita ruído no diff
                    return tok
                return pre + cert + post
    return tok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--cert", default=None, choices=list(GARBLES.keys()))
    ap.add_argument("--rules", default=None, help="json {regex: troca} p/ correções custom")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p = Path(a.file)
    d = json.loads(p.read_text(encoding="utf-8"))
    extra = json.loads(Path(a.rules).read_text(encoding="utf-8")) if a.rules else {}

    changes = []
    for w in d.get("words", []):
        if w.get("type") != "word":
            continue
        old = w["text"]; new = fix_token(old, a.cert, extra)
        if new != old:
            changes.append((old, new)); w["text"] = new
    d["text"] = "".join(w["text"] for w in d.get("words", []))

    print(f"=== fix_transcript {p.name} (cert={a.cert}, {len(changes)} troca(s)) ===")
    for old, new in changes:
        print(f"  '{old}' -> '{new}'")
    if not changes:
        print("  (nada a corrigir)")
    if a.apply and changes:
        shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        print(f"  gravado (backup em {p.name}.bak)")
    elif changes:
        print("  DRY-RUN — rode com --apply p/ gravar")

if __name__ == "__main__":
    main()
