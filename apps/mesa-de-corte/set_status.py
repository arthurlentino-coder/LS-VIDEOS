#!/usr/bin/env python3
"""Atualiza o status de um item da fila do pedido (progresso ao vivo no app).
Uso: py set_status.py <lote> <item_id> <pendente|em_edicao|revisar|aprovado> [saida_path] [--fmt <formato>]
     py set_status.py <lote> <item_id> etapa "<texto do passo>"   # progresso ao vivo (não muda status)
     py set_status.py <lote> __next__            # marca 1o pendente como em_edicao
Com --fmt: muda o status SÓ daquele formato (item.fmts) e deriva o status do item.
"""
import json, sys
from pathlib import Path
ORDERS = Path(__file__).resolve().parent / "orders"
VALID = {"pendente","em_edicao","revisar","aprovado"}

def ensure_fmts(item):
    fmts = item.get("formatos") or ["normal"]
    cur = item.get("fmts") if isinstance(item.get("fmts"), dict) else {}
    base = item.get("status","pendente")
    for f in fmts: cur.setdefault(f, base)
    item["fmts"] = {f: cur[f] for f in fmts if f in cur}
    return item["fmts"]

def rollup(item):
    vals = list((item.get("fmts") or {}).values())
    if not vals: return item.get("status","pendente")
    if all(v=="aprovado" for v in vals): return "aprovado"
    if any(v=="em_edicao" for v in vals): return "em_edicao"
    if any(v=="revisar" for v in vals): return "revisar"
    return "pendente"

def main():
    argv = sys.argv[1:]
    fmt = None
    if "--fmt" in argv:
        i = argv.index("--fmt"); fmt = argv[i+1]; del argv[i:i+2]
    if len(argv) < 2: print(__doc__); return
    lote, item = argv[0], argv[1]
    f = ORDERS / f"{lote}.json"
    if not f.exists(): print("sem pedido:", lote); return
    o = json.loads(f.read_text("utf-8"))
    if item == "__next__":
        nxt = next((it for it in o["fila"] if it["status"]=="pendente"), None)
        if nxt: nxt["status"]="em_edicao"; print("editando:", nxt["id"])
    else:
        status = argv[2] if len(argv)>2 else "aprovado"
        hit = next((it for it in o["fila"] if it["id"]==item), None)
        if not hit: print("item não encontrado:", item); return
        if status == "etapa":
            hit["etapa"] = argv[3] if len(argv)>3 else ""
            print(f"{item} etapa: {hit.get('etapa','')}")
        elif status not in VALID:
            print("status inválido:", status); return
        elif fmt:                                   # per-formato
            fmts = ensure_fmts(hit)
            if fmt not in fmts: print("formato não pertence ao item:", fmt); return
            fmts[fmt] = status
            hit["status"] = rollup(hit)
            if len(argv)>3: hit["saida"]=argv[3]
            hit.pop("etapa", None)
            print(f"{item}[{fmt}] -> {status}  (item: {hit['status']})")
        else:                                       # item inteiro
            hit["status"]=status
            ensure_fmts(hit)
            for k in hit["fmts"]: hit["fmts"][k]=status   # mantém fmts coerente
            if status in ("revisar","aprovado","pendente"): hit.pop("etapa", None)
            if len(argv)>3: hit["saida"]=argv[3]
            print(f"{item} -> {status}")
    f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")

if __name__=="__main__": main()
