#!/usr/bin/env python3
"""setowner.py — define o DONO de um lote (quem vai vê-lo no console).

No multi-tenant, cada lote tem owner; 'user' só vê/mexe nos lotes cujo owner é ele
(admin vê todos). Como o operador costuma CRIAR o lote, use isto p/ atribuí-lo ao cliente.

Uso:
  py setowner.py <lote> <usuario>     # define owner
  py setowner.py <lote> --clear       # remove owner (volta a só-admin)
  py setowner.py --list               # lista lotes e donos
"""
import argparse, json, sys
from pathlib import Path

ORDERS = Path(__file__).resolve().parent / "orders"

def users():
    f = ORDERS / "_users.json"
    try: return set((json.loads(f.read_text("utf-8")) or {}).get("users", {}).keys())
    except Exception: return set()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lote", nargs="?")
    ap.add_argument("usuario", nargs="?")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or not a.lote:
        for p in sorted(ORDERS.glob("*.json")):
            if p.name.startswith("_"): continue
            try: o = json.loads(p.read_text("utf-8-sig"))
            except Exception: continue
            print(f"  {o.get('lote', p.stem):20s} dono: {o.get('owner') or '(sem dono / só-admin)'}")
        if not a.list: print("\nUso: py setowner.py <lote> <usuario>  |  --clear  |  --list")
        return

    f = ORDERS / f"{a.lote}.json"
    if not f.exists():
        print("sem lote:", a.lote); return
    o = json.loads(f.read_text("utf-8-sig"))
    if a.clear:
        o.pop("owner", None); print(f"'{a.lote}': dono removido (só-admin)")
    else:
        if not a.usuario:
            print("informe o usuário (ou --clear)"); return
        us = users()
        if us and a.usuario not in us:
            print(f"AVISO: usuário '{a.usuario}' não existe em _users.json (rode useradd.py). Setando mesmo assim.")
        o["owner"] = a.usuario
        print(f"'{a.lote}': dono = {a.usuario}")
    f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")

if __name__ == "__main__":
    main()
