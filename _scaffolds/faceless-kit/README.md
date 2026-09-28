# faceless-kit — biblioteca reusável de blocos faceless

Engine dirigida por **config** pro faceless data-viz (padrão navy). Em vez de reescrever HTML+timeline
por lote, você edita uma lista `SCENES[]` (tipo de cena + tempos + conteúdo) e a engine renderiza e anima.

## Arquivos
- `kit.css` — design system completo (todos os blueprints).
- `kit.js` — engine: `FacelessKit.build({duration, scenes, cues})`. Registro de tipos de cena.
- `index.template.html` — starter: copie pro `<block>/index.html`, edite só o `SCENES[]`.
- `vendor/`, `fonts/` — gsap + Arial Black/Inter.

## Fluxo pra montar um bloco/combo faceless
1. Transcreva o áudio (Scribe) → gere `assets/cues.js` (legenda karaokê word-timed).
2. Copie `index.template.html` → `index.html`, ajuste `data-duration`.
3. Preencha `SCENES[]`: cada cena com `start`/`end` (fronteira de ideia) e as **âncoras** dos reveals
   nos tempos das **palavras exatas** (sincronia fala↔motion é regra dura).
4. Pra cena `broll`: escolha o clipe pelo pool — `py ../broll-pool/pick_broll.py <tags>` — e declare
   um `<video class="clip" src=... data-start=<janela> data-duration=<dur> muted>` no nível do root
   (o `<video>` em sub-composição fica preto; ver README §9 do HyperFrames). Landscape → crop 9:16 antes.
5. `npx hyperframes render . -o out.mp4 -f 30 -w 3` → muxe o áudio do combo + loudnorm −14.

## Tipos de cena (SCENES[].type)
| type | pra quê | campos-chave |
|---|---|---|
| `headline` | pôster (só eyebrow+headline) | eb, ebc, hl |
| `isoladas` | badges soltas (problema "isolada") | items[4], heroAt, stagger |
| `connect` | badges conectadas por linha (solução) | items[4], heroAt, linkAt |
| `grid` | grade de certs + futuros + selo ∞ | items[], futbar, seal, heroAt/futAt/sealAt |
| `cost` | cards de custo + contador subindo | items[[t,v]], total, totalLabel, countAt |
| `flatline` | linha de carreira que achata + muro ✕ | heroAt, stopAt |
| `stopdate` | círculo stop ✕ + data grande | date, heroAt, dateAt |
| `lock` | certificação bloqueada 🔒 | lockLabel, heroAt |
| `vaga` | card de oportunidade/vaga | role, sub, upline, heroAt |
| `cta` | datecard + LIVE + botão pulsante | date, dateSub, live, btn, dateAt/liveAt/btnAt |
| `broll` | grade escura + lower-third (sobre `<video>`) | lt, ltc, ltAt |

Comuns a (quase) todos: `eb` (eyebrow), `ebc` (cor: cy/gr/co/ye), `hl` (headline, aceita `<br>`+`<span class='co'>`),
`ebAt`/`hlAt` (tempos; default = start+0.15 / +0.27). Cores: `.cy` ciano, `.gr` verde, `.co` coral, `.ye` amarelo.

## Regras herdadas (não quebrar)
- **Set-no-init + reveal-com-.to** (a engine já faz) → nada vaza antes da hora.
- **Sincronia fala↔motion**: cada reveal na palavra exata (setar os `*At`).
- **Cenas nunca vazias**: eyebrow no start, hero em ≤0,5s.
- **Só certificações reais** (CPA, CPRO-I, CPRO-R, CFP) — nunca inventar.
- **Legenda**: pill branco fixo (a engine já monta de `cues`).
- **Duração do bloco = block_cap** (senão `-shortest` corta a fala no combo).
