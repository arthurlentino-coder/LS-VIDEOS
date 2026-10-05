# Prompt de setup — Processo de edição de criativos

> Cole o texto entre as linhas `=====` numa sessão nova do Claude Code (app desktop, aba Code),
> aberta na pasta-raiz `VIDEOS/`. Detalhes de cada etapa estão no `README.md` da raiz (as §
> citadas são de lá). Se este prompt e o README divergirem, vale o README; se o README divergir do
> código, vale o código.

==========================================================================

Você vai operar o processo de edição de criativos em vídeo (talking-heads 9:16 de marketing
educacional e financeiro). Qualidade acima de economia. Leia o `README.md` inteiro antes de editar.

## 0. Máquina nova — conferir o ambiente PRIMEIRO
Antes de qualquer coisa, rode o doctor e resolva o que ele apontar (guia em
`_scaffolds/pipeline-kit/SETUP.md`):
```
py _scaffolds/pipeline-kit/doctor.py
```
Ele confere ffmpeg/ffprobe, Node+npx+HyperFrames, a estrutura do `VIDEOS/`, YuNet, a lib de SFX,
os **helpers do video-use** (ficam FORA do repo — `VIDEO_USE_HELPERS`) e `ELEVENLABS_API_KEY`.
`✗` = essencial faltando. Caminhos são auto-detectados; sobrescreva com `VIDEOS_ROOT`,
`VIDEO_USE_HELPERS`, `HF_SFX_DIR`. Rodar Python com `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.
> O repo versiona só o PROCESSO; mídia (input/output/masters) e os helpers do video-use não vêm
> no git — numa máquina nova, traga a mídia e instale os helpers (ver SETUP.md §3).

## 1. Ferramentas e integrações

### 1.1 Base (obrigatórias)
| Ferramenta | Para quê | Como chamar / onde fica |
|---|---|---|
| Windows 11 + PowerShell / Git Bash | ambiente | — |
| **Python 3.12 via `py`** | todos os scripts | `py` (o `python` é o atalho da Microsoft Store e não roda) |
| **ffmpeg / ffprobe** | inventário, corte, tonemap, composição, loudnorm | winget; no PATH |
| **Node 24** | HyperFrames, impeccable, QA do Codex | `C:\Program Files\nodejs` (fora do PATH → usar `hf.ps1`) |
| **video-use** (instalação editável) | metodologia de corte + helpers | `<pai de VIDEOS>\claude\video use`; `SKILL.md` = método; `helpers\` = `transcribe.py`, `transcribe_batch.py`, `pack_transcripts.py`, `render.py`, `grade.py`, `timeline_view.py`, `hf_subs.py`, `hf.ps1` |
| **ElevenLabs Scribe** | transcrição word-level pt | `ELEVENLABS_API_KEY` no `.env` do video-use — nunca exibir nem pedir a chave em chat |
| **HyperFrames** (HTML → vídeo) + **GSAP** + **Lottie** | legenda karaokê, motion, overlays, faceless | `& "$HELPERS\hf.ps1" lint / render / snapshot` (roda `npx hyperframes`) |
| **Pacotes Python** | rosto, áudio, download | `opencv-python-headless`, `onnxruntime` (YuNet), `numpy`, `librosa`, `requests`, `yt-dlp` |
| **YuNet** (`yunet.onnx`) | detecção de rosto do split | `_scaffolds/pipeline-kit/edit/hf/` |
| **Git** | versiona o processo (não a mídia) | repo em `VIDEOS/` |

Máquina nova: instalar o video-use seguindo `_scaffolds/pipeline-kit/README.md` (clone no commit
de `BASE_COMMIT` + `render.py.patch` + `hf_subs.py` + `hf.ps1` + `pip install -e .`).

### 1.2 Skills do Claude Code
| Skill | Uso no processo |
|---|---|
| `hyperframes`, `hyperframes-cli`, `-core`, `-animation`, `-creative`, `-media`, `-registry`, `faceless-explainer`, `motion-graphics`, `embedded-captions`, `talking-head-recut`, `media-use` (repo `heygen-com/hyperframes`, em `~\.agents\skills`) | autoria e render das composições; `hyperframes-media/assets/sfx/` é a biblioteca de SFX |
| `/watch` (`bradautomates/claude-video`) | QA visual dos renders e leitura de referências — `--detail balanced --no-whisper`, `--resolution 720+` para ler texto |
| `/impeccable` (instalada no projeto, com hooks) | sinal de qualidade de design nos HTML de motion (não é gate) |
| `/ponytail`, `/ponytail-review`, `/ponytail-audit` | enxugar scripts e composições |
| `/graphify` (`$PYSCRIPTS\graphify.exe`) | mapa navegável do repositório |
| `/notebooklm` (`$PYSCRIPTS\notebooklm.exe`) | pesquisa e apoio de roteiro; login por `notebooklm login --browser chrome` |

### 1.3 Ferramentas do Claude Code usadas no fluxo
- **Monitor** persistente — watcher dos pedidos do app (§3).
- **show_widget** — preview SVG dos gráficos no gate de motion-plan (§6).
- **Browser embutido** (`Claude_Browser`) — medir layout das composições pelo DOM, abrir o app,
  buscar assets. Para `flaticon.com` usar este, não o Claude in Chrome (bloqueia o domínio).

### 1.4 Ferramentas do próprio repositório
| Onde | O quê |
|---|---|
| `apps/mesa-de-corte/` | app local (§3): `server.py`, `index.html`, `set_status.py`, `queue_notify.ps1`, `PADROES.html` |
| `apps/mesa-de-corte/finish_split.py`, `finish_hybrid.py`, `finish_faceless.py` | finalizadores por formato, com gate de certificação |
| `apps/mesa-de-corte/check_cert.py` | gate: barra certificação errada no texto do motion (bypass `SKIP_CERT=1` só com motivo) |
| `apps/mesa-de-corte/qa_lote.py` | QA técnico do lote inteiro |
| `scripts/guard_ciladas.py` | detector das ciladas de GSAP/SVG/ffmpeg num projeto |
| `_scaffolds/pipeline-kit/build_item.sh` | **build canônico de 1 item** (da base até entregue): make_divider + reconcile_durations + **lint_item** (gate pré-render) → render dos 4 formatos → finish → **dress (áudio por copy, PADRÃO)** → set_status revisar → QA. Flags: `RECONCILE=0`, `CTA_EXT=1`, `MOOD=…`, `DRESS=0`, `SKIP_CERT=1`, `VIDEOS_ROOT` |
| `_scaffolds/pipeline-kit/doctor.py` | checa o ambiente da máquina (binários/estrutura/assets/helpers/chave) |
| `_scaffolds/pipeline-kit/new_project.py` | scaffolda `projects/<x>/edit` dos kits + `edl.json` stub com a cert no note |
| `_scaffolds/pipeline-kit/edit/master.py` | **master SDR com receita AUTO** pelo ffprobe (tonemap HLG/PQ; transpose do metadado; `--rotate`/`--tonemap`/`--probe`) — usar no lugar de escrever a cadeia na mão |
| `_scaffolds/pipeline-kit/edit/fix_transcript.py` | corrige garbles do Scribe lote-aware (CPRO-I/CPRO-R/CFP/CPA/ANBIMA → token certo) + `--rules` (datas); DRY-RUN por padrão |
| `_scaffolds/pipeline-kit/edit/` | scripts de projeto: `zoom_concat.py`, `hf/compose_hfsubs.py`, `hf/facecrop.py`, `hf/yunet_ort.py`, `hf/sfx_mix.py`, `hf/make_divider.py` (gera subs-divider), `hf/reconcile_durations.py` (alinha durações à base), `hf/lint_item.py` (lint pré-render) |
| `_scaffolds/pipeline-kit/audio/` | **áudio por copy é PADRÃO**: `sfx_from_cues.py` (cues→sfx.json por palavra), `trilha.py` (`pick-mood` calmo/sério/enérgico + `dress`: bed 0.40 + SFX + ducking + swell no CTA + loudnorm −14), `dress_item.py` (veste os 4 formatos; split=bed-only; `--order` lê config.audio do lote), `music_gen.py` (recap/aftermovie) |
| `_scaffolds/split-kit/` | motion do split dirigido por `SCENES[]` |
| `_scaffolds/faceless-shotseq/` | faceless padrão (shot-sequence) |
| `_scaffolds/faceless-kit/` | faceless data-viz dirigido por `SCENES[]` |
| `_scaffolds/anim-library/` | heroes SVG e ilustrações capture-safe + registro de Lottie |
| `_scaffolds/broll-pool/` | b-roll 1080×1920 com tags: `pick_broll.py <tags>`, `gen_gallery.py` |
| `_scaffolds/brand/` | logos e avatares das marcas |
| `_scaffolds/flow-hybrid/` | contrato para base cinematográfica gerada no Flow/Veo |
| `_codex/video-system/` | presets de zonas e gramática visual + `qa/video-qa.mjs` (QA do faceless shot-sequence) |

### 1.5 Fontes externas de assets
- **LottieFiles** e **Flaticon animated icons** — personagens e ícones animados (vetor, sem PNG).
- **Tabler Icons** (MIT) — ícones estáticos recoloríveis.
- **Pexels / Pixabay / Mixkit / Coverr** — b-roll grátis de uso comercial; normalizar para
  1080×1920, sem áudio, e registrar no `broll.json`. Nada de marca/instituição real visível.
- **Windows Task Scheduler** — tarefa `MesaDeCorte-QueueNotify` (avisa pedido pendente fora de sessão).

### 1.6 Integrações opcionais
Nenhuma é necessária para entregar. Chaves ficam no `.env` do video-use (ou no ambiente) — nunca
exibir nem pedir em chat. **Tudo que gasta crédito: confirmar com o usuário antes de rodar.**

| Integração | Para quê | Acesso | Como entra no processo |
|---|---|---|---|
| **Google Flow / Veo** | base cinematográfica por cena (ambiente, metáfora, pessoa) | web do Flow (geração manual; a API Gemini dá limite) | base SEM texto; todo texto vem do HyperFrames; contrato em `_scaffolds/flow-hybrid/` (README §7.3.3) |
| **Opus Clip** | vídeo longo → cortes curtos com reenquadramento por falante | API `api.opus.pro`, `OPUS_API_KEY` (Bearer); arquivo local via `upload-links` | criar o projeto com `renderPref.enableCaption=false` e queimar a nossa karaokê por cima |
| **Descript** | edição por transcrição, limpeza de áudio (Studio Sound), filler words, dublagem | API `descriptapi.com/v1`, `DESCRIPT_API_KEY` (token inteiro como Bearer) | limpeza de áudio ruim ou tradução; o corte continua sendo o nosso EDL |
| **Topaz Video** | upscale, denoise, estabilização, interpolação de frames | API `api.topazlabs.com`, `TOPAZ_API_KEY` (header `X-API-Key`) | recuperar bruta de baixa qualidade antes do master |
| **Freepik** | stock licenciado (fotos, vetores, ícones) + geração por IA (Mystic, Kling, Runway) | API `api.freepik.com`, `FREEPIK_API_KEY` (header `x-freepik-api-key`); cliente em `_codex/video-system/tools/freepik.mjs` | asset sob medida quando o stock grátis não casa com a ideia da cena |
| **Hera / Kling / Firefly** | geração de ícones/animações por IA | `HERA_API_KEY` no `.env`; Kling/Firefly pela conta do usuário | só se superar o motion feito à mão (que é o padrão) |
| **HeyGen CLI** | catálogo de música/SFX (e TTS) da HeyGen | `~\.local\bin\heygen` → `heygen auth login --key` (o usuário faz) | faixa real no lugar da trilha sintetizada; sem login, usar `pipeline-kit/audio/trilha.py` |
| **Pippit** (skill `pippit-skill`) | geração/edição por IA e publicação/agendamento em TikTok, Instagram, Facebook | access key do Pippit (setup pela própria skill) | só se o usuário pedir publicação ou geração pela Pippit |

Variáveis de sessão (README §1): `$VIDEOS`, `$HELPERS`, `$PYSCRIPTS`, `$TOOLS`. Portabilidade:
`VIDEO_USE_HELPERS` e `HF_SFX_DIR` sobrescrevem os caminhos padrão. Rodar Python com
`PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.

## 2. Pastas e nomes

```
VIDEOS/
  input/<LOTE>/            brutas — nunca alterar nem re-transcrever
  projects/<nome>/edit/    trabalho (transcripts/, edl.json, master, base, hf/, project.md)
  output/<LOTE>/           entregas (cliente com vários lotes: output/<CLIENTE>/Lote N/ e
                           output/<CLIENTE>/Avulsos <AAAA-MM-DD>/)
  apps/  _scaffolds/  _codex/  scripts/  prompts/
```

- Projeto novo: `cp -r _scaffolds/pipeline-kit/edit/. projects/<nome>/edit/`.
- Nomes: normal = `<nome>.mp4`; `<nome>_split`, `_hybrid`, `_faceless`, `_trilha`.
  Combinatório = `<PREF>_H03_D02_F1`.
- `prompts/CODEX_EDITING_STANDARD.md` é do fluxo Codex — só o usuário edita.

## 3. Como os pedidos chegam — Mesa de Corte

- Subir: `py apps/mesa-de-corte/server.py` → http://localhost:8756 (ou `preview_start mesa-de-corte`).
- O usuário escolhe a pasta de `input/`, a lane **Lote padrão** (presets por cliente) ou **Edição
  geral** (formato, legenda, opções avançadas), roteiro, trechos in/out, combos gancho×corpo×CTA.
  "Começar" grava `apps/mesa-de-corte/orders/<lote>.json` (fila `pendente → em_edicao → revisar →
  aprovado`) e uma linha em `orders/_events.txt`.
- **Toda sessão:** armar Monitor persistente `tail -n0 -F "apps/mesa-de-corte/orders/_events.txt"`.
  Eventos: `START`, `APPROVE … proximo=<id>`, `AJUSTE … nota=…`.
- Ao receber: responder na hora "recebi" (lote, itens, formatos, item ativo) e dar uma linha de
  status a cada etapa (probe → transcrição → master → EDL → base → cada formato → finish → QA).
- Entregar: `py apps/mesa-de-corte/set_status.py <lote> <item> revisar <saida.mp4>`.
  Um item por vez; o próximo só após APPROVE (combinatório pode ir em paralelo).
- Revisão granular no app: aprovação/ajuste são **por formato e por parte** (legenda/takes/motion/
  transição/áudio…). Ao refazer só um formato, devolva com `set_status.py <lote> <item> revisar
  <saida> --fmt <formato>`. O evento `AJUSTE` traz `formatos=` e `partes=`; leia `item.ajustes`.
- Pedido colado no chat (JSON "Ordem de Edição") vale igual.

## 4. Antes de cortar

1. **Formatos** do lote: o preset responde; se veio pelo chat, perguntar.
2. **Roteiro:** conferir se bate com as brutas; nº do arquivo ≠ ordem do roteiro (mapear por fala).
3. **`ffprobe`:** resolução, fps, rotação (stream e displaymatrix), transfer, áudio.
   - Metadado `rotation=-90` → ffmpeg autorrota, **sem transpose**. Retrato gravado deitado
     (ex.: 3840×2160) sem metadado ou com rotação só no pacote → **`transpose=1`**. Validar 1 frame.
   - HLG/Dolby Vision (bt2020) → master SDR (README §6). bt709/xvYCC SDR → sem tonemap.
4. **Scribe** em áudio **48 kHz** (`transcribe.py … --language pt`), cache em `transcripts/`.
   `pack_transcripts.py` → `takes_packed.md`. Corrigir grafia de certificações (CPA, CPA-20,
   CPRO-I, CPRO-R, CFP, ANBIMA, CEA), nomes e datas.
5. **Take:** olhando pra câmera → fiel ao roteiro → sem bastidor. Errou e recomeçou = descarta a
   passada inteira. Esquete proposital fica; blooper e direção saem. Refrão proposital não é retake.
   Slate falado ("Script N, empresa/neutro/só voz") = vários criativos na mesma bruta.

## 5. Pipeline por formato

**Base:** `edl.json` com ranges sem sobreposição (`end ≤ start` seguinte), cortes na respiração;
fim de cada frase conferido com `silencedetect` (o Scribe comprime a cauda) →
`zoom_concat.py --mode seam --hold 0.12 --zoom-t 0.14 --start-dir in` → `base_zoom_seam.mp4`
no fps da fonte. VSL: +1 s de handle no fim.

- **Normal** — `hf_subs.py --crossfade 0 --box-alpha 0.3 --preset vertical` → `hf.ps1 lint` →
  render webm → `hf/compose_hfsubs.py`. Legenda nunca sobre o rosto.
- **Split** — topo `facecrop.py` 1080×960; motion pelo `split-kit`; legenda-divisória
  `--box-bottom 1035 --box-alpha 1.0`; SFX em `sfx.json` → **`finish_split.py`**.
- **Hybrid** — footage o tempo todo + card lower-third compacto por beat (`bottom:214px`) +
  karaokê acima do card → **`finish_hybrid.py`**.
- **Faceless** — `faceless-shotseq` (ou `faceless-kit` se for data-viz); cenas cheias em ≤0,5 s,
  hard-cut entre frames, b-roll só onde a fala pede; QA `node _codex/video-system/qa/video-qa.mjs <manifesto>`
  → **`finish_faceless.py`**. VSL faceless: sem legenda.
- **Trilha** — `audio/trilha.py build-bed --mood …` + `apply` → `<nome>_trilha.mp4` ao lado do
  final; só entra se a vibe combinar com o conteúdo (README §7.7).
- Todo fechamento: CRF 20, loudnorm two-pass −14 LUFS / −2,8 dBTP. Usar os finalizadores, nunca
  ffmpeg inline.

## 6. Motion (split, hybrid, faceless)

- **Gate:** `motion-plan.md` (1 linha por cena) + preview SVG via show_widget → aprovação → build.
- Cada cena pela **ideia**, não pela frase literal. Todas as cenas no mesmo patamar. Tom adulto e
  corporativo (sem mascote). Nada congela (idle). Paleta coesa por cena.
- Reusar antes de criar: `anim-library`, `broll-pool`, `brand`. Lottie SVG puro não sobrevive ao
  capture — preferir SVG grande inline ou o pré-render em canvas (README §7.3.1).
- Validar sem render: `hf.ps1 snapshot --at <t>` ou Browser + `getBBox()`; texto nunca estoura a
  forma. `py scripts/guard_ciladas.py projects/<nome>/edit` → 0 erros.
- Ciladas (README §9): sem x/y em `<g translate()>`; `svgOrigin`; `immediateRender:false` em
  fromTo de flash; sem drawSVG; `<video>` só no nível do index; contador seek-safe;
  overlay webm com `-c:v libvpx-vp9` e `-t` da base.

## 7. QA e entrega

- `py apps/mesa-de-corte/qa_lote.py <lote>` + `/watch` em cada entregável + checklist README §12.
- Nunca sobrescrever aprovado (entregar `_REVIEW`). Disco cheio → apagar masters/motions
  regeneráveis de itens aprovados, nunca `input/` ou `output/`.
- Registrar em `project.md`. Mudou um padrão → atualizar README e este prompt; mudou um script do
  kit ou do video-use → regravar em `_scaffolds/pipeline-kit/` e commitar.

## 8. Primeira resposta esperada

Antes de editar: status de cada ferramenta da §1.1 e §1.2 (ok/falta), se a chave Scribe respondeu,
se o app sobe em :8756, se o watcher está armado, quais pedidos estão pendentes em `orders/` e,
das integrações opcionais (§1.6), quais têm chave ou login configurado — só checar a presença, sem
chamada que gaste crédito.

==========================================================================
