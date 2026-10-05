#!/usr/bin/env python3
"""useradd.py — cria/atualiza uma conta do console (orders/_users.json).

Com pelo menos 1 usuário cadastrado (ou MESA_TOKEN setado), o console passa a exigir
login (Basic Auth). Cada lote fica com dono (owner) = quem criou; 'admin' vê todos.

Uso:
  py useradd.py <usuario> <senha> [--role admin|user]
  py useradd.py --list
Senha é hasheada (pbkdf2-sha256); o arquivo _users.json fica em orders/ (fora do git).
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

ORDERS = Path(__file__).resolve().parent / "orders"
F = ORDERS / "_users.json"

def load():
    if F.exists():
        try: return json.loads(F.read_text("utf-8")) or {"users": {}}
        except Exception: pass
    return {"users": {}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("usuario", nargs="?")
    ap.add_argument("senha", nargs="?")
    ap.add_argument("--role", default="user", choices=["admin", "user"])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    data = load()
    if a.list or not (a.usuario and a.senha):
        us = data.get("users", {})
        if not us: print("(nenhum usuário — modo aberto, sem login)")
        for u, v in us.items(): print(f"  {u}  [{v.get('role','user')}]")
        if not a.list: print("\nUso: py useradd.py <usuario> <senha> [--role admin|user]")
        return
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", a.senha.encode("utf-8"), bytes.fromhex(salt), 120000).hex()
    ORDERS.mkdir(exist_ok=True)
    data.setdefault("users", {})[a.usuario] = {"hash": h, "salt": salt, "role": a.role}
    F.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    print(f"usuário '{a.usuario}' ({a.role}) salvo. O console agora exige login.")

if __name__ == "__main__":
    main()
