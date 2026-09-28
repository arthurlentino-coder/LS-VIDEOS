# Engine faceless — shot-sequence (padrão §7.6.1)

Scaffold que garante que TODO faceless saia no padrão batido em 2026-08-24.
Referência viva: `output/TESTES/VIT_H1_D1_F1_faceless.mp4` (fonte `projects/VITALICIO/_map/edit/hf/faceless/`).

## O que este scaffold já traz pronto
- `index.html` — esqueleto (áudio → b-roll → frames → captions), com as regras de ouro nos comentários.
- `compositions/captions.html` — **karaokê embutido** (pill creme, palavra ativa escurece), lê `assets/cues.js`.
- `compositions/frames/_blueprint-*.html` — 4 blueprints com o **motion de ouro baked**:
  - `poster` — eyebrow + headline 2 linhas + apoio/número.
  - `cards-accumulate` — lista que entra 1 a 1 + count-up.
  - `broll-overlay` — overlay TRANSPARENTE (grade+tint+vinheta+lower-third) p/ frames de b-roll.
  - `cta` — botão + press + mount de Lottie opcional.
- `vendor/` (gsap + lottie), `fonts/` (Arial Black + Inter), `hyperframes.json`.
- `gen_cues.mjs` — transcript → `assets/cues.js`.

## 🎯 DIREÇÃO VISUAL-FIRST (default #1 — feedback 2026-08-25: "focou demais no texto")
**O VISUAL carrega a mensagem, NÃO o texto.** Erro a evitar: cards de palavra gigante centralizada tomando a tela (kinetic-typography) — a legenda karaokê JÁ mostra a fala, então texto grande é redundante.
- **Protagonista da cena = ícone/ilustração animada ou LOTTIE de personagem** (grande, ~500–620px, centro). Texto = **headline PEQUENO de apoio** (~78–94px, canto/topo), estilo "equilibrado" da referência.
- **Lottie de personagem** nos momentos humanos e no CTA (§7.6.1). Assets em `assets/lottie/` (9): runner(urgência) climbstairs(progresso) graduation(aprovação) exam(prova) manworking(estudo) chat badge click(CTA) wave. Blueprint `_blueprint-lottie-hero.html`. **⚠️ CILADA: Lottie SVG puro (`renderer:'svg'`+`goToAndStop`) SOME no capture do hyperframes.** Fix VALIDADO = **CANVAS pré-renderizado**: rasterizar cada frame (SVG→dataURL img→canvas) num array `FR`, e a timeline desenha `ctx.drawImage(FR[i])`; registrar a promise do preload em `window.__ready` p/ o render ESPERAR. (blueprint já traz o helper `preload()`.)
- Cada cena responde: **"que IMAGEM/animação representa essa fala?"** (não "que palavra escrever"). Diagrama/comparação/progressão/b-roll/Lottie — a palavra é só rótulo.
- Referência viva do estilo: `_codex/validation/C0207/faceless-v7-rebuild/compositions/frames/01-inscricoes.html` (runner Lottie 520px + card ilustrado + headline pequeno top-left).

## ⚠️ REGRAS PERMANENTES (feedback do usuário — valem p/ TODO lote pelo app)
**Estas duas são as que mais voltam. Conferir SEMPRE antes de entregar:**

### A) Sincronia fala ⇄ motion (cada entrada NA palavra)
- Extrair os tempos das palavras do transcript (`words` com `type==='word'`, `.start`) e amarrar **cada reveal** ao tempo local = `palavra_abs − frame_start`. Ex.: o hero só entra quando a locução DIZ aquilo — nunca antes (regressão clássica: "NÍVEL ABSURDO" entrando 3s antes de ser falado).
- Antes de renderizar, listar os anchors (`node -e` com find por palavra) e usar esses números nos `tl.to(...,{}, T)`.
- Count-up de número termina **na palavra do número**.

### B) Cena NUNCA vazia (encher a tela cedo, sem quebrar a sincronia)
- Preencher o **topo ~83%** (hero y260–1050, apoio y1080–1450). Metade de baixo vazia = "fraco/vazio".
- Se a palavra-chave da cena só é dita lá pra frente, **encher a tela ANTES com o que já está sendo falado** (ex.: marca/eyebrow/ícone entra em ~0.9s), e o payoff cai na palavra. Técnica validada: elemento **nasce GRANDE no centro** e **sobe** pra abrir espaço quando o payoff chega.
- Cena longa (>~5s) com **1 reveal só = lenta**. Preferir **mais cenas curtas com hard-cut** + beats internos frequentes (mudança visual a cada ≤~3–5s). Se a cena tem que ser longa, dar 2–3 beats internos + motion secundário contínuo.
- Câmera presente ajuda a "encher" (stage ~1.06 / bg ~1.10 push-in pela duração toda).

## Motion de ouro (não quebrar — é o que diferencia do build simplificado)
1. **Sub-composição POR FRAME** — cada frame é um `<template>` com timeline própria `window.__timelines['id']`. NUNCA single-file monolito.
2. **1 frame a cada ~5–7s** — 33s ≈ 5–7 frames; 68s ≈ 9. Cada frame se desenvolve a **duração inteira**.
3. **Nada congela:** todo frame tem `push-in lento do .stage` + `parallax do .bg` rodando por `D` inteiro, e um `idle` (float/wobble yoyo) depois das entradas.
4. **Reveal semântico** — cada peça entra **na palavra** correspondente (back.out); números usam **count-up**.
5. **B-roll** = `<video class="clip">` no `index` (1º no DOM = camada baixa) nos beats de emoção; o frame é overlay transparente.
6. **Legenda** = sempre `captions.html` embutido. Nunca burnar .ass no faceless.
7. Paleta `#07131f` / ciano `#22d3ee` / verde `#34d399` / amarelo `#fbbf24` só p/ deadline/CTA/1 ênfase; coral `#ff5c67` p/ custo/negativo. Display Arial Black uppercase.

## Fluxo de autoria (por vídeo)
1. `cp -r _scaffolds/faceless-shotseq projects/<PROJ>/edit/hf/faceless`
2. Copiar o áudio da narração p/ `assets/audio.m4a` (do master/base_zoom_seam) e o transcript.
3. `node gen_cues.mjs <transcript.json> assets/cues.js`
4. Planejar os beats (gate de storyboard SVG antes) → 1 frame por beat.
5. Para cada beat: `cp compositions/frames/_blueprint-<tipo>.html compositions/frames/NN-nome.html`,
   trocar `data-composition-id`, o texto e `D` (= data-duration do frame).
6. Preencher o `index.html`: uma linha `<div class="scene" ...>` por frame (start/duration casados),
   e `<video class="clip">` p/ cada b-roll.
7. `npx hyperframes lint .` → `npx hyperframes render . -f 30 -q draft -w 2 --protocol-timeout 900000`
   (2 workers p/ não estourar RAM). Áudio já entra via `<audio class="clip">` — sem mux manual.
8. QA frame-a-frame (ffmpeg -ss) antes de entregar. Entregar `_REVIEW`.

## Ciladas (valem sempre)
- Elemento posicionado precisa de `position:absolute` explícito (senão empilha no canto).
- `fromTo` sem `immediateRender:false` vaza o "from"; arte centrada em `left:50%` precisa `xPercent:-50` no from E no to.
- Vídeo dentro de sub-composição sai PRETO → b-roll SEMPRE no index.
- `drawSVG` é plugin premium — usar scale/opacity reveal.
- Snapshot é flaky com Lottie — validar cena de Lottie no render, não no snapshot.
