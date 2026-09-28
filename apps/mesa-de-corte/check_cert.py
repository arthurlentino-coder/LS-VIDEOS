#!/usr/bin/env python3
"""check_cert.py — GUARD anti-erro de certificacao no motion.

Cruza a certificacao ESPERADA do criativo com todo rotulo/headline/eyebrow/chip/sub
escrito nos HTML de motion (split/hybrid/faceless) e barra divergencia de FAMILIA
(ex.: escreveu 'CPA' num video que e 'CPRO-I').

CLI:
  py check_cert.py --edit projects/CPROI_3/edit             # infere cert do note do edl.json
  py check_cert.py --edit projects/CPROI_3/edit --cert CPRO-I
  py check_cert.py --edit projects/CPROI_3/edit --file hf/split/public/index.html

Importavel (usado como GATE em finish_split / compose_hfsubs / finish_faceless):
  import check_cert
  check_cert.gate(edit_dir, files=[...])   # levanta SystemExit se divergir (bypass: env SKIP_CERT=1)

Familias: CPA (CPA/CPA-10/CPA-20), CPRO-I, CPRO-R, CFP, ANBIMA, CEA, CGA.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CERT_PATTERNS = [
    (re.compile(r"CPA[\s\-]?20", re.I), "CPA"),
    (re.compile(r"CPA[\s\-]?10", re.I), "CPA"),
    (re.compile(r"CPRO[\s\-]?I\b", re.I), "CPRO-I"),
    (re.compile(r"CPRO[\s\-]?R\b", re.I), "CPRO-R"),
    (re.compile(r"\bCPA\b", re.I), "CPA"),
    (re.compile(r"\bCFP\b", re.I), "CFP"),
    (re.compile(r"\bANBIMA\b", re.I), "ANBIMA"),
    (re.compile(r"\bCEA\b", re.I), "CEA"),
    (re.compile(r"\bCGA\b", re.I), "CGA"),
]

def family_of(text: str):
    for rx, fam in CERT_PATTERNS:
        if text and rx.search(text):
            return fam
    return None

TEXT_RX = re.compile(
    r"(?:headline|kick|sub|label)\s*:\s*'([^']*)'"
    r"|>([^<>{}]*?)</(?:div|span|text|b)>"
    r"|class=\"(?:eyebrow|kick|sub|head|apoio|chip)\"[^>]*>([^<]*)"
)

def _scan_file(p: Path, expected_fam: str):
    issues = []
    try:
        lines = p.read_text("utf-8", errors="replace").splitlines()
    except Exception:
        return issues
    for i, ln in enumerate(lines, 1):
        low = ln.lstrip()
        if low.startswith("<!--") or low.startswith("//") or low.startswith("*"):
            continue
        for m in TEXT_RX.finditer(ln):
            frag = next((g for g in m.groups() if g), "")
            fam = family_of(frag)
            if fam and fam != expected_fam:
                issues.append((str(p), i, fam, frag.strip()[:60]))
    return issues

def expected_from_edl(edit: Path):
    edl = edit / "edl.json"
    if edl.exists():
        note = (json.loads(edl.read_text("utf-8-sig")).get("note_orientacao") or "")
        return family_of(note)
    return None

def motion_files(edit: Path):
    out = []
    for sub in ("hf/split/public/index.html", "hf/hybrid/public/index.html"):
        pp = edit / sub
        if pp.exists():
            out.append(pp)
    fr = edit / "hf" / "faceless" / "compositions" / "frames"
    if fr.is_dir():
        out += sorted(fr.glob("*.html"))
    return out

def run_check(edit, cert=None, only_files=None):
    """Retorna (expected_family, [ (file, line, found_fam, frag), ... ])."""
    edit = Path(edit)
    expected = family_of(cert) or cert or expected_from_edl(edit)
    if not expected:
        return (None, [])
    files = [Path(f) if Path(f).is_absolute() else (edit / f) for f in only_files] if only_files else motion_files(edit)
    issues = []
    for p in files:
        if p.exists():
            issues += _scan_file(p, expected)
    return (expected, issues)

def gate(edit, files=None, cert=None, label="motion"):
    """GATE p/ o fluxo: imprime e ABORTA (SystemExit) se divergir. Bypass: env SKIP_CERT=1."""
    if os.environ.get("SKIP_CERT") == "1":
        print(f"[check_cert] SKIP_CERT=1 — gate de certificacao pulado ({label}).")
        return
    # fail-closed: arquivo de motion pedido e ausente/ilegivel = gate nao checou nada -> aborta
    if files is not None:
        if not files:
            sys.exit(f"[check_cert] nenhum arquivo de motion encontrado p/ {label} — gate nao pode checar.")
        for f in files:
            p = Path(f) if Path(f).is_absolute() else Path(edit) / f
            try:
                p.read_text("utf-8", errors="replace")
            except OSError as e:
                sys.exit(f"[check_cert] arquivo de motion ausente/ilegivel ({label}): {p} ({e})")
    expected, issues = run_check(edit, cert=cert, only_files=files)
    if expected is None:
        print(f"[check_cert] cert esperada nao inferida ({label}) — gate nao aplicado.")
        return
    if not issues:
        print(f"[check_cert] ✓ {label}: certificacao '{expected}' consistente.")
        return
    print(f"[check_cert] ✗ GATE BLOQUEOU {label}: esperado '{expected}', mas o motion escreveu outra certificacao:")
    for (f, ln, fam, frag) in issues:
        try:
            rel = Path(f).relative_to(Path(edit))
        except Exception:
            rel = f
        print(f"    {rel}:{ln}  '{fam}'  → \"{frag}\"")
    sys.exit(f"[check_cert] CORRIJA a certificacao antes de finalizar (ou SKIP_CERT=1 p/ forcar).")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit", required=True)
    ap.add_argument("--cert", default=None)
    ap.add_argument("--file", action="append", default=None, help="checar so este(s) arquivo(s) (relativo ao edit)")
    a = ap.parse_args()
    expected, issues = run_check(a.edit, cert=a.cert, only_files=a.file)
    if expected is None:
        sys.exit("nao consegui inferir a certificacao esperada; passe --cert")
    print(f"check_cert: esperado = {expected}")
    for (f, ln, fam, frag) in issues:
        try: rel = Path(f).relative_to(Path(a.edit))
        except Exception: rel = f
        print(f"  ✗ {rel}:{ln}  escreveu '{fam}' (esperado {expected})  → \"{frag}\"")
    if not issues:
        print("  ✓ nenhuma divergencia de certificacao")
        return 0
    print(f"\nRESULTADO: {len(issues)} divergencia(s) — CORRIGIR antes de renderizar.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
