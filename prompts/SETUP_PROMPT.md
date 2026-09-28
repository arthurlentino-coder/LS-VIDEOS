# Prompt de setup — Processo de edição de criativos (v2, 2026-09-28)

> Cole o texto entre as linhas `=====` numa sessão NOVA do Claude Code (app desktop, aba Code),
> aberta na pasta-raiz `VIDEOS/`. Ele reconstrói o processo que está em produção: pipeline
> video-use + Scribe + zoom seam + karaokê HyperFrames + 4 formatos (normal/split/hybrid/faceless)
> + trilha com gate + app **Mesa de Corte** + bibliotecas reusáveis + finalizadores com gate.
>
> A referência detalhada é o `README.md` da raiz (as § citadas abaixo são de lá). Se este prompt e
> o README divergirem, o README manda; se o README divergir do código, o código manda.
> A v1 (só video-use + legenda arredondada, sem HyperFrames) está em `prompts/_legado/`.

==========================================================================

Você vai operar o processo de edição de criativos em vídeo (talking-heads 9:16 de marketing
educacional/financeiro) que já está validado em produção. Qualidade acima de economia.
Leia o `README.md` da raiz INTEIRO antes de editar qualquer vídeo.

## 1. Ambiente (verificar e me reportar antes de tudo)

Windows 11, PowerShell. Confirme cada item e me diga o que falta — não instale nada sem me avisar.

- **Python 3.12 via `py`** (o `python` desta máquina é o atalho da Microsoft Store e NÃO funciona;
  use sempre `py`). Pacotes: `video-use` (instalação editável em `..\claude\video use`),
  `opencv-python-headless`, `onnxruntime`, `numpy`, `librosa`, `requests`, `yt-dlp`.
- **ffmpeg/ffprobe** (winget). **Node 24** em `C:\Program Files\nodejs` (fora do PATH da sessão →
  sempre via wrapper `& "$HELPERS\hf.ps1" <cmd>`).
- **ElevenLabs Scribe:** `ELEVENLABS_API_KEY` no `.env` da instalação `video use`. Nunca exibir,
  copiar ou pedir a chave em chat — só testar que funciona.
- **Skills** em `~\.agents\skills` (source `heygen-com/hyperframes`: hyperframes, hyperframes-cli,
  -core, -animation, -creative, -media, faceless-explainer…), `watch` (bradautomates/claude-video),
  `ponytail*`, `impeccable` (no projeto, com hooks), `graphify`, `notebooklm`. Metodologia de corte =
  `video use\SKILL.md`.
- Variáveis de sessão (README §1): `$VIDEOS`, `$HELPERS` (= `..\claude\video use\helpers`:
  transcribe, transcribe_batch, pack_transcripts, render, grade, hf_subs, timeline_view, hf.ps1),
  `$PYSCRIPTS`, `$TOOLS`. Rodar Python com `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.

## 2. Pastas e nomes

```
VIDEOS/
  input/<LOTE>/                 brutas — NUNCA alterar nem re-transcrever
  projects/<nome>/edit/         todo o trabalho (transcripts/, edl.json, master, base, hf/, project.md)
  output/<LOTE>/                entregas por lote (ex.: output/CFP/, output/FINCAPITAL/Lote 3/,
                                output/FINCAPITAL/Avulsos 2026-09-09/); flat OU subpastas por formato
  apps/mesa-de-corte/           app local (cockpit do pipeline)
  _scaffolds/                   kits e bibliotecas reusáveis (split-kit, faceless-shotseq, faceless-kit,
                                anim-library, broll-pool, brand, flow-hybrid)
  _codex/video-system/          sistema do Codex (presets de zona/gramática + QA) — não editar o
                                prompts/CODEX_EDITING_STANDARD.md, só o usuário
  scripts/                      one-offs + guard_ciladas.py, tighten_edl.py
```

- **Nome por formato:** normal = `<nome>.mp4` (SEM sufixo); demais `<nome>_split|_hybrid|_faceless.mp4`;
  trilha = `<nome>_trilha.mp4` ao lado. Combinatório = `<PREF>_H03_D02_F1`.
- **Git** versiona o processo (README, prompts, scripts, app, `_scaffolds/`, `_codex/video-system`);
  mídia, `projects/`, `input/`, `output/` e `orders/` ficam fora.
- **Projeto novo:** `cp -r _scaffolds/pipeline-kit/edit/. projects/<nome>/edit/` — é a fonte canônica
  de `zoom_concat`, `compose_hfsubs`, `facecrop`, `yunet*`, `sfx_mix`. Não copiar de projeto antigo.
  Máquina nova: instalar o video-use com o patch de `_scaffolds/pipeline-kit/video-use/`.

## 3. Como os pedidos chegam — Mesa de Corte

- Subir: `py apps/mesa-de-corte/server.py` → http://localhost:8756 (ou `preview_start mesa-de-corte`).
- O usuário escolhe pasta de `input/`, lane **Lote padrão** (presets Lucas/LS · FinCapital ·
  MARE/VSL) ou **Edição geral** (Formato + Legenda + "Opções avançadas"), roteiro, trechos in/out,
  combos gancho×corpo×CTA, e clica "Começar". Isso grava `apps/mesa-de-corte/orders/<lote>.json`
  (fila com status `pendente → em_edicao → revisar → aprovado`) e uma linha em `orders/_events.txt`.
- **Em toda sessão nova, armar o watcher** (Monitor persistente):
  `tail -n0 -F "apps/mesa-de-corte/orders/_events.txt"` — eventos `START`, `APPROVE …proximo=<id>`,
  `AJUSTE … nota=…`. Fora de sessão, a Tarefa Agendada `MesaDeCorte-QueueNotify` só NOTIFICA.
- Ao receber pedido: **responder na hora "recebi"** (lote, nº itens, formatos, item ativo) e dar uma
  linha de status a **cada etapa** (probe → transcrição → master → EDL → base → cada formato →
  finish/gate → QA).
- Progresso na fila: `py apps/mesa-de-corte/set_status.py <lote> <item> revisar <saida.mp4>`.
  UM item em edição por vez; o próximo só depois do APPROVE (exceto combinatório).
- Pedido colado no chat (JSON "Ordem de Edição") vale igual.

## 4. Antes de cortar

1. **Formatos:** confirmar por lote quais (normal/split/hybrid/faceless/trilha) — o preset do app
   já responde; se veio pelo chat, PERGUNTAR.
2. **Roteiro:** ler o roteiro anexado e conferir se bate com as brutas (já veio doc errado).
   Nº do arquivo ≠ ordem do roteiro — mapear por transcrição.
3. **Inventário `ffprobe`:** resolução, fps, rotação (stream E displaymatrix), transfer, áudio.
   - **Rotação varia por lote** — decidir por evidência e validar 1 frame:
     metadado `rotation=-90` no stream (iPhone .MOV, CPRO-I) → ffmpeg autorrota, **sem transpose**;
     3840×2160 com retrato deitado sem metadado ou só a nível de pacote (PERPETUOS, MARE, ANBIMA,
     FinCap L3, MISSÃO CPA) → **`transpose=1`** (`transpose=2` sai de cabeça pra baixo).
   - **HLG/DV (bt2020)** → master SDR com a cadeia do README §6. **bt709/xvYCC SDR** → sem tonemap.
4. **Transcrição Scribe** (`transcribe.py … --language pt`, áudio **48 kHz** — 16 kHz derrubou
   takes), cache em `transcripts/`, nunca re-transcrever. `pack_transcripts.py` → `takes_packed.md`.
   Corrigir tokens: certificações (CPA, CPA-20, CPRO-I, CPRO-R, CFP, ANBIMA, CEA), nomes, datas.
5. **Seleção de take** (nesta ordem): olhando pra câmera (cabeça baixa = ensaio, descarta) →
   fiel ao roteiro → sem bastidor. **Errou-e-recomeçou = descarta a passada inteira** até o
   recomeço. **Esquete/historinha proposital FICA**; blooper/direção/conversa SAI. Refrão proposital
   não é retake. Bruta com slate falado ("Script N, empresa/neutro/só voz") = vários criativos.

## 5. Pipeline por formato

**Base (todos):** `edl.json` com ranges sem sobreposição (`end ≤ start` seguinte), cortes em
respiração → `zoom_concat.py --mode seam --hold 0.12 --zoom-t 0.14 --start-dir in` →
`base_zoom_seam.mp4` (fps da fonte). Conferir a **cauda comprimida do Scribe** com `silencedetect`
antes de fechar cada range final. VSL: +1s de "gordurinha" no fim.

- **Normal** — karaokê `hf_subs.py --crossfade 0 --box-alpha 0.3 --preset vertical` → `hf.ps1 lint`
  → render webm → `hf/compose_hfsubs.py` (força `-c:v libvpx-vp9`, `-t` da base, loudnorm −14).
  Legenda **nunca sobre o rosto** (medir com YuNet em close/contra-plongée).
- **Split** — topo `facecrop.py` (YuNet via `yunet_ort.py`/onnxruntime; OpenCV 5 retorna 0 faces)
  1080×960; embaixo motion a partir do **`_scaffolds/split-kit`** (editar só `SCENES[]`);
  legenda-divisória `--box-bottom 1035 --box-alpha 1.0`; SFX `sfx.json`.
  Fechar com **`py apps/mesa-de-corte/finish_split.py --edit <dir> --out <mp4>`**.
- **Hybrid** — footage o tempo todo + card lower-third compacto por beat (`bottom:214px`) +
  karaokê acima do card. Fechar com **`finish_hybrid.py`**.
- **Faceless** — padrão = **`_scaffolds/faceless-shotseq`** (shot-sequence, README §7.6.1);
  `faceless-kit` se for data-viz pesado; `faceless-editorial` é LEGADO. Cenas preenchem logo
  (herói ≤ ~0,5 s), hard-cut entre frames, b-roll só onde a fala pede (`broll-pool/pick_broll.py`).
  MARE/VSL: sem legenda. Fechar com **`finish_faceless.py`**.
- **Trilha** — `<nome>_trilha.mp4` ao lado, pad sintetizado (7ª/9ª + celeste, ducking, 2 whooshes);
  moods calmo/sério/enérgico; **gate de vibe** por vídeo — se destoa, não entra (README §7.7).
- Os finalizadores rodam o **gate `check_cert.py`** (bloqueia "CPA" num vídeo CPRO-I etc.;
  bypass `SKIP_CERT=1` só com motivo). Sempre usá-los em vez de ffmpeg inline.

## 6. Motion (split/hybrid/faceless)

- **Gate de motion-plan:** `motion-plan.md` (1 linha/cena) + **preview SVG inline (show_widget)**
  dos gráficos → aprovação do usuário → só então build/render.
- Avaliar pela **ideia** da cena, não pela frase literal. Todas as cenas do vídeo no **mesmo
  patamar**. Tom adulto/corporativo (nada de mascote). Nada congela (idle). Paleta coesa por cena.
- Reusar antes de criar: `anim-library` (22 heroes SVG + ILLOS capture-safe; Lottie SVG puro morre
  no capture, só climbstairs sobrevive → preferir SVG grande inline), `broll-pool` (32 clipes; sem
  marca/instituição real visível), `brand/lucas-silva-logo.png`. Novos assets: LottieFiles, Flaticon
  (via browser embutido), Pexels grátis.
- Validar layout **sem render**: `hf.ps1 snapshot --at …` ou Browser pane + `getBBox()`. Texto
  nunca estoura a forma (`textLength`). `py scripts/guard_ciladas.py projects/<nome>/edit` → 0 erros.
- Ciladas (README §9): nunca x/y num `<g translate()>`; `svgOrigin` e não `transformOrigin px`;
  `immediateRender:false` em fromTo de flash; sem drawSVG; `<video>` só no nível do index;
  contador seek-safe; overlay webm com `libvpx-vp9`.

## 7. QA e entrega

- `py apps/mesa-de-corte/qa_lote.py <lote>` (duração entre formatos, −14±1,5 LUFS, preto, mudo,
  1080×1920/~30fps) + `/watch` em cada entregável (`--detail balanced --no-whisper`, 720+ p/ ler texto).
- Checklist README §12. Entregar `_REVIEW` em vez de sobrescrever aprovado. Disco cheio → apagar
  masters/motions regeneráveis de itens já aprovados (nunca `input/` nem `output/`).
- Atualizar `project.md`, marcar `revisar` na fila e, ao mudar qualquer padrão, atualizar o README.

## 8. Primeira resposta esperada

Antes de editar, me diga: status de cada item da §1 (ok/falta), se a chave Scribe respondeu,
se o app sobe em :8756, se o watcher está armado, e qual pedido/lote está pendente em `orders/`.

==========================================================================
