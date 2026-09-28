#!/usr/bin/env python3
"""guard_ciladas.py — varre uma composição HyperFrames (public/) e os scripts de
compose atrás das ciladas JÁ VIVIDAS (README §9 e §7.6). ADVISORY e ENXUTO de
propósito: só sinais de baixo falso-positivo (arquivos de composição costumam
ser minificados; heurística ampla vira ruído inútil). Sai 1 se houver ERRO de
alta confiança (drawSVG), 0 caso contrário. É SINAL, não gate — igual /impeccable.

Uso:
    py guard_ciladas.py projects/<nome>/edit/hf/split/public
    py guard_ciladas.py projects/<nome>/edit            # varre tudo abaixo
"""
import re
import sys
from pathlib import Path

JS_EXT = {".html", ".js", ".mjs"}
PY_EXT = {".py", ".ps1"}

# só padrões RAROS e de alta confiança — cada um mapeia a uma cilada documentada.
JS_CHECKS = [
    (re.compile(r"drawSVG|DrawSVGPlugin"), "erro",
     "drawSVG é plugin PREMIUM — não está no bundle GSAP do HyperFrames (§9). Remover."),
    # pivô em px num contexto SVG = a cilada exata do CPA (anel de pulso saiu do quadro).
    (re.compile(r"transformOrigin\s*:\s*['\"][^'\"]*px"), "warn",
     "transformOrigin com pivô em 'Npx Npx': em <g>/shape SVG isso joga a figura pra fora — use svgOrigin:'x y' (§9)."),
]

# compose/ffmpeg: input .webm precisa de -c:v libvpx-vp9 ANTES, senão perde o alpha.
PY_WEBM = re.compile(r"-i\b[^\n]*\.webm|['\"][^'\"]*\.webm['\"]")

def scan_js(path, text, findings):
    for i, ln in enumerate(text.splitlines(), 1):
        for rx, sev, msg in JS_CHECKS:
            if rx.search(ln):
                findings.append((sev, path, i, msg, ln.strip()[:100]))

def scan_py(path, text, findings):
    has_forced_decoder = "libvpx-vp9" in text
    for i, ln in enumerate(text.splitlines(), 1):
        if ".webm" in ln and PY_WEBM.search(ln) and not has_forced_decoder:
            findings.append(("warn", path, i,
                "usa .webm mas o script não força `-c:v libvpx-vp9` em lugar nenhum: o decoder VP9 nativo descarta o alpha → fundo preto no overlay (§9).",
                ln.strip()[:100]))

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.exists():
        print(f"caminho não existe: {root}"); return 2
    skip = {"node_modules", "vendor", ".git"}
    files = [root] if root.is_file() else [
        p for p in root.rglob("*")
        if p.suffix.lower() in JS_EXT | PY_EXT and not (skip & set(p.parts))]
    findings = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        (scan_js if p.suffix.lower() in JS_EXT else scan_py)(p, text, findings)

    if not findings:
        print(f"guard_ciladas: OK — nenhuma cilada conhecida em {root}")
        return 0

    erros = [f for f in findings if f[0] == "erro"]
    warns = [f for f in findings if f[0] == "warn"]
    for sev, path, i, msg, snippet in erros + warns:
        tag = "ERRO " if sev == "erro" else "aviso"
        try:
            rel = path.relative_to(root if root.is_dir() else root.parent)
        except ValueError:
            rel = path
        print(f"[{tag}] {rel}:{i}\n        {msg}\n        > {snippet}")
    print(f"\nguard_ciladas: {len(erros)} erro(s), {len(warns)} aviso(s). (advisory — leia e julgue)")
    return 1 if erros else 0

if __name__ == "__main__":
    sys.exit(main())
