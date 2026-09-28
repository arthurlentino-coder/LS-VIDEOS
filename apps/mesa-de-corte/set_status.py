#!/usr/bin/env python3
"""Atualiza o status de um item da fila do pedido (progresso ao vivo no app).
Uso: py set_status.py <lote> <item_id> <pendente|em_edicao|revisar|aprovado> [saida_path]
     py set_status.py <lote> __next__            # marca 1o pendente como em_edicao
"""
import json, sys
from pathlib import Path
ORDERS = Path(__file__).resolve().parent / "orders"
VALID = {"pendente","em_edicao","revisar","aprovado"}

def main():
    if len(sys.argv) < 3: print(__doc__); return
    lote, item = sys.argv[1], sys.argv[2]
    f = ORDERS / f"{lote}.json"
    if not f.exists(): print("sem pedido:", lote); return
    o = json.loads(f.read_text("utf-8"))
    if item == "__next__":
        nxt = next((it for it in o["fila"] if it["status"]=="pendente"), None)
        if nxt: nxt["status"]="em_edicao"; print("editando:", nxt["id"])
    else:
        status = sys.argv[3] if len(sys.argv)>3 else "aprovado"
        if status not in VALID: print("status inválido:", status); return
        hit = next((it for it in o["fila"] if it["id"]==item), None)
        if not hit: print("item não encontrado:", item); return
        hit["status"]=status
        if len(sys.argv)>4: hit["saida"]=sys.argv[4]
        print(f"{item} -> {status}")
    f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")

if __name__=="__main__": main()
