#!/usr/bin/env python3
"""gen_gallery.py — regenera index.html (galeria estatica) a partir do broll.json.
Rodar sempre que adicionar/remover clipes:  py gen_gallery.py
Agrupa por categoria, mostra thumb + meta + tags e tem busca client-side.
Usa caminhos relativos (clips/<n>.thumb.jpg) -> abre como arquivo OU via server.
"""
import json, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "broll.json").read_text("utf-8-sig"))
clips = data["clips"]

# ordena por categoria (mantendo ordem de aparicao) e monta cards
cats = {}
for c in clips:
    cats.setdefault(c.get("cat", "Sem categoria"), []).append(c)

def card(c):
    name = html.escape(Path(c["file"]).stem)
    thumb = html.escape(Path(c["file"]).with_suffix("").as_posix() + ".thumb.jpg")
    meta = f'{html.escape(c.get("cat",""))} · {c.get("orient","")} · {c.get("dur","?")}s'
    src = c.get("source")
    badge = f'<span class="src">{html.escape(src)}</span>' if src else ""
    desc = html.escape(c.get("desc", ""))
    tags = "".join(f"<span>{html.escape(t)}</span>" for t in c.get("tags", []))
    hay = html.escape((name + " " + c.get("desc","") + " " + " ".join(c.get("tags",[])) + " " + c.get("cat","")).lower())
    return (f'<div class="card" data-h="{hay}"><div class="prev"><img src="{thumb}" alt="" loading="lazy">{badge}</div>'
            f'<div class="nm">{name}</div><div class="meta">{meta}</div>'
            f'<div class="desc">{desc}</div><div class="tg">{tags}</div>'
            f'<div class="use">clips/{name}.mp4</div></div>')

blocks = ""
for cat, items in cats.items():
    blocks += (f'<div class="grp-h" data-cat="{html.escape(cat.lower())}">{html.escape(cat)} · {len(items)}</div>'
               f'<div class="grid">{"".join(card(c) for c in items)}</div>')

n = len(clips)
htmlout = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Biblioteca de B-roll</title>
<style>
 :root{{--bg:#07131f;--panel:#0e1f2e;--line:#24384a;--ink:#eaf2f6;--mut:#8fb0c4;--cy:#22d3ee}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
 header{{padding:26px 32px 6px}} h1{{margin:0;font-size:24px}} .sub{{color:var(--mut);margin:6px 0 0}}
 main{{padding:16px 32px 60px}}
 .search{{width:100%;max-width:460px;margin:6px 0 14px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);font-size:14px}}
 .search::placeholder{{color:var(--mut)}}
 .grp-h{{font-size:13px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;color:var(--cy);margin:22px 0 10px}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px}}
 .card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:0 0 14px;overflow:hidden;display:flex;flex-direction:column;gap:8px}}
 .prev{{position:relative;aspect-ratio:9/16;max-height:280px;background:#0a1a26;overflow:hidden}}
 .prev img{{width:100%;height:100%;object-fit:cover;display:block}}
 .src{{position:absolute;top:8px;right:8px;font-size:10px;font-weight:700;background:rgba(7,19,31,.8);border:1px solid var(--line);border-radius:6px;padding:2px 7px;color:var(--mut)}}
 .nm{{font-weight:800;font-size:16px;padding:0 14px}} .meta{{color:var(--mut);font-size:12px;padding:0 14px}}
 .desc{{font-size:13px;padding:0 14px;color:#cfe0ea}}
 .tg{{display:flex;flex-wrap:wrap;gap:5px;padding:0 14px}} .tg span{{font-size:11px;color:var(--mut);background:#0a1a26;border:1px solid var(--line);border-radius:6px;padding:2px 7px}}
 .use{{font:12px/1.4 ui-monospace,Consolas,monospace;color:var(--cy);background:#0a1a26;border-radius:8px;padding:7px;margin:0 14px;white-space:pre-wrap}}
 .empty{{color:var(--mut);padding:18px 0}}
</style></head><body>
<header><h1>🎞️ Biblioteca de B-roll</h1>
<p class="sub">{n} clipes tagueados · escolha por tema com <code>pick_broll.py &lt;tag&gt;</code> · landscape precisa reframe 9:16 no uso. Gerada por <code>gen_gallery.py</code>.</p></header>
<main>
 <input id="q" class="search" type="search" placeholder="filtrar por nome, tag, categoria… (ex.: dinheiro, sucessório, aperto)">
 <div id="wrap">{blocks}</div>
 <p id="empty" class="empty" hidden>Nenhum clipe com esse filtro.</p>
</main>
<script>
 var q=document.getElementById('q'),empty=document.getElementById('empty');
 q.addEventListener('input',function(){{
   var t=q.value.trim().toLowerCase(),any=false;
   document.querySelectorAll('#wrap .grp-h').forEach(function(h){{
     var grid=h.nextElementSibling,shown=0;
     grid.querySelectorAll('.card').forEach(function(c){{
       var m=!t||c.dataset.h.indexOf(t)>-1;c.style.display=m?'':'none';if(m)shown++;
     }});
     var vis=shown>0;h.style.display=vis?'':'none';grid.style.display=vis?'':'none';if(vis)any=true;
   }});
   empty.hidden=any;
 }});
</script>
</body></html>"""

(HERE / "index.html").write_text(htmlout, encoding="utf-8")
print(f"OK -> index.html ({n} clipes, {len(cats)} categorias)")
