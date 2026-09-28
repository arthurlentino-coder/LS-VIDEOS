# split-kit — kit reusável do SPLIT (padrão editorial MARE)

Extrai o sistema do split (metade de baixo) num kit dirigido por config, do mesmo jeito que o `faceless-kit`. Em vez de reescrever CSS+engine+ilustrações a cada vídeo, edita-se só um array `SCENES[]`.

## Arquivos
- `kit.css` — design system (disco, atmo/grid/grão, kick/headline/sub, statline, footer, sparks). NÃO editar por vídeo.
- `kit.js` — engine (`SplitKit.build`) + **biblioteca de ilustrações** (`ILLOS`) com a animação-assinatura de cada uma. NÃO editar por vídeo (só p/ ADICIONAR ilustração nova ao acervo).
- `index.template.html` — starter: copiar → `projects/<X>/edit/hf/split/public/index.html` e editar só o `SCENES[]` + as duas `data-duration`.
- `fonts/`, `vendor/gsap.min.js` — assets prontos.

## Uso (novo split)
1. `cp -r _scaffolds/split-kit/* projects/<X>/edit/hf/split/public/` e **`mv index.template.html index.html`** (renomear, NÃO deixar os dois — senão o lint acusa `multiple_root_compositions`). Substituir o `top.mp4` de exemplo pelo facecrop real do topo do projeto.
   > Nota: `hf.ps1 lint` acusa `missing_timeline_registry` (falso positivo — o `window.__timelines.split` é setado em runtime pelo `kit.js` externo, não inline; o render funciona). Ignorar.
2. Abrir `index.html`, setar as **duas `data-duration`** = duração REAL da `base_zoom_seam.mp4` (`ffprobe`, NÃO o `total_duration_s` do edl — ele fica velho).
3. Preencher `SCENES[]`: uma cena por beat da fala (reusar os `start`/`dur` do split antigo do projeto, se houver). `layout` alterna default/reverse; `stack` p/ abertura, hero e fecho. `accent` muda por seção narrativa. `headline` usa `**palavra**` p/ destacar.
4. Validar SEM render cheio: `hf.ps1 snapshot --at <t>` (SVG puro renderiza no snapshot). Conferir hero + cenas de risco.
5. Render: `hf.ps1 render --low-memory-mode -o .../hf/split_motion.mp4`.
6. Fechar: `finish_split.py <projeto>` (mux base + legenda divisória `subs-divider.webm` + SFX `sfx.json` + loudnorm → `output/<lote>/<nome>_split.mp4`).

## Campos da cena
`{ start, dur, layout, accent, halo?, kick, headline, sub?, art:{type, ...} }`

## Acervo de ilustrações (`art.type`)
| type | o que é | params |
|---|---|---|
| `seal` | medalha/selo com rótulo | `label` (ex.: "CPRO-R","CPA") |
| `exam` | folha de prova com 3 checks | — |
| `download` | seta de download + tag | `label?` (ex.: "GRÁTIS") |
| `chat` | balão de mensagem (WhatsApp/ajuda) | — |
| `button` | botão + cursor tocando | `label` (texto do botão) |
| `refresh` | seta circular (atualizada) | — |
| `target` | alvo + flecha cravando | `arrow?` (cor da flecha) |
| `gradcap` | capelo de formatura + borla | — |
| `shield` | escudo + check (garantia/sem pegadinha) | — |
| `lupa` | documento + lupa (de verdade) | — |
| `gift` | presente com laço (grátis/entrega) | — |
| `bars` | 3 barras subindo (carreira) | `arrow?` (cor da seta) |
| `question` | "?" grande | — |
| `person` | pessoa (+ anel de destaque) | `ring?` (cor do anel) |
| `price0` | "R$0" riscado | — |
| `cue` | taco+bola de sinuca + burst (assinatura) | — |
| `num` | count-up numérico | `to`, `prefix?`, `suffix?` |
| `arms` | braços abertos + coração (abraço) | — |
| `star` | estrela (referência/destaque) | — |

## Regras herdadas (padrão atual)
- **Legenda karaokê vai na DIVISÓRIA** por cima (não é do kit): `subs-divider.webm` sobreposto no finisher (box sólido, ~y915-1035, acima do conteúdo editorial). O texto editorial (kick+headline) NÃO substitui a legenda neste fluxo.
- Cor/acento muda por seção narrativa; hero e fecho em `stack`.
- Render HyperFrames SEMPRE com `--low-memory-mode` (disco).
- Ilustração nova: adicionar em `ILLOS` (par `svg(a,u,o)` + `sig(tl,g,q,u,at,o)`), ids com `data-k` namespaced por cena; validar por snapshot.

Ver [[mesa-de-corte-console]] e a memória do lote CPRO-R p/ o histórico do padrão.
