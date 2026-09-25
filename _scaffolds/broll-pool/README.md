# Pool de b-roll (com tags)

Acervo central de b-roll pro faceless escolher por **tema de cena**, em vez de hardcodar clipes.

- `clips/` — os vídeos (**31 clipes**; os 23 novos são Pexels 9:16 nativo 1080×1920 25fps sem áudio, os 4 originais 9:16 nativo + 4 landscape → **reframe 9:16 no uso**).
- `broll.json` — manifesto: cada clipe com `tags`, `desc`, `cat`, `orient`, dims, `dur` e `source` (nos novos). Categorias: Carreira e estudo, Mercado financeiro, Consultoria, Dados e gráficos, App e digital, Trabalho, **Dinheiro**, **Fechamento**, **Celular e app**, **Cidade e prédio**, **Formatura e aprovação**.
- `pick_broll.py` — escolhe por tags.
- `gen_gallery.py` — regenera `index.html` (galeria estática agrupada por categoria + busca) a partir do `broll.json`. Rodar após adicionar/remover clipes. Servida em `/lib/broll/` pelo server do app; o app tem também a view nativa (`/api/broll`).

## Uso
```bash
py pick_broll.py carreira problema estudo      # melhor clipe (caminho absoluto)
py pick_broll.py --top 3 dados trading         # 3 melhores com score
py pick_broll.py --json sucesso mercado        # {file,score,orient,w,h,desc} do melhor
py pick_broll.py --list                        # lista tudo
```

Score = nº de tags casadas (empate → clipe mais curto, mais versátil).

## No faceless
Cada cena de b-roll pede as tags do seu tema (ex.: `problema/carreira` → `estudo-mesa`,
`solução/sucesso` → `mercado-dados`). Se o clipe for `landscape`, aplicar crop/scale 9:16
antes de compor (o clip vai sob a `.grade` escura + lower-third).

## Adicionar clipe
Colocar o `.mp4` em `clips/` (padrão do pool: 1080×1920 25fps h264 sem áudio) + uma entrada em `broll.json` com `cat`/tags/`orient`/`dur`/`desc`, gerar o thumb (`clips/<n>.thumb.jpg`, 360×640) e rodar `py gen_gallery.py`. Fonte grátis usada: Pexels (`pexels.com/download/video/<id>/` devolve UHD → transcodar p/ 1080×1920 e apagar o UHD).
