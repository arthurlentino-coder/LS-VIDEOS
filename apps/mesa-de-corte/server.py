#!/usr/bin/env python3
"""Mesa de Corte — servidor local do console de edicao.

Serve o index.html, lista as pastas reais de VIDEOS/input/, recebe a ordem do
console e mantem uma fila com status/aprovacao (1 por vez). O motor de edicao
em si e o Claude Code: este servidor e o cockpit (pasta -> config -> fila).

Rodar:  python server.py   ->  http://localhost:8756
"""
from __future__ import annotations

import base64
import hmac
import ssl
import datetime
import json
import math
import threading
import subprocess
import shutil
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # VIDEOS/apps/mesa-de-corte
# sobe até achar a pasta que contém input/ (robusto a onde o app está)
VIDEOS = next((p for p in [ROOT, *ROOT.parents] if (p / "input").is_dir()), ROOT.parent)
INPUT = VIDEOS / "input"
ORDERS = ROOT / "orders"
ORDERS.mkdir(exist_ok=True)


def emit_event(text: str) -> None:
    """Append a one-line event to orders/_events.txt so o watcher do Claude
    (tail -F) seja notificado de qualquer acao do app (start/approve/reject)."""
    try:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        with open(ORDERS / "_events.txt", "a", encoding="utf-8") as fh:
            fh.write(f"{ts}\t{text}\n")
    except Exception:
        pass


def fmt_saida(saida: str, fmt: str) -> str:
    """Deriva o caminho de um formato a partir da saida (normal): split -> <nome>_split.mp4."""
    if fmt and fmt != "normal":
        p = Path(saida)
        return str(p.with_name(p.stem + "_" + fmt + p.suffix))
    return saida
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
PORT = int(os.environ.get("MESA_PORT", "8756"))
HOST = os.environ.get("MESA_HOST", "127.0.0.1")   # 0.0.0.0 p/ expor na rede (exige MESA_TOKEN)
AUTH_TOKEN = os.environ.get("MESA_TOKEN", "")      # se definido, exige Basic Auth (senha = token) -> admin
CERT = os.environ.get("MESA_CERT", ""); KEY = os.environ.get("MESA_KEY", "")  # HTTPS opcional
import hashlib

def USERS_FILE():
    return ORDERS / "_users.json"

def load_users():
    f = USERS_FILE()
    if not f.exists():
        return {}
    try:
        return (json.loads(f.read_text("utf-8")) or {}).get("users", {})
    except Exception:
        return {}

def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), 120000).hex()

def auth_configured():
    return bool(AUTH_TOKEN) or bool(load_users())
# Serializa mutações HTTP; scripts externos ainda precisam respeitar a fila.
ORDER_LOCK = threading.Lock()
THUMB_LOCK = threading.Lock()
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def thumbnail(src, width):
    thumb = src.with_suffix(".thumb.jpg")
    with THUMB_LOCK:
        if thumb.is_file() and thumb.stat().st_size and thumb.stat().st_mtime >= src.stat().st_mtime:
            return thumb
        try:
            for at in ("0.6", "0"):
                result = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", at,
                    "-i", str(src), "-frames:v", "1", "-vf", f"scale={width}:-2", str(thumb)],
                    capture_output=True, timeout=30)
                if result.returncode == 0 and thumb.is_file() and thumb.stat().st_size:
                    return thumb
        except (OSError, subprocess.TimeoutExpired):
            pass
    return None


def safe(s: str) -> str:
    return "".join(c for c in (s or "") if c.isalnum() or c in "-_ .").strip().replace(" ", "_") or "lote"


def list_folders():
    out = []
    if INPUT.is_dir():
        for p in sorted(INPUT.iterdir()):
            if p.is_dir():
                n = sum(1 for f in p.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXT)
                if n:
                    out.append({"name": p.name, "count": n})
        loose = sum(1 for f in INPUT.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXT)
        if loose:
            out.insert(0, {"name": "(raiz de input/)", "count": loose, "root": True})
    return out


def list_files(folder: str):
    d = INPUT if folder in ("", "(raiz de input/)") else INPUT / folder
    if not d.is_dir():
        return []
    return sorted(f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXT)


def build_order(cfg: dict) -> dict:
    validate_order(cfg)
    folder = cfg.get("pasta", "")
    formats = cfg.get("formatos") or ["normal"]
    base = INPUT if folder in ("", "(raiz de input/)") else INPUT / folder
    fila = []
    client = cfg.get("fila_client")
    if client:
        # fila montada no app (formatos por vídeo + exclusões já aplicados)
        for it in client:
            if it.get("tipo") == "combo":
                seg = it.get("segmentos") or {}
                origens = {
                    role: [{"arquivo": fn, "origem": str(base / fn)} for fn in (seg.get(role) or [])]
                    for role in ("hook", "desenv", "cta")
                }
                fila.append({
                    "id": it.get("id"),
                    "tipo": "combo",
                    "segmentos": seg,
                    "origens": origens,
                    "formatos": it.get("formatos") or formats,
                    "status": "pendente",
                })
            else:
                fn = it.get("arquivo")
                item = {
                    "id": it.get("id") or Path(fn).stem,
                    "arquivo": fn,
                    "origem": str(base / fn),
                    "formatos": it.get("formatos") or formats,
                    "status": "pendente",
                }
                if it.get("trecho"):  # bruta com vários vídeos: recorte in/out
                    item["trecho"] = it["trecho"]
                fila.append(item)
    else:
        for fn in list_files(folder):
            fila.append({
                "id": Path(fn).stem,
                "arquivo": fn,
                "origem": str(base / fn),
                "formatos": formats,
                "status": "pendente",   # pendente -> em_edicao -> revisar -> aprovado
            })
    return {
        "lote": cfg.get("lote") or folder or "lote",
        "pasta": folder,
        "pasta_abs": str(base),
        "config": cfg,
        "fila": fila,
        "criado": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def validate_order(cfg):
    folder = cfg.get("pasta", "")
    if not isinstance(folder, str):
        raise ValueError("pasta invalida")
    base = (INPUT if folder in ("", "(raiz de input/)") else INPUT / folder).resolve()
    if base != INPUT.resolve() and INPUT.resolve() not in base.parents:
        raise ValueError("pasta fora de input")
    files = set(list_files(folder))
    if not files:
        raise ValueError("pasta vazia ou nao encontrada")
    def formats(value):
        if not isinstance(value, list) or not value or any(not isinstance(f, str) or not f.strip() for f in value):
            raise ValueError("escolha ao menos um formato por video")
    formats(cfg.get("formatos", ["normal"]))
    if "fila_client" not in cfg:  # compatibilidade com pedidos antigos
        return
    items = cfg["fila_client"]
    if not isinstance(items, list) or not items:
        raise ValueError("selecione ao menos um video")
    ids = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("item invalido")
        formats(item.get("formatos", cfg.get("formatos", ["normal"])))
        if item.get("tipo") == "combo":
            segments = item.get("segmentos")
            if not isinstance(segments, dict):
                raise ValueError("segmentos invalidos")
            sources = []
            for role in ("hook", "desenv", "cta"):
                group = segments.get(role)
                if not isinstance(group, list) or not group:
                    raise ValueError("combo precisa de gancho, corpo e CTA")
                sources.extend(group)
        else:
            sources = [item.get("arquivo")]
        if any(not isinstance(fn, str) or fn not in files for fn in sources):
            raise ValueError("arquivo inexistente na pasta selecionada")
        identity = item.get("id") or (Path(sources[0]).stem if item.get("tipo") != "combo" else None)
        if not isinstance(identity, str) or not identity.strip() or identity in ids:
            raise ValueError("identificador vazio ou duplicado")
        ids.add(identity)
        if "trecho" in item:
            span = item["trecho"]
            if not isinstance(span, dict):
                raise ValueError("trecho invalido")
            start, end = span.get("start"), span.get("end")
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in (start, end)) or start < 0 or end <= start:
                raise ValueError("trecho precisa de inicio >= 0 e fim maior que inicio")


def order_path(lote: str) -> Path:
    return ORDERS / (safe(lote) + ".json")


def media_path(item, fmt):
    saida = item.get("saida")
    if not saida:
        return None
    p = Path(fmt_saida(saida, fmt))
    if not p.is_absolute():
        p = VIDEOS / p
    p = p.resolve()
    return p if VIDEOS.resolve() in p.parents and p.is_file() else None


# ---- status POR FORMATO (compat com status do item) ----
def ensure_fmts(item):
    """Garante item['fmts'] = {formato: status}; inicializa do status do item."""
    fmts = item.get("formatos") or ["normal"]
    cur = item.get("fmts")
    if not isinstance(cur, dict):
        cur = {}
    base = item.get("status", "pendente")
    for f in fmts:
        cur.setdefault(f, base)
    # remove formatos que não pertencem mais
    item["fmts"] = {f: cur[f] for f in fmts if f in cur}
    return item["fmts"]

def rollup_status(item):
    """Deriva o status do item a partir dos formatos (aprovado só se todos; senão o 'pior')."""
    vals = list((item.get("fmts") or {}).values())
    if not vals:
        return item.get("status", "pendente")
    if all(v == "aprovado" for v in vals):
        return "aprovado"
    if any(v == "em_edicao" for v in vals):
        return "em_edicao"
    if any(v == "revisar" for v in vals):
        return "revisar"
    return "pendente"

def hist_add(item, acao, formato=None, nota=None, ajustes=None):
    h = item.setdefault("historico", [])
    h.append({
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "acao": acao, "formato": formato,
        "nota": nota, "ajustes": ajustes,
    })


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

    def _authed(self):
        # modo aberto (sem contas e sem token) = single-user admin, compat local
        self.user = None; self.role = "admin"
        if not auth_configured():
            return True
        h = self.headers.get("Authorization", "")
        if not h.startswith("Basic "):
            return False
        try:
            raw = base64.b64decode(h[6:]).decode("utf-8", "replace")
            user, pw = (raw.split(":", 1) + [""])[:2] if ":" in raw else ("", raw)
        except Exception:
            return False
        users = load_users()
        u = users.get(user)
        if u and "hash" in u and "salt" in u:
            if hmac.compare_digest(hash_pw(pw, u["salt"]), u["hash"]):
                self.user = user; self.role = u.get("role", "user"); return True
            return False
        if AUTH_TOKEN and hmac.compare_digest(pw, AUTH_TOKEN):   # token mestre = admin
            self.user = user or "admin"; self.role = "admin"; return True
        return False

    def _can(self, order):
        """dono ou admin (ou modo aberto)."""
        if self.role == "admin":
            return True
        return bool(self.user) and order.get("owner") == self.user

    def _need_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Mesa de Corte"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if not self._authed():
            return self._need_auth()
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            p = ROOT / "index.html"
            if p.exists():
                self._send(200, p.read_bytes(), "text/html")
            else:
                self._send(404, b"index.html nao encontrado", "text/plain")
        elif u.path == "/lib/anim" or u.path.startswith("/lib/anim/"):
            base = (VIDEOS / "_scaffolds" / "anim-library").resolve()
            rel = u.path[len("/lib/anim"):].lstrip("/") or "index.html"
            p = (base / rel).resolve()
            if (p == base or base in p.parents) and p.exists() and p.is_file():
                self._stream_file(p)
            else:
                self._send(404, b"nao encontrado", "text/plain")
        elif u.path == "/lib/broll" or u.path.startswith("/lib/broll/"):
            base = (VIDEOS / "_scaffolds" / "broll-pool").resolve()
            rel = u.path[len("/lib/broll"):].lstrip("/") or "index.html"
            p = (base / rel).resolve()
            if (p == base or base in p.parents) and p.exists() and p.is_file():
                self._stream_file(p)
            else:
                self._send(404, b"nao encontrado", "text/plain")
        elif u.path == "/api/folders":
            self._send(200, {"folders": list_folders(), "input": str(INPUT)})
        elif u.path == "/api/files":
            self._send(200, {"files": list_files(q.get("folder", [""])[0])})
        elif u.path == "/api/broll":
            bp = VIDEOS / "_scaffolds" / "broll-pool" / "broll.json"
            if bp.exists():
                self._send(200, json.loads(bp.read_text("utf-8-sig")))
            else:
                self._send(200, {"clips": []})
        elif u.path == "/api/brollmedia":
            pool = (VIDEOS / "_scaffolds" / "broll-pool").resolve()
            p = (pool / q.get("file", [""])[0]).resolve()
            if pool in p.parents and p.exists():
                self._stream_file(p)
            else:
                self._send(404, {"error": "clipe nao encontrado"})
        elif u.path == "/api/brollthumb":
            pool = (VIDEOS / "_scaffolds" / "broll-pool").resolve()
            src = (pool / q.get("file", [""])[0]).resolve()
            if pool not in src.parents or not src.exists():
                return self._send(404, {"error": "nao encontrado"})
            thumb = thumbnail(src, 360)
            if thumb:
                self._stream_file(thumb)
            else:
                self._send(404, {"error": "thumb falhou"})
        elif u.path == "/api/orders":
            active = ""
            af = ORDERS / "_active.txt"
            if af.exists():
                active = af.read_text("utf-8").strip()
            out = []
            for f in sorted(ORDERS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    o = json.loads(f.read_text("utf-8-sig"))
                except Exception:
                    continue
                if not self._can(o):            # multi-tenant: só os próprios (admin vê todos)
                    continue
                fila = o.get("fila", [])
                cnt = {}
                ajustes_pend = 0
                for it in fila:
                    s = it.get("status", "pendente")
                    cnt[s] = cnt.get(s, 0) + 1
                    if it.get("ajustes"):                 # item com ajuste em aberto
                        ajustes_pend += 1
                cfg = o.get("config") or {}
                out.append({
                    "lote": o.get("lote"),
                    "projeto": cfg.get("projeto") or o.get("lote"),
                    "criado": o.get("criado"),
                    "total": len(fila),
                    "aprovado": cnt.get("aprovado", 0),
                    "revisar": cnt.get("revisar", 0),
                    "em_edicao": cnt.get("em_edicao", 0),
                    "pendente": cnt.get("pendente", 0),
                    "ajustes": ajustes_pend,
                    "estilo": cfg.get("estilo"),
                    "formatos": o.get("formatos") or cfg.get("formatos") or [],
                    "active": o.get("lote") == active,
                })
            self._send(200, {"orders": out})
        elif u.path == "/api/status":
            f = order_path(q.get("lote", [""])[0])
            if f.exists():
                order = json.loads(f.read_text("utf-8-sig"))
                if not self._can(order):
                    return self._send(403, {"error": "sem acesso a este lote"})
                for item in order.get("fila", []):
                    item["previews"] = [fmt for fmt in item.get("formatos", ["normal"]) if media_path(item, fmt)]
                    ensure_fmts(item)
                self._send(200, order)
            else:
                self._send(404, {"error": "sem ordem"})
        elif u.path in ("/api/media", "/api/mediathumb"):
            lote = q.get("lote", [""])[0]
            of = order_path(lote)
            if of.exists():
                try:
                    if not self._can(json.loads(of.read_text("utf-8-sig"))):
                        return self._send(403, {"error": "sem acesso"})
                except Exception:
                    pass
            if u.path == "/api/media":
                self.serve_media(lote, q.get("item", [""])[0], q.get("fmt", ["normal"])[0])
            else:
                self.serve_media_thumb(lote, q.get("item", [""])[0], q.get("fmt", ["normal"])[0])
        elif u.path == "/api/download":
            lote = q.get("lote", [""])[0]; item = q.get("item", [""])[0]; fmt = q.get("fmt", ["normal"])[0]
            of = order_path(lote)
            if not of.exists():
                return self._send(404, {"error": "sem ordem"})
            order = json.loads(of.read_text("utf-8-sig"))
            if not self._can(order):
                return self._send(403, {"error": "sem acesso"})
            entry = next((it for it in order.get("fila", []) if it["id"] == item), None)
            if not entry:
                return self._send(404, {"error": "item nao encontrado"})
            # não-admin só baixa formato APROVADO (entrega liberada)
            if self.role != "admin":
                ensure_fmts(entry)
                if entry["fmts"].get(fmt) != "aprovado":
                    return self._send(403, {"error": "formato ainda nao aprovado"})
            p = media_path(entry, fmt)
            if not p:
                return self._send(404, {"error": "arquivo nao encontrado"})
            proj = (order.get("config") or {}).get("projeto") or lote or "video"
            suf = "" if fmt == "normal" else "_" + fmt
            name = safe(f"{proj}_{item}{suf}") + p.suffix
            self._stream_file(p, download_name=name)
        elif u.path == "/api/rawmedia":
            self.serve_raw(q.get("folder", [""])[0], q.get("file", [""])[0])
        else:
            self._send(404, {"error": "not found"})

    def serve_raw(self, folder, file):
        base = INPUT if folder in ("", "(raiz de input/)") else INPUT / folder
        p = (base / file).resolve()
        if INPUT not in p.parents or not p.exists():
            return self._send(404, {"error": "clipe nao encontrado"})
        self._stream_file(p)

    def serve_media(self, lote, item, fmt="normal"):
        f = order_path(lote)
        if not f.exists():
            return self._send(404, {"error": "sem ordem"})
        order = json.loads(f.read_text("utf-8-sig"))
        entry = next((it for it in order["fila"] if it["id"] == item), {})
        p = media_path(entry, fmt)
        if not p:
            return self._send(404, {"error": "arquivo nao encontrado"})
        self._stream_file(p)

    def serve_media_thumb(self, lote, item, fmt="normal"):
        f = order_path(lote)
        if not f.exists():
            return self._send(404, {"error": "sem ordem"})
        order = json.loads(f.read_text("utf-8-sig"))
        entry = next((it for it in order["fila"] if it["id"] == item), {})
        p = media_path(entry, fmt)
        if not p:
            return self._send(404, {"error": "arquivo nao encontrado"})
        thumb = thumbnail(p, 240)
        if thumb:
            self._stream_file(thumb)
        else:
            self._send(404, {"error": "thumb falhou"})

    def _stream_file(self, p, download_name=None):
        size = p.stat().st_size
        ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            if a:
                start = int(a)
            if b:
                end = int(b)
            end = min(end, size - 1)
        length = end - start + 1
        self.send_response(206 if rng else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.end_headers()
        with open(p, "rb") as fh:
            fh.seek(start)
            remaining = length
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_POST(self):
        if not self._authed():
            return self._need_auth()
        with ORDER_LOCK:
            self._post()

    def _post(self):
        u = urllib.parse.urlparse(self.path)
        ln = int(self.headers.get("Content-Length", "0") or "0")
        try:
            body = json.loads(self.rfile.read(ln) or b"{}")
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"error": "JSON invalido"})
        if not isinstance(body, dict):
            return self._send(400, {"error": "pedido deve ser um objeto"})
        if u.path == "/api/start":
            try:
                order = build_order(body)
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            if self.user:
                order["owner"] = self.user       # multi-tenant: dono do lote
            if order["fila"]:
                order["fila"][0]["status"] = "em_edicao"
            order_path(order["lote"]).write_text(json.dumps(order, ensure_ascii=False, indent=2), "utf-8")
            (ORDERS / "_active.txt").write_text(order["lote"], "utf-8")
            # sinal p/ o watcher do Claude iniciar a edicao automaticamente
            (ORDERS / "_signal.txt").write_text(
                f"{order['lote']}\t{order['criado']}\t{len(order['fila'])}", "utf-8")
            emit_event(f"START lote={order['lote']} itens={len(order['fila'])} "
                       f"editando={order['fila'][0]['id'] if order['fila'] else '-'}")
            self._send(200, {"ok": True, "lote": order["lote"], "count": len(order["fila"])})
        elif u.path == "/api/roteiro":
            name = os.path.basename(body.get("name", "") or "roteiro")
            b64 = body.get("b64", "") or ""
            lote = body.get("lote", "") or ""
            folder = body.get("pasta", "") or ""
            base = INPUT if folder in ("", "(raiz de input/)") else INPUT / folder
            dest_dir = base if base.exists() else ORDERS
            try:
                data = base64.b64decode(b64.split(",")[-1])
                dest = dest_dir / name
                dest.write_bytes(data)
                self._send(200, {"ok": True, "saved": str(dest), "bytes": len(data)})
            except Exception as e:
                self._send(400, {"error": str(e)})
        elif u.path == "/api/brollupload":
            pool = VIDEOS / "_scaffolds" / "broll-pool"
            clips_dir = pool / "clips"
            clips_dir.mkdir(parents=True, exist_ok=True)
            name = os.path.basename(body.get("name", "") or "broll.mp4")
            cat = (body.get("cat", "") or "Sem categoria").strip() or "Sem categoria"
            b64 = body.get("b64", "") or ""
            try:
                data = base64.b64decode(b64.split(",")[-1])
                # nome único se já existir
                dest = clips_dir / name
                stem, suf = dest.stem, dest.suffix
                i = 2
                while dest.exists():
                    dest = clips_dir / f"{stem}-{i}{suf}"
                    i += 1
                dest.write_bytes(data)
                w = h = 0
                dur = 0.0
                try:
                    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", str(dest)], capture_output=True, text=True, check=False).stdout
                    meta = json.loads(out or "{}")
                    st = (meta.get("streams") or [{}])[0]
                    w, h = int(st.get("width", 0) or 0), int(st.get("height", 0) or 0)
                    dur = round(float((meta.get("format") or {}).get("duration", 0) or 0), 1)
                except Exception:
                    pass
                rel = "clips/" + dest.name
                clip = {"file": rel, "cat": cat,
                        "orient": "portrait" if (h and w and h >= w) else "landscape",
                        "w": w, "h": h, "dur": dur, "desc": "", "tags": []}
                bp = pool / "broll.json"
                pool_data = json.loads(bp.read_text("utf-8-sig")) if bp.exists() else {"clips": []}
                pool_data.setdefault("clips", []).append(clip)
                bp.write_text(json.dumps(pool_data, ensure_ascii=False, indent=2), "utf-8")
                self._send(200, {"ok": True, "clip": clip})
            except Exception as e:
                self._send(400, {"error": str(e)})
        elif u.path == "/api/brollupdate":
            pool = VIDEOS / "_scaffolds" / "broll-pool"
            bp = pool / "broll.json"
            if not bp.exists():
                return self._send(404, {"error": "sem pool"})
            data = json.loads(bp.read_text("utf-8-sig"))
            rel = body.get("file", "")
            found = next((c for c in data.get("clips", []) if c.get("file") == rel), None)
            if not found:
                return self._send(404, {"error": "clipe nao encontrado"})
            if "cat" in body:
                found["cat"] = (body.get("cat") or "Sem categoria").strip() or "Sem categoria"
            if "desc" in body:
                found["desc"] = body.get("desc", "") or ""
            if "tags" in body:
                tags = body.get("tags") or []
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                found["tags"] = tags
            bp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            self._send(200, {"ok": True, "clip": found})
        elif u.path == "/api/brolldelete":
            pool = VIDEOS / "_scaffolds" / "broll-pool"
            bp = pool / "broll.json"
            rel = body.get("file", "")
            data = json.loads(bp.read_text("utf-8-sig")) if bp.exists() else {"clips": []}
            data["clips"] = [c for c in data.get("clips", []) if c.get("file") != rel]
            bp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            src = (pool / rel).resolve()
            if pool in src.parents and src.exists():
                trash = pool / "clips" / "_trash"
                trash.mkdir(parents=True, exist_ok=True)
                try:
                    src.rename(trash / src.name)
                except Exception:
                    pass
                th = src.with_suffix(".thumb.jpg")
                if th.exists():
                    try:
                        th.rename(trash / th.name)
                    except Exception:
                        pass
            self._send(200, {"ok": True})
        elif u.path == "/api/order_delete":
            lote = body.get("lote", "")
            f = order_path(lote)
            if not f.exists():
                return self._send(404, {"error": "sem ordem"})
            try:
                if not self._can(json.loads(f.read_text("utf-8-sig"))):
                    return self._send(403, {"error": "sem acesso a este lote"})
            except Exception:
                pass
            trash = ORDERS / "_trash"
            trash.mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            try:
                f.rename(trash / (safe(lote) + "-" + ts + ".json"))
            except Exception:
                f.unlink()
            af = ORDERS / "_active.txt"
            if af.exists() and af.read_text("utf-8").strip() == lote:
                af.unlink()
            self._send(200, {"ok": True})
        elif u.path == "/api/approve":
            f = order_path(body.get("lote", ""))
            if not f.exists():
                return self._send(404, {"error": "sem ordem"})
            o = json.loads(f.read_text("utf-8"))
            if not self._can(o):
                return self._send(403, {"error": "sem acesso a este lote"})
            hit = next((it for it in o["fila"] if it["id"] == body.get("item")), None)
            if not hit:
                return self._send(404, {"error": "item nao encontrado"})
            ensure_fmts(hit)
            fmt = body.get("formato")
            if fmt is not None and fmt not in hit["fmts"]:
                return self._send(400, {"error": "formato nao pertence ao item"})
            if fmt:                                   # aprova UM formato
                hit["fmts"][fmt] = "aprovado"
                hist_add(hit, "aprovado", formato=fmt)
            else:                                     # aprova o item inteiro
                for k in hit["fmts"]:
                    hit["fmts"][k] = "aprovado"
                hist_add(hit, "aprovado", formato="todos")
            hit["status"] = rollup_status(hit)
            hit.pop("etapa", None)
            if hit["status"] == "aprovado":
                hit.pop("ajustes", None)   # nada pendente; o histórico guarda o registro
            # só avança p/ o próximo quando o item TODO está aprovado
            nxt = None
            if hit["status"] == "aprovado" and not any(it["status"] == "em_edicao" for it in o["fila"]):
                nxt = next((it for it in o["fila"] if it["status"] == "pendente"), None)
                if nxt:
                    nxt["status"] = "em_edicao"
            f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")
            done = all(it["status"] == "aprovado" for it in o["fila"])
            emit_event(f"APPROVE lote={body.get('lote')} item={body.get('item')} formato={fmt or 'todos'} status={hit['status']} "
                       + (f"proximo={nxt['id']}" if nxt else ("lote_completo" if done else "")))
            self._send(200, {"ok": True})
        elif u.path == "/api/reject":
            f = order_path(body.get("lote", ""))
            if not f.exists():
                return self._send(404, {"error": "sem ordem"})
            o = json.loads(f.read_text("utf-8-sig"))
            if not self._can(o):
                return self._send(403, {"error": "sem acesso a este lote"})
            hit = next((it for it in o["fila"] if it["id"] == body.get("item")), None)
            if not hit:
                return self._send(404, {"error": "item nao encontrado"})
            PARTES = {"legenda", "takes", "motion", "transicao", "audio", "enquadramento", "copy", "outro"}
            formatos = hit.get("formatos", [])

            def _valida(fm, tp):
                if fm is not None and fm not in formatos:
                    return "formato nao pertence ao item"
                if tp is not None and (type(tp) not in (int, float) or not math.isfinite(tp) or tp < 0):
                    return "tempo invalido"
                return None

            ajustes_in = body.get("ajustes")
            if isinstance(ajustes_in, list) and ajustes_in:   # NOVO: lista por parte
                clean = []
                for aj in ajustes_in:
                    parte = (aj.get("parte") or "outro").lower()
                    if parte not in PARTES:
                        parte = "outro"
                    fm, tp = aj.get("formato"), aj.get("tempo")
                    err = _valida(fm, tp)
                    if err:
                        return self._send(400, {"error": err})
                    clean.append({"parte": parte, "formato": fm, "tempo": tp,
                                  "nota": (aj.get("nota", "") or "").strip()})
                hit["ajustes"] = clean

                def _lab(a):
                    t = f" @{a['tempo']:.1f}s" if a["tempo"] is not None else ""
                    fmx = f" [{a['formato']}]" if a["formato"] else ""
                    return f"{a['parte']}{fmx}{t}: {a['nota'] or '(ajustar)'}"
                hit["nota_ajuste"] = " · ".join(_lab(a) for a in clean)
                hit["formato"] = clean[0]["formato"]
                hit["tempo"] = clean[0]["tempo"]
                partes_log = ",".join(a["parte"] for a in clean)
                alvos = {a["formato"] for a in clean if a["formato"]}   # formatos citados
            else:                                             # LEGADO: nota única
                nota = (body.get("nota", "") or "").strip()
                fmt, tempo = body.get("formato"), body.get("tempo")
                err = _valida(fmt, tempo)
                if err:
                    return self._send(400, {"error": err})
                hit["nota_ajuste"] = nota
                hit["formato"] = fmt
                hit["tempo"] = tempo
                hit.pop("ajustes", None)
                partes_log = "nota-livre"
                clean = None
                alvos = {fmt} if fmt else set()

            # marca os formatos afetados p/ refação (os não-citados = item inteiro)
            ensure_fmts(hit)
            if not alvos:
                alvos = set(hit["fmts"])
            busy = any(it is not hit and it["status"] == "em_edicao" for it in o["fila"])
            novo = "pendente" if busy else "em_edicao"
            for t in alvos:
                if t in hit["fmts"]:
                    hit["fmts"][t] = novo
            hit["status"] = rollup_status(hit)
            hit.pop("etapa", None)
            hist_add(hit, "ajuste", formato=",".join(sorted(alvos)), nota=hit["nota_ajuste"], ajustes=clean)
            f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")
            emit_event(f"AJUSTE lote={body.get('lote')} item={body.get('item')} status={hit['status']} formatos={','.join(sorted(alvos))} partes={partes_log} nota={hit['nota_ajuste'] or '(sem nota)'}")
            self._send(200, {"ok": True})
        elif u.path == "/api/audio":
            f = order_path(body.get("lote", ""))
            if not f.exists():
                return self._send(404, {"error": "sem ordem"})
            a = body.get("audio") or {}
            mood = a.get("mood", "auto"); bed = a.get("bed", "medio")
            if mood not in ("auto", "calmo", "serio", "energico"):
                return self._send(400, {"error": "mood invalido"})
            if bed not in ("baixo", "medio", "alto"):
                return self._send(400, {"error": "bed invalido"})
            o = json.loads(f.read_text("utf-8-sig"))
            if not self._can(o):
                return self._send(403, {"error": "sem acesso a este lote"})
            o.setdefault("config", {})["audio"] = {"enabled": bool(a.get("enabled", True)), "mood": mood, "bed": bed}
            f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")
            emit_event(f"AUDIO lote={body.get('lote')} enabled={o['config']['audio']['enabled']} mood={mood} bed={bed}")
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})


if __name__ == "__main__":
    scheme = "https" if (CERT and KEY) else "http"
    print(f"Mesa de Corte - {scheme}://{HOST}:{PORT}  (input/: {INPUT})")
    if AUTH_TOKEN:
        print("  auth: Basic ON (senha = MESA_TOKEN)")
    elif HOST != "127.0.0.1":
        print("  AVISO: EXPOSTO sem MESA_TOKEN - defina MESA_TOKEN/contas antes de abrir na rede!")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    if CERT and KEY:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=CERT, keyfile=KEY)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()

