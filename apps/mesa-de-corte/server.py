#!/usr/bin/env python3
"""Mesa de Corte — servidor local do console de edicao.

Serve o index.html, lista as pastas reais de VIDEOS/input/, recebe a ordem do
console e mantem uma fila com status/aprovacao (1 por vez). O motor de edicao
em si e o Claude Code: este servidor e o cockpit (pasta -> config -> fila).

Rodar:  python server.py   ->  http://localhost:8756
"""
from __future__ import annotations

import base64
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
PORT = 8756
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

    def do_GET(self):
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
                fila = o.get("fila", [])
                cnt = {}
                for it in fila:
                    s = it.get("status", "pendente")
                    cnt[s] = cnt.get(s, 0) + 1
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
                    "estilo": cfg.get("estilo"),
                    "formatos": o.get("formatos") or cfg.get("formatos") or [],
                    "active": o.get("lote") == active,
                })
            self._send(200, {"orders": out})
        elif u.path == "/api/status":
            f = order_path(q.get("lote", [""])[0])
            if f.exists():
                order = json.loads(f.read_text("utf-8-sig"))
                for item in order.get("fila", []):
                    item["previews"] = [fmt for fmt in item.get("formatos", ["normal"]) if media_path(item, fmt)]
                self._send(200, order)
            else:
                self._send(404, {"error": "sem ordem"})
        elif u.path == "/api/media":
            self.serve_media(q.get("lote", [""])[0], q.get("item", [""])[0], q.get("fmt", ["normal"])[0])
        elif u.path == "/api/mediathumb":
            self.serve_media_thumb(q.get("lote", [""])[0], q.get("item", [""])[0], q.get("fmt", ["normal"])[0])
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

    def _stream_file(self, p):
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
            hit = next((it for it in o["fila"] if it["id"] == body.get("item")), None)
            if not hit:
                return self._send(404, {"error": "item nao encontrado"})
            if hit["status"] == "aprovado":
                return self._send(200, {"ok": True})
            if hit["status"] != "revisar":
                return self._send(409, {"error": "item ainda nao esta em revisao"})
            hit["status"] = "aprovado"
            nxt = None if any(it["status"] == "em_edicao" for it in o["fila"]) else next((it for it in o["fila"] if it["status"] == "pendente"), None)
            if nxt:
                nxt["status"] = "em_edicao"
            f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")
            done = all(it["status"] == "aprovado" for it in o["fila"])
            emit_event(f"APPROVE lote={body.get('lote')} aprovado={body.get('item')} "
                       + (f"proximo={nxt['id']}" if nxt else ("lote_completo" if done else "sem_proximo")))
            self._send(200, {"ok": True})
        elif u.path == "/api/reject":
            f = order_path(body.get("lote", ""))
            if not f.exists():
                return self._send(404, {"error": "sem ordem"})
            o = json.loads(f.read_text("utf-8-sig"))
            nota = (body.get("nota", "") or "").strip()
            hit = next((it for it in o["fila"] if it["id"] == body.get("item")), None)
            if not hit:
                return self._send(404, {"error": "item nao encontrado"})
            fmt, tempo = body.get("formato"), body.get("tempo")
            if fmt is not None and fmt not in hit.get("formatos", []):
                return self._send(400, {"error": "formato nao pertence ao item"})
            if tempo is not None and (type(tempo) not in (int, float) or not math.isfinite(tempo) or tempo < 0):
                return self._send(400, {"error": "tempo invalido"})
            busy = any(it is not hit and it["status"] == "em_edicao" for it in o["fila"])
            hit["status"] = "pendente" if busy else "em_edicao"
            hit["nota_ajuste"] = nota
            hit["formato"] = fmt
            hit["tempo"] = tempo
            f.write_text(json.dumps(o, ensure_ascii=False, indent=2), "utf-8")
            emit_event(f"AJUSTE lote={body.get('lote')} item={body.get('item')} status={hit['status']} formato={fmt} tempo={tempo} nota={nota or '(sem nota)'}")
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})


if __name__ == "__main__":
    print(f"Mesa de Corte - servidor local: http://localhost:{PORT}")
    print(f"input/: {INPUT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

