# VIDEOS — processo padrão de edição (guia p/ replicar)

Convenção fechada em 2026-06-29, **validada e em produção** (IMG_5055 9:16, C0205 16:9+9:16,
e os lotes CPA / C-PRO I / C-PRO R). Este documento é a referência para **qualquer colega
replicar o processo do zero**. Se algo aqui divergir do que você vê no código, o código manda —
avise para atualizarmos o doc.

---

## 0. TL;DR — o que entregar

> **Atualizado 2026-09-28.** O prompt de setup para reconstruir tudo numa sessão nova é
> `prompts/SETUP_PROMPT.md` (v2). Pedidos chegam pelo app **Mesa de Corte** (§13).

Os formatos são **definidos por lote** — o preset do app responde (Lucas/LS e FinCapital =
normal+split+hybrid+faceless; MARE/VSL = só faceless sem legenda); se o pedido veio pelo chat,
**perguntar**. Formatos disponíveis:

1. **Normal** (`<nome>.mp4`, sem sufixo) — talking head + **zoom `seam`** + **karaokê** (`box-alpha 0.3`).
2. **Split** (`_split`) — topo reenquadrado por rosto + **legenda na divisória** (`box-alpha 1.0`) + motion embaixo (`_scaffolds/split-kit`) + **SFX**.
3. **Hybrid** (`_hybrid`) — footage o tempo todo + card lower-third compacto por beat (`bottom:214px`) + karaokê acima do card. Ref. `projects/IMG_5055/edit/hf/hybrid/motion-plan.md`.
4. **Faceless** (`_faceless`) — shot-sequence §7.6.1, scaffold `_scaffolds/faceless-shotseq`.
5. **Trilha + SFX** (`_trilha`) — camada de áudio sutil (§7.7), **com GATE de vibe** por vídeo: se destoa do conteúdo, não entra.

Todo split/hybrid/faceless fecha pelos **finalizadores com gate de certificação** (§13.2).

---

## 1. Estrutura de pastas

```
VIDEOS/
  input/                      Fontes originais. NUNCA alteradas nem re-transcritas.
                              Lotes por assunto em subpastas (ex.: input/CPA/CPA 1.MOV).
  output/<LOTE>/              Finais entregues, por lote (ex.: output/CFP/, output/FINCAPITAL/Lote 3/,
                              output/FINCAPITAL/Avulsos <AAAA-MM-DD>/). Flat ou subpastas por
                              formato — o qa_lote.py aceita os dois. Normal SEM sufixo.
  projects/<nome>/
      edit/                   Todo o trabalho: transcript, edl.json, clips, legendas,
                              base/preview, helpers locais, hf/ (composições HyperFrames).
      edit/project.md         Log do projeto (decisões, parâmetros, status).
  prompts/                    Prompts e specs de referência (SETUP_PROMPT.md,
                              CODEX_EDITING_STANDARD.md). README.md fica na raiz.
  scripts/                    Scripts soltos por lote/one-off (_perp_*, _fincap*, _cpro*,
                              _lottie*, guard_ciladas.py, tighten_edl.py, …).
  apps/                       Interfaces web auxiliares (studio-criativos ×3, mesa-de-corte).
  _codex/                     Sistema de vídeo por-frame (video-system/, validation/, refs).
  _scaffolds/                 Kits e bibliotecas (§13.3): split-kit, faceless-shotseq, faceless-kit,
                              anim-library, broll-pool, brand, flow-hybrid (faceless-editorial = legado).
  _temp/                      Artefatos temporários / auditoria (assets-temp, snapshots-audit).
```

> **Python = `py`.** O `python` desta máquina é o atalho da Microsoft Store e não roda; onde este
> guia escreve `python`, use `py`. **Git** versiona o processo (docs, app, scripts, kits); mídia e
> `projects/`/`output/` ficam fora. Scripts de projeto: `_scaffolds/pipeline-kit/` (ver §13.4).

- **`<nome>`** = nome-base do arquivo de origem (`IMG_5055`, `CPA_1`, …).
- **Entrada:** joga o arquivo original em `input/`; o `edl.json` referencia a fonte por
  caminho absoluto. A fonte fica **intocada** e nunca é re-transcrita (cache em `transcripts/`).
- **Saída:** `output/<nome>.mp4` (padrão) e `output/<nome>_split.mp4` (split). Duas orientações
  do mesmo vídeo: `<nome>_landscape.mp4` / `<nome>_vertical.mp4`.

**Helpers compartilhados** (render.py, transcribe.py, hf_subs.py, zoom_concat.py, facecrop.py,
sfx_mix.py, …) vêm da **instalação editável `video-use`**. Cada projeto recebe **cópia local**
dos scripts que ajusta por vídeo (`round_subs.py`, `zoom_concat.py`, `hf/compose_hfsubs.py`,
`hf/facecrop.py`, `hf/sfx_mix.py`).

A metodologia de edição é a skill **`video-use`**.

### Convenção de caminhos (portátil)

Este guia **não** usa caminhos absolutos. Defina duas referências uma vez, na sua máquina, e
use-as no resto do documento:

- **`$VIDEOS`** = a raiz deste repositório (a pasta que contém este `README.md`).
- **`$HELPERS`** = a pasta `helpers/` da instalação editável `video-use`. Por padrão ela fica
  ao lado do repo (`$VIDEOS\..\claude\video use\helpers`), mas confirme onde o `pip install -e`
  a colocou na sua máquina.
- **`$PYSCRIPTS`** = a pasta `Scripts/` do Python (onde ficam os CLIs instalados por `pip`, ex.:
  `graphify.exe`, `notebooklm.exe`). **Ela NÃO está no PATH desta máquina** — chamar sempre pelo
  caminho completo, mesma cilada do Node/`hf.ps1` (ver §8).
- **`$TOOLS`** = `$VIDEOS\..\claude\tools` — clones das ferramentas auxiliares da §11.

No PowerShell, no início da sessão:
```powershell
$VIDEOS    = "$PSScriptRoot"                     # ou o caminho da sua pasta VIDEOS
$HELPERS   = Resolve-Path "$VIDEOS\..\claude\video use\helpers"   # ajuste se necessário
$PYSCRIPTS = Split-Path (Get-Command python).Source | Join-Path -ChildPath "Scripts"
$TOOLS     = Resolve-Path "$VIDEOS\..\claude\tools"
Set-Location $VIDEOS
```
A partir daqui, todo comando referencia `$HELPERS\<script>` e caminhos **relativos** à raiz do
repo (`projects\...`, `input\...`, `output\...`) — nunca `C:\Users\...`.

---

## 2. Pipeline padrão (versão 1 — talking head)

Ordem validada (IMG_5055 9:16 e C0205 16:9+9:16; DV/HLG cobertos na seção 6):

1. **Inventário** — `ffprobe` na fonte (resolução, fps, rotação, HDR/HLG).
2. **Transcrição** — `transcribe.py <src> --edit-dir projects/<nome>/edit --language pt`
   (ElevenLabs **Scribe**, pt, cache em `transcripts/` — **nunca** re-transcreve).
   Corrigir tokens que o Scribe erra (ex.: "Atacada"→"A tacada"; nomes de certificação).
3. **EDL** — montar `edl.json`: ranges/crops/transição. Regras:
   - Cortar nas **respirações de frase** (aperta o texto e dá ritmo ao zoom).
   - **"Errou-e-repetiu":** se a pessoa erra e refaz, corta o take inteiro do erro.
   - **RANGES NÃO PODEM SE SOBREPOR em source-time** (`start` do próximo ≥ `end` do anterior) —
     senão a legenda conta as palavras da fronteira 2× e cria uma *cue-fantasma* (ver Gotchas).
4. **Grade** — `grade.py` só se a fonte for HDR/HLG (ver seção 6). Se já for SDR, `grade:null`.
5. **Transição / base** — **zoom `seam`** (padrão, seção 4) → `base_zoom_seam.mp4`.
6. **Legenda karaokê** — `hf_subs.py` → render webm → `compose_hfsubs.py` (seção 5).
7. **Fechamento** — `compose_hfsubs.py` (normal) ou os finalizadores §13.2 (split/hybrid/faceless):
   CRF 20, **loudnorm two-pass** alvo **−14 LUFS / −2,8 dBTP**, um passe só, no fim.
   (`round_subs.py` = alternativa estática antiga; só resta 1 cópia, em `projects/intro1_final1/`.)

### 2.1 Regras de entrada que mudaram desde a v1 (consolidado 2026-09-28)

- **Rotação varia por lote — decidir por evidência e validar 1 frame.** `rotation=-90` no stream
  (iPhone .MOV, VITALICIO, C-PRO I rebuild) → o ffmpeg autorrota, **sem transpose**. 3840×2160 com
  retrato deitado sem metadado, ou rotação só a nível de pacote (PERPETUOS, ANBIMA, MARE, FinCap L3,
  MISSÃO CPA) → **`transpose=1`** (`transpose=2` sai de cabeça pra baixo).
- **Scribe em 48 kHz** — transcrever em 16 kHz derrubou takes limpos (MARE #11/#12).
- **Cauda comprimida do Scribe:** conferir o fim real de cada frase com `silencedetect` antes de
  fechar o range (senão o corte decepa o áudio e a legenda some antes).
- **Seleção de take**, nesta ordem: olhando pra câmera (cabeça baixa = ensaio) → fiel ao roteiro →
  sem bastidor. Errou-e-recomeçou = descarta a passada inteira. **Esquete proposital fica**,
  blooper/direção sai. Slate falado ("Script N, empresa/neutro/só voz") = vários criativos na bruta.
- **Roteiro × bruta:** conferir antes de cortar (já veio doc de outro lote); nº do arquivo ≠ ordem.
- **VSL:** +1 s de "gordurinha" no fim (handle de remontagem, idle contínuo).

---

## 3. Regra dos lotes — UM VÍDEO POR VEZ

Quando o usuário passa vídeos em lote (ex.: pasta `input/CPA/`):

- **Roteiro único → um de cada vez, do início ao fim** (as 2 versões + motion 100% aprovado),
  e só então o próximo. **Não** renderizar o lote em paralelo — cada vídeo tem roteiro próprio e
  o motion precisa ficar perfeito individualmente.
- **Exceção — lotes COMBINATÓRIOS podem ir em paralelo:** quando é a **mesma edição por parte,
  recombinada** (ex.: 2 hooks × 6 corpos = 12; cada parte é editada 1 vez, só as junções mudam).

Critério: *roteiro único → um por vez* vs *mesmas partes recombinadas → paralelo*.

---

## 4. Transição nos cortes — ZOOM `seam` é o PADRÃO

Motor **ffmpeg** (transformar footage é território do ffmpeg; HyperFrames seria pesado/lossy).
Ferramenta: `zoom_concat.py` (cópia local por projeto; reaproveita `render.extract_all_segments`).

```powershell
# de dentro de projects\<nome>\edit
python zoom_concat.py --mode seam --hold 0.12 --zoom-t 0.14 --start-dir in --out base_zoom_seam.mp4
# fontes DV/HLG já viram master SDR antes; rodar com VIDEO_USE_FPS=30 (ver seção 6)
```

- Níveis de zoom **alternam segurados**: começa zoom (1.12) → 1º corte volta ao normal (1.0) → alterna.
- Transição entre níveis é **monotônica** (um sentido só), **centrada no corte**, com ease de
  **velocidade máxima NO corte** (acelera chegando / desacelera saindo) → mascara o salto sem "ir e voltar".
- **Corte seco (xfade=0):** a legenda **precisa** vir de `hf_subs.py --crossfade 0` (offsets diferentes).

**Rejeitado, não repetir:** `--mblur` (motion blur → efeito fantasma/double-exposure); modos
`static`/`smooth`/`cut`/`masked` (jump seco, ou "ir e voltar"). O efeito **rende com MUITOS cortes**
(refs cortam a cada 1–2s); em vídeo de poucos cortes o **crossfade 130ms** (opção antiga do `render.py`
com `crossfade_s` no edl + `hf_subs.py` **sem** `--crossfade 0`) pode fazer mais sentido.

---

## 5. Legenda karaokê — preset padrão (`hf_subs.py`)

Legenda padrão do processo. Frase centralizada e estável; cada palavra "acende"
(apagada→preto, opacity 0.4→1) no instante real falado (karaokê word-synced); quebra balanceada
(DP) sem palavra órfã e sem terminar linha em preposição/conjunção; sem sobreposição entre cues.

- **Gerador:** `helpers/hf_subs.py` — constrói as cues direto do `edl.json` + transcripts (tempo por
  **palavra** na timeline de saída). Presets `vertical` / `landscape` (mesma geometria do `round_subs.py`).
- **Fundo (padrão adotado 2026-07-06):** caixa branca **translúcida** — `--box-alpha 0.3` (era 0.5).

```powershell
# 1) gerar a composição a partir do edl.json (corte seco => --crossfade 0)
python "$HELPERS\hf_subs.py" --edl edit\edl.json --out-dir edit\hf\subs-animated `
   --duration <dur do base> --preset vertical --crossfade 0 --box-alpha 0.3
# 2) validar + renderizar overlay transparente (~10 min)
cd edit\hf\subs-animated
& "$HELPERS\hf.ps1" lint
& "$HELPERS\hf.ps1" render --format webm --fps <fps> --quality high -o ..\subs-animated.webm
# 3) compor sobre o base + loudnorm  (FORÇA libvpx-vp9 no input do webm)
python edit\hf\compose_hfsubs.py     # -> output/<nome>.mp4
```

> **CRÍTICO:** ao compor overlay `.webm`, forçar o decoder `libvpx-vp9` no input — o decoder VP9
> **nativo** do ffmpeg descarta o alpha (cobre o vídeo de preto):
> `ffmpeg -i base.mp4 -c:v libvpx-vp9 -i overlay.webm -filter_complex "[0:v][1:v]overlay=0:0:format=auto" ...`

**Verificar antes de fechar:** snapshot num instante de fala (karaokê parcial) **e** num instante
de fronteira entre cues (deve ficar vazio = sem dupla legenda).

Alternativa rápida (sem os ~10 min de render): `round_subs.py` (estática arredondada, mesma estética).

---

## 6. Fontes Dolby Vision / HLG → SDR (não lavar as cores)

Celular grava **DV profile 8 + HLG (bt2020)**. A conversão "solta" **lava as cores / estoura os
brancos**. Criar um **master SDR** do vídeo inteiro ANTES do pipeline, com a cadeia correta:

```
zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=100,
tonemap=tonemap=hable:desat=0,
zscale=t=bt709:m=bt709:p=bt709:r=tv,
format=yuv420p,scale=1080:1920:flags=lanczos
```

```powershell
ffmpeg -i src -vf "<cadeia acima>" -c:v libx264 -crf 16 -g 30 -keyint_min 30 -c:a aac -b:a 192k master_sdr.mp4
```

- `npl=100` + hable + gamut correto = cores ricas e fiéis ao bruto. (`npl=203` = brancos um tico
  menos estourados; **sem tonemap** = saturadão/errado, não usar.)
- O ffmpeg **auto-aplica a rotação** (não usar `-noautorotate`): stored 3840×2160 + rot −90 vira
  2160×3840 → `scale 1080:1920` sem distorcer.
- Depois: `edl.json` aponta pro master, `grade:null` (não re-tonemapar), roda o resto com `VIDEO_USE_FPS=30`.

---

## 7. Versão SPLIT (e demais formatos com motion)

Topo = talking head reenquadrado por rosto; embaixo = motion graphics (fundo preto) sincronizado
com a fala; legenda karaokê **branca sólida** na divisória.

### 7.1 Reenquadramento do topo por rosto (`facecrop.py`)
A footage varia (a pessoa anda / a câmera dá zoom) → **crop fixo NUNCA serve**. Usar o rastreio de rosto:

- `edit/hf/facecrop.py` + modelo **YuNet** (`yunet.onnx`, do opencv_zoo). Detecta rosto por frame,
  rejeita outliers, interpola frames sem face, suaviza forte (mediana + média móvel) e recorta uma
  "câmera virtual" **1080×960** que mantém o rosto no mesmo tamanho/posição o vídeo todo.
- Params-chave: `TARGET_FACE_FRAC=0.26`, `FACE_CY_FRAC=0.42`, `SMOOTH_POS=41`, `SMOOTH_ZOOM=71`.
- Uso: `facecrop.py base_zoom_seam.mp4 yunet.onnx top.mp4` → re-encoda com `-g 30`.
- **YuNet quebrado no OpenCV 5.0.0** (retorna 0 faces): fallback via **onnxruntime** com decoder
  manual — `projects/CPA_1/edit/hf/yunet_ort.py` (strides 8/16/32, score=sqrt(cls*obj)).

### 7.2 Etapa-gate OBRIGATÓRIA — MOTION-PLAN
O motion referencia o que está sendo dito → **não se automatiza**. Antes de codar/renderizar:

1. Transcrição pronta → rascunhar o **`motion-plan.md`** inteiro (1 linha por cena):
   **# · Tempo (start→dur, casado com a fala) · Fala (gatilho) · Kicker · Gráfico · Headline
   (palavra-destaque) · Sub · Cor**.
2. Gerar **preview visual** dos gráficos de cada cena (mockup dos ícones) pro usuário ver **antes**.
3. Usuário edita/aprova — foco na coluna **Gráfico**.
4. Aprovado → construir o `split/public/index.html` seguindo o plano.

**Narrativa por cor:** rosa = problema → verde = solução/confiança → ciano = CTA.

**Avaliar pela IDEIA, não pela frase literal (regra adotada 2026-07-13):** ao escolher o Gráfico de
cada cena — seja no rascunho inicial ou num upgrade de ícone depois —, pensar no **sentimento/ideia
que aquele trecho quer passar**, não ilustrar a frase falada palavra por palavra. Ex.: "sua vida não
muda" não pede uma engrenagem qualquer girando — pede algo que capture a **sensação de estagnação**
(uma roda de hamster correndo sem sair do lugar acerta muito mais essa ideia); "você consegue" não
pede um boneco genérico subindo escada — pede a sensação de **conquista/esforço reconhecido** (um
executivo de terno chegando ao topo da curva de sucesso). Antes de aceitar o primeiro ícone óbvio
que combina com as palavras, perguntar: "isso realmente transmite o que esse momento do vídeo quer
fazer o espectador sentir?". Ao buscar um asset de personagem pra isso, checar **LottieFiles e
Flaticon** (`flaticon.com/animated-icons` — usar o `Claude_Browser`, não o `claude-in-chrome`, que
bloqueia esse domínio) — ver 7.3.1.

### 7.3 Qualidade dos gráficos = flat-vector à mão (PADRÃO)
- Estilo "sticker": **cores chapadas + contorno grosso escuro** (`#241536`, stroke ~2.6–3 num
  viewBox de 100), estética de mascote flat. É o **ativo de produção** e a baseline de comparação.
- Para ilustração pronta, usar icon sets **MIT/CC** (ex.: **Tabler Icons**, MIT) recolorido —
  **nunca** imagem de banco com marca d'água.
- **IDLE (padrão):** os gráficos **não podem congelar** após a entrada. Cada cena tem um respiro
  sutil (`idle(id, at, endt)`: flutua `y:-6, scale:1.04, sine.inOut, yoyo`) rodando por baixo das
  animações-hero pelo resto do trecho.
- Melhoria futura (opcional): geração por IA (Hera/Kling/Firefly) — **hoje não é pendência**,
  só entra se validarmos melhor uma das ferramentas.

### 7.3.2 Direção visual e variedade de composição (PADRÃO, adotado 2026-07-30)

- **Referência aprovada:** `projects/IMG_5051/edit/hf/split/public/index.html`, com render final em
  `output/IMG_5051/IMG_5051_split.mp4`. Esta versão passa a ser a referência visual oficial para
  novos splits.
- **Acabamento:** usar ilustração editorial financeira completa, com personagem/objeto principal,
  cenário em profundidade, base, textura e detalhes secundários. Evitar ícone isolado ou line-art
  simplista como arte principal.
- **Paleta — coesão POR CENA, não paleta única no vídeo (regra do usuário, 2026-07-30):** o que
  importa é que **dentro de cada cena as cores não distoem** — personagem, objetos, fundo, headline,
  textos auxiliares, cards, brilhos e partículas pertencem todos à mesma família cromática **daquela
  cena**. A **paleta PODE mudar de uma cena para a outra** (petróleo/creme/dourado é só um exemplo de
  paleta de cena, não a paleta obrigatória do vídeo inteiro). Ou seja: cada cena escolhe sua paleta e
  a mantém coesa; o vídeo não precisa ser monocromático de ponta a ponta.
- **Hierarquia cromática dentro da cena:** cada cena mantém uma cor de fundo/estrutura, uma cor de
  conteúdo principal e uma cor de acento — todas da paleta escolhida para aquela cena. Cores originais
  de assets externos não têm prioridade sobre a paleta da cena; recolorir/filtrar o que destoar.
- **Validação de cor:** revisar frames reais de **todas** as cenas depois da renderização. Uma cena só
  está aprovada quando personagem, objetos, fundo, headline, textos auxiliares e cards da CENA parecem
  pertencer ao mesmo sistema visual — sem uma cor isolada brigando com o acento **daquela cena**
  (entre cenas, a paleta pode variar de propósito).
- **Cards:** nunca cobrir rosto, mãos, objeto principal ou percurso da animação. Posicionar cards
  fora da silhueta e validar todos os estados relevantes em contact sheet, não apenas um frame.
- **Cantos limpos:** não exibir códigos técnicos, numeração gigante, labels de sistema ou marcas de
  registro nos cantos. O acabamento deve parecer peça final, não tela de diagnóstico.
- **Respiro da divisória:** manter distância visual clara entre a legenda da divisória e o primeiro
  elemento do motion. Distribuir o conjunto mais abaixo na faixa, evitando conteúdo grudado no topo
  e grande vazio sem função na base.
- **Variedade obrigatória:** não repetir `motion à esquerda + texto à direita` em todas as cenas.
  Alternar pelo menos três arranjos ao longo do vídeo quando a quantidade de cenas permitir:
  `arte esquerda/texto direita`, `texto esquerda/arte direita`, composição central/empilhada ou
  composição diagonal/assimétrica. Nunca repetir o mesmo arranjo por mais de duas cenas consecutivas.
- **Motion coerente com o layout:** entradas devem acompanhar o lado de origem da arte/texto; não
  espelhar apenas o CSS mantendo a animação vindo da direção errada.

### 7.3.3 Base cinematográfica Flow/Veo + acabamento HyperFrames (PADRÃO OPCIONAL, adotado 2026-08-03)

Quando a cena pede metáfora, ambiente, pessoa, emoção ou profundidade cinematográfica, o Flow/Veo
pode gerar a **base sem texto**. O HyperFrames continua obrigatório para headline, kicker, números,
badges, CTA, identidade, sincronização e movimentos editoriais. O teste aprovado é
`output/FLOW_TEST_IMG5051/TESTE_A_FLOW_BASE_HF.mp4`.

- **Uma base por cena, dois destinos:** gerar uma vez em 9:16 e reutilizar no split e no faceless.
- **Split:** reenquadrar a base para 1080×960; o talking head continua no topo. Preferir crop quando
  o assunto central tolera a faixa; caso contrário, usar portrait central + preenchimento desfocado.
- **Faceless:** usar a mesma base full-frame 1080×1920, com grade/scrim e copy editorial responsiva.
- **Nunca pedir texto ao Flow:** prompts devem conter `no letters, no words, no numbers, no captions`.
  Toda informação legível é responsabilidade do HyperFrames.
- **Áudio do Flow é descartado.** Voz, legenda, trilha e SFX continuam vindo do pipeline local.
- **Normalização obrigatória:** 1080×1920, 30 fps, SDR/yuv420p, GOP 30 e duração da cena. A fonte
  atual sai em 720×1280, 24 fps e 8 s.
- **Duração:** no piloto, uma geração de 8 s pode ser desacelerada para a duração da fala. Se uma
  cena acima de 10 s parecer arrastada, dividir em duas bases; não usar loop visível nem cauda congelada.
- **Gate permanece:** o `motion-plan.md` é aprovado antes da geração. Acrescentar `Tratamento` com
  `FLOW_BG_HF_OVERLAY` para cenas Flow e manter as demais como `HF_EDITORIAL`, `LOTTIE` ou `STOCK_BROLL`.
- **Consistência:** se Flow entrar em uma cena, avaliar o patamar de todas as cenas. A base pode mudar
  de paleta por cena, mas copy, grid, tipografia, margens e comportamento de entrada permanecem no
  sistema do vídeo.
- **Rastreabilidade:** salvar prompt, modelo, arquivo bruto e normalizado por cena. Convenção:
  `incoming/NN.mp4`, `prompts/NN-*.txt`, `generated/NN-normalized.mp4` e manifest JSON com timing/copy.

Scaffold e contrato: `_scaffolds/flow-hybrid/`. Piloto completo em preparação:
`projects/FLOW_TEST_IMG5051/full-manifest.json`.

### 7.3.1 Upgrade de ícone → animação de personagem real (PADRÃO, adotado 2026-07-10)
Quando um ícone representa uma **pessoa/personagem** (não um objeto abstrato como lupa, chave,
cursor) e hoje só pulsa/balança como imagem estática, o upgrade é trocar por uma animação real
de personagem, buscada em:
- **LottieFiles** (busca por tema, ex. "person typing", "hamster wheel", "climb stairs to success").
- **Flaticon** (`flaticon.com/animated-icons`) — adicionado como segunda fonte em 2026-07-13.

**Checklist de triagem antes de baixar (aprendido em [[lottie-b3-runner-investigation]]):**
1. **Movimento real por frame** — checar `ks.p/r/s/o` com `a:1` (keyframed) nas layers, não só um
   frame estático repetido. Ferramenta rápida: extrair 2-3 frames via canvas e comparar (dump real,
   não confiar em memória de um scrub anterior — ver [[feedback-thorough-debugging]]).
2. **100% vetor** (`ty4`/shape layers), **sem `assets` de imagem** (`ty2`/PNG) — assets baseados em
   raster exigem recolorir pixel a pixel, não vale o esforço pra um ícone pequeno.
3. **O estilo sobrevive a recolorir pra um tom só?** Se o personagem já usa **contorno escuro**
   separando as formas (como o resto dos ícones da casa), recolorir fill→cor de acento e
   stroke→`#241536` funciona bem. Se o personagem usa **blocos de cor adjacentes sem contorno**
   pra se diferenciar (ilustração "flat" comum), recolorir tudo pra um tom vira uma mancha
   ilegível — nesse caso **manter as cores originais** do asset (funcionou bem no CPA_1 cena 7:
   executivo de terno mantido em cores naturais, só a cor do prop/fundo precisa combinar com o
   acento da cena).
4. **O tom/estilo do personagem combina com o assunto do vídeo?** (regra adotada 2026-07-15, ver
   [[feedback-lottie-tone-match]]). Passar nos 3 critérios técnicos acima não basta — um mascote
   fofo/infantil (bichinho, monstrinho de olho só) destoa de conteúdo sério de banco/certificação/
   mercado financeiro, mesmo com movimento e vetor perfeitos. Antes de baixar, **olhar o preview
   visual** do asset (não só o JSON) e perguntar: isso pareceria bem numa VSL de investimento/prova/
   certificação? Preferir ilustração adulta semi-realista ou flat corporativa (executivo de terno,
   formando de beca, pessoa relaxando numa cadeira, estudante estudando, dupla de atendimento com
   headset/telefone) — não mascotes ou personagens "app infantil".

**Consistência de qualidade dentro do mesmo vídeo (regra adotada 2026-07-15, ver
[[feedback-consistent-motion-quality]]):** NUNCA elevar só 1 cena de um vídeo a Lottie real
deixando as demais no ícone flat-vector simples de sempre — isso faz a cena elevada destoar
das outras (uma parte muito simples, outra muito complexa). Ao fazer um upgrade de motion,
avaliar e elevar **TODAS as cenas do vídeo juntas, no mesmo passe**: a(s) cena(s) que
representam pessoa/emoção ganham o personagem Lottie real; todas as outras ganham reforço de
motion secundário equivalente (shine sweep, burst de destaque/conquista, sparkle, ponto
viajante numa trilha, anel de impacto) pra ficarem no mesmo patamar de produção — nunca deixar
uma cena "nua" ao lado da cena-hero.

**Integração (técnica validada, reusar sempre):** pré-renderizar cada frame do Lottie num
`<canvas>` durante um setup **assíncrono** (serializar SVG → `Image` → `canvas.drawImage`), só
registrar `window.__timelines[id]` **depois** do preload terminar, e desenhar no canvas visível via
`onUpdate` do GSAP **sincronamente** (sem ffmpeg nenhum de composição — é isso que resolve a classe
de bug "Lottie não pinta no capture do HyperFrames"). Helper reusável
`preloadLottieFrames(animationData, w, h)` — copiar de `projects/teste1/edit/hf/split/public/index.html`
pro projeto novo. Se a animação for mais curta que a cena, tocar em loop contínuo (`% period`); se
for do tamanho da cena, tocar direto pelo tempo decorrido (sem loop).

**Já aplicado em:** teste1 (4 ícones: pessoa trabalhando, hamster na rodinha, corredor, halterofilista)
e no lote CPA inteiro (CPA_1 a CPA_5 — executivo escalando, formando comemorando, cara relaxando
na cadeira, estudante estudando pra prova, dupla de atendimento acenando). Ver
[[lottie-b3-runner-investigation]] e [[cpa1-motion-upgrade-test]] pra receita completa e ciladas
já mapeadas.

**Ciladas de GSAP/SVG a evitar (aprendidas 2026-07-15, ver [[gsap-fromto-immediaterender-bug]]):**
1. **`fromTo` com "from" visível vaza pro resto da timeline.** Um burst/flash feito como
   `tl.fromTo(id, {opacity:1,...}, {opacity:0,...}, tempo)` renderiza o `opacity:1` (o "from")
   durante **todo o tempo antes** de `tempo`, não só no instante do flash — porque a timeline,
   quando buscada pra um `t` anterior ao tempo do tween, usa o "from" como o estado de progresso 0.
   Se o "from" for uma **saída do estado natural/oculto do elemento** (não o próprio default),
   sempre adicionar `immediateRender: false` nos vars. `fromTo`s cujo "from" JÁ É o estado
   natural/oculto (ex. os helpers padrão `kickIn`/`gIn`/`headIn`, ou um pop-in `{scale:0.3,opacity:0}`)
   não precisam disso. Verificar sempre com contact sheet **antes** do tempo marcado do tween, não
   só depois — o bug só aparece scrubando pra um momento anterior ao flash.
2. **Anel/pulso circular via `scale`+`svgOrigin` num `<g>` pode ficar não-concêntrico.** Um
   "ripple" feito como `<g><circle .../></g>` animado com `scale` + `svgOrigin:'cx cy'` já
   renderizou deslocado do centro real (efeito Venn-diagram, não um pulso concêntrico). Pra
   ripple/pulso num círculo, **animar o atributo `r` do próprio círculo diretamente**
   (`attr:{r: novoValor}`) em vez de escalar um `<g>` — imune a esse problema porque `cx`/`cy`
   nunca mudam. O padrão `scale`+`svgOrigin` continua ok pra burst de LINHAS ao redor de um ponto
   (sem um raio único pra animar).

### 7.4 Legenda da divisória + SFX
- Legenda **sólida** na divisória: `hf_subs.py --crossfade 0 --box-bottom 1035 --box-alpha 1.0`.
- **SFX (padrão só nos splits por ora):** `hf/sfx_mix.py` + `hf/split/sfx.json` (mapa de cues
  `[{t,file,gain,nota}]`). Biblioteca local em `hyperframes-media/assets/sfx/*.mp3`. Cada cena tem
  seu **acento** ligado ao ícone (pop/chime/click/impact/sparkle/riser). **Whoosh de troca de cena
  raleado**: ~2–4 por vídeo (1 a cada ~3 trocas), não em toda troca. O SFX é etapa separada
  (dá pra refazer sozinho sobre o `split_with_audio.mp4`).

### 7.5 Montagem final do split
`top.mp4` (topo, sem áudio) + motion (baixo) → render → **muxar áudio −14** do `base_zoom_seam`
(o render sai sem áudio) + **overlay da legenda webm** (forçar `-c:v libvpx-vp9`) + SFX, num passe.
→ `output/<nome>_split.mp4` (já inclui SFX).

### 7.6 FACELESS — formato-opção (padrão EDITORIAL cravado 2026-07-30)

Vídeo **100% SEM talking head**. **Híbrido:** cenas-conceito viram **ilustração editorial** (mesmo
sistema do split, §7.3.2) e cenas de pessoa/emoção/mercado viram **b-roll cinematográfico**. É
opção de formato (não obrigatória) — perguntar por lote (§0).

- **Sistema de cada cena de motion** (idêntico ao split, mas **full-frame 1080×1920**): `.disc`
  (plataforma circular) + **personagem Lottie recolorido por `filter` CSS** (reusar climbstairs/
  graduation/exam/manworking/wave de `IMG_5051/edit/hf/split/assets/`) OU **ilustração SVG autoral**
  desenhada na paleta (barras, pizza, chave, selo, moedas, relógio, chat, hub-and-spoke…),
  preenchendo o disco (`.artsvg` 476×476, centrado); + **3 badges** rotulados flutuando + copy
  (kick / headline Arial Black com palavra-acento / sub); ambiente atmo + grid + grain + vig. Bloco
  centralizado com respiro arte↔texto (`.wrap{justify-content:center}` + `.copy{margin-top:150px}`).
- **Cenas de b-roll:** vídeo full-bleed + `.bgrade` (scrim) + `.bcopy` (kick/headline/sub no rodapé).
  Pool grátis Pexels/Pixabay/Mixkit/Coverr (uso comercial, sem atribuição); **b-roll SEM ken-burns**
  (footage estático — o zoom foi rejeitado).
- **Cor:** coesão POR CENA, paleta muda por seção narrativa (§7.3.2). Classes prontas:
  `.pal-warm / .pal-mint / .pal-cyan / .pal-azure / .pal-rose` (cada uma define ~14 CSS vars incl.
  `--charf` = filtro do personagem).
- **Idle** (§7.3): a arte flutua, nunca congela. **Timings** reusados do `faceless-broll/` antigo
  do projeto (data-start/duration por cena) — não re-transcrever.
- **CILADA (aprendida 2026-07-30):** nunca animar `x`/`y` num `<g transform="translate()">` — o GSAP
  vira matriz e **apaga o translate**, jogando a figura pro topo do viewBox. Usar **coordenadas
  absolutas**; `scale` puro (sem x/y) e `scale`/`rotation`+`svgOrigin` são seguros (ver §9).
- **Montagem final:** render (sem áudio) → **overlay `subs-divider.webm`** (`-c:v libvpx-vp9`, offset
  por projeto: CPRO 680 / IMG_5055 660 / CPA 600) + **muxar áudio −14** do `base_zoom_seam` (mutar
  foley pré-fala se houver, ex. CPA_1 `volume=0:enable='lt(t,2.65)'`). Um passe.
- **Scaffold reutilizável:** `_scaffolds/faceless-editorial/` — framework externo
  (`framework.css` + `framework.js` com `window.HF.{frames,player,wordSplit,timeline,enter,benter,idle,charLoop,cta}`),
  vendor, fontes e os 5 personagens Lottie já prontos, + `index.html` template (cenas de exemplo) e
  `COMO-USAR.md`. **Copiar essa `public/` pro projeto e editar SÓ as cenas + o script curto de timeline**
  (o framework NÃO se reescreve — economia grande de tempo/tokens; carregamento externo validado no
  render do HF). Referências: `output/TESTES/{CPRO_1,IMG_5055,CPA_1}_faceless_editorial.mp4`.
  As versões antigas `_faceless_broll.mp4` (radar/neon multicor) viraram **histórico**.

#### 7.6.1 FACELESS — arquitetura shot-sequence / blueprint (PADRÃO ÚNICO, cravado 2026-08-20)

**Reconciliação 2026-08-20:** o faceless passou a ser regido pela arquitetura **shot-sequence** do
sistema Codex (`_codex/video-system/` + `prompts/CODEX_EDITING_STANDARD.md` §6), que é mais nova e por-frame.
O antigo **"v2 pôster vertical" virou LEGADO/fallback simples** (nota no fim).
**Referência de vídeo VIVA** = `output/TESTES/C0207_faceless_V7_2_cyan.mp4` (25fps; corredor do Frame 1
recolorido magenta→ciano `#22d3ee` p/ fechar a paleta, validado quadro a quadro 2026-08-20; a
`_V7_1_timing_preview.mp4` é a anterior, corredor magenta); projeto-exemplo completo em
`_codex/validation/C0207/faceless-v7-rebuild/`
(STORYBOARD.md + frame.md + `compositions/frames/*.html`). **Referência editorial de ritmo** = o CPRO_1
(o MP4 `CPRO_1_faceless_editorial.mp4` **não existe mais**; sobrou como still/contact-sheet em
`_codex/reference-analysis/faceless/` + `_codex/validation/reference_audit/CPRO_1_faceless_editorial-reference.jpg`).

- **Nada de template fixo — cada frame é uma SHOT-SEQUENCE.** O frame se divide em **3–4 cenas
  cronometradas (Scene 1→4)** que se desenvolvem pela duração inteira; **nenhuma cena congela após a
  entrada** e **nenhuma começa vazia** (sujeito principal legível ≤0.5s). A composição de cada frame é
  escolhida pela **intenção da fala** (pôster tipográfico / diagrama / progressão / comparação / b-roll)
  — **uma ideia dominante por frame**.
- **Blueprint por frame:** `video-text-pivot`, `grid-card-assemble`, `cta-morph-press`, `compose`
  (b-roll). O reveal é **semântico**: cada peça de apoio entra **na palavra correspondente** da fala.
- **Ritmo `impact-build-proof-cta`** — pico no beat de **prova**; **mudança visual a cada ≤5s**.
- **Gramática visual por família** (`presets/visual-grammar.json`): `certification` / `career` /
  `urgency` / `difficulty`, cada uma com conceitos + componentes (`timeline`/`checklist`/`progress`/
  `metric`/`comparison`/`alert`/`cta`) + lista de **avoid** (mascote, casino/sinuca, horror-literal,
  neon-game, e o **cartão descartado `CPA 20 / CERTIFICAÇÃO ATUAL / RETA FINAL`** — proibido em todos os formatos).
- **Zonas seguras faceless** (`presets/formats.json`): `contentZone` x70 y100 **940×1430**;
  `captionZone` **safe-base y1580–1770**. Preencher o **topo ~83%**; hero entre **y260–1050**, apoio
  **y1080–1450**. Legenda pill inferior, no máx. 2 linhas, 1 palavra ativa ciano/amarela — **nunca**
  cobre o hero nem labels; nenhum texto de motion invade a faixa da legenda.
- **Motion direcional e proposital** (verbos): `assemble` · `route` · `accumulate` · `stamp` · `morph`
  · `press`. **Todo elemento tem entrada, desenvolvimento OU idle — nada congelado.**
- **Transições:** entre frames o corte é **hard-cut de propósito** — a continuidade mora **DENTRO** da
  shot-sequence, não na emenda. *(Isto SUBSTITUI a antiga regra "corte seco proibido": a v2 punia o corte
  porque os frames eram estáticos; com a cena viva de ponta a ponta, o corte fica limpo.)* `zoom seam`
  segue válido quando o conteúdo pede continuidade visual.
- **Arte:** **Lottie profissional** nos movimentos humanos e no CTA; **HTML/SVG só** p/ interfaces,
  calendários, tipografia e dados. **B-roll só onde é semanticamente necessário** (ex.: "meses
  estudando"), sob **grade escura** + movimento sutil. Proibido: mascote/infantil, ícone genérico não
  relacionado, SVG improvisado/provisório (vale o tom, §feedback-lottie).
- **Paleta/tipo de referência** (`frame.md`): canvas `#07131f`, ciano `#22d3ee` / verde `#34d399`,
  **amarelo `#fbbf24` só p/ deadline, CTA e 1 ponto de ênfase**; Display Arial Black uppercase,
  hero 92–150px, copy visível curta (uma claim / um número / um status por reveal). Sem header no topo,
  sem faixa amarela lateral.
- **Infra + QA:** manifesto `codex-video.json` (a partir de `templates/codex-video.example.json`) →
  `node _codex/video-system/qa/video-qa.mjs <manifesto>` (corrigir TODOS os erros) → snapshots das
  mudanças de cena → render 1080×1920 preservando fps → remux/mix de áudio + `ffprobe`. **Snapshot é
  flaky com Lottie** (validar cena de personagem no render). Entregar `_REVIEW`, nunca sobrescrever aprovado.
- **B-ROLL = opção validada (2 variantes: motion-puro OU motion+b-roll).** Intercalar 1–2 cenas de
  footage editorial nos beats de emoção/pessoa (não nos de dado). Receita: clipe do pool grátis
  (`_codex/.../assets/*.mp4` etc., reuso sem download), **`<video class="clip">` no nível do `index`**
  (1º no DOM = camada de baixo) + o frame de gráficos como **overlay transparente** (`#root{background:
  transparent}`, grade escura só na base + lower-third) — vídeo dentro de sub-composição sai PRETO (§9).
  Legenda karaokê pode ser **embutida** (`compositions/captions.html` lendo `assets/cues.js`, seek-safe
  com `tl.set`) em vez de overlay webm. Refs: `output/TESTES/FINCAP2_R3_faceless_broll.mp4` +
  `VIT_H1_D1_F1_faceless.mp4` (testes 2026-08-24). **Cortar erro de locutora:** o defeito pode ser a
  ENTREGA (rindo/hesitação — Scribe marca `[riso]`/`audio_event`), não a palavra; cortar em silêncio
  dos 2 lados + `acrossfade qsin` e RE-TRANSCREVER o áudio corrigido p/ cues limpos.

> **LEGADO — FACELESS v2 "pôster vertical" (cravado 2026-08-03, agora fallback simples):** template fixo
> `.rail` (copy alto-esquerda + arte centrada + karaokê base), ref `output/TESTES/CPA_1_faceless_editorial.mp4`.
> Usar só quando um shot-sequence completo não se justificar. **Cilada de GSAP que continua valendo em
> geral:** arte centrada em `left:50%` precisa de **`xPercent:-50` no `from` E no `to`** — animar `x`/`scale`
> sem isso vira matriz e mata a centragem (mesma família da cilada do `<g translate>`).

> **Fronteira Codex ⇄ Claude:** o `prompts/CODEX_EDITING_STANDARD.md` proíbe sincronização automática com este
> README. Esta seção **adota** a arquitetura do lado Claude; **não** edito o doc do Codex por conta —
> só o usuário altera aquele arquivo.

---

### 7.7 TRILHA + SFX — padrão-com-gate (promovido 2026-08-03)

Camada de áudio sutil por cima do final validado. **É formato PADRÃO** (§0, item 3), mas
**cada aplicação passa por GATE:** confirmar que **tipo + "vibe"** da trilha combinam com aquele
conteúdo antes de gerar. Sério/institucional (banco, certificação) pede pad calmo; se a trilha
soar animada/pop/muzak ou brigar com a fala, **não entra** — mostrar/perguntar na dúvida.

- Saída: `output/<nome>_trilha.mp4` **ao lado** do final, **sem tocar** no áudio validado.
- **Vibe:** corporativo calmo SEM música de elevador — tríades simples soam muzak; usar voicings
  com **7ª/9ª** (Am7·Fmaj7·Cadd9·G6) + linha esparsa tipo **celeste/caixinha** (poucas notas com
  decaimento+reverb). Fala SEMPRE manda.
- **Nível:** pad ~0.60 antes do ducking (o quase-subliminar inicial NÃO serviu).
- **SFX:** 2 whooshes leves por vídeo em cortes de cena (~1/3 e ~2/3), `whoosh-short.mp3` vol 0.26.
- **Fonte:** pad **sintetizado por ffmpeg** (livre de licença) — HeyGen catalog exigiria auth do CLI
  (instalado, não autenticado; NUNCA manusear a API key do usuário). Receita ffmpeg completa em
  `[[audio-bed-trilha-option]]` (memória): pad `aevalsrc`+`acrossfade`+`chorus`, topline plucks
  `adelay`+`aecho`, mix `sidechaincompress` + whooshes + `afade`/`alimiter` → ~−14 LUFS.

---

## 8. HyperFrames — ambiente e regras

Renderiza vídeo a partir de HTML. **Integrado como camada visual** (legenda karaokê, split motion,
intro/outro, lower-thirds, data-viz).

> **REGRA (atualizada 2026-07-21):** o HyperFrames **pode ser usado sempre que a edição precisar de
> um motion / gráfico / animação / overlay** — não é mais restrito a "só quando pedido explicitamente".
> Quando uma cena/frase ganha com motion (critérios da §7.2 avaliar pela ideia e §7.3.1 elevar todas
> as cenas no mesmo patamar), gerar o motion via HyperFrames faz parte do fluxo normal, sem autorização
> caso a caso. O pipeline base (transcrição → edl → zoom → subs → output) continua não o invocando
> sozinho quando não há motion a fazer. *(Antes: "nunca gera nada automaticamente" — REVOGADO.)*

- **Ambiente (ok):** Node v24+ instalado (onde o instalador o colocou, ex.: `C:\Program Files\nodejs`;
  costuma ficar **fora do PATH da sessão** — por isso o wrapper abaixo), Chrome de render cacheado,
  ffmpeg ok. Whisper/Kokoro/MusicGen/Docker ficam ✗ no `doctor` — **opcionais, não usados**.
- **Invocação PATH-safe:** usar o wrapper `hf.ps1` (resolve o PATH do Node), **não** `npx hyperframes` direto:
  ```powershell
  & "$HELPERS\hf.ps1" <comando hyperframes>
  ```
- `hf.ps1 lint` **antes** de todo `render`, rodando **de dentro** da pasta que tem o `index.html`
  (`public/` no split). Casar SEMPRE **resolução + fps** do projeto (mismatch = erro nº 1 no concat).
- **Versão:** o `hf.ps1` roda `npx --yes hyperframes` **sem pin** (o cache npx já tem 0.7.x e 0.8.x).
  A antiga trava em `0.7.26` (0.7.27 quebrado) não é mais aplicada. Se um render quebrar após
  atualização, fixar a versão no `hf.ps1` e registrar aqui.
- `hf.ps1 snapshot --at <t>` valida timing/layout sem render; kits com timeline em JS externo dão
  falso-positivo `missing_timeline_registry` no lint.

---

## 9. Gotchas (erros já vividos — não repetir)

- **Cue-fantasma:** ranges do edl sobrepostos em source-time → `hf_subs` conta a palavra da fronteira
  2× e gera uma cue curta (~0.08s) sobreposta atrás da legenda. **Sempre cortar em fronteira limpa**
  (`end_anterior ≤ start_seguinte`).
- **Micro-cue trava a legenda:** cue < 0.2s (ex.: "E" isolado) grudava a caixa a cena inteira.
  Corrigido no `hf_subs.py` com `MIN_CUE_DUR=0.40s`.
- **Pontuação solta:** o Scribe emite "," como palavra separada → cue começando com vírgula. O
  `hf_subs.py` funde tokens só-de-pontuação na palavra anterior e tira pontuação do início da cue.
- **Alpha preto no overlay:** decoder VP9 nativo descarta o alpha → **forçar `-c:v libvpx-vp9`** no input.
- **Cauda congelada:** overlay webm mais longo que a base faz o ffmpeg repetir o último frame →
  compor com `-t <dur da base>`.
- **Transform em SVG aninhado:** GSAP `x/y/scale/rotation` num `<g>` SVG aninhado **não renderiza**
  no capture → envolver num `<div>` HTML.
- **B-roll `<video>` dentro de sub-composição = TELA PRETA:** um `<video class="clip">` dentro de um
  frame carregado por `data-composition-src` **não decodifica** no render (sai preto). Pôr o vídeo como
  clip de **nível `index`** (primeiro no DOM = camada de baixo) e deixar o frame de gráficos como
  **overlay transparente** (`#root{background:transparent}`, sem o `<video>`) por cima. Confirmado no
  VITALICIO faceless (2026-08-24). Ordem de pintura no HF = ordem no DOM (vídeo 1º, cenas depois, legenda por último).
- **Contador seek-safe:** `tl.call(()=>n++)` num contador mutável dá número ERRADO no render (não é
  seek-safe) → usar estado por tempo: dots/dígitos com opacity via `tl.set`/tween, ou `onUpdate` lendo
  um proxy `{v}` tween. (VITALICIO/R3 faceless.)
- **Pivô do GSAP em SVG:** usar `svgOrigin:'x y'` (não `transformOrigin:'Npx Npx'`, que joga o shape
  pra fora do quadro).
- **Encoding:** rodar com `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` (senão o `→` quebra no cp1252).
- **Ilustração à mão orgânica** (mão, personagem) quase sempre sai torta — preferir icon set MIT/CC.
- **`drawSVG`** é plugin premium, **não** está no bundle GSAP do HyperFrames — não usar.

---

## 10. Projetos / lotes de referência

- `projects/IMG_5055/` — talking-head 9:16; **berço do processo** (zoom seam, karaokê, split,
  4 formatos de motion de teste em `hf/{produced,faceless,hybrid,split}`).
- `projects/C0205/` — anúncio Natal, 16:9 + 9:16 (vertical com punch-in via crop_x).
- **Lote CPA** — 5 talking-heads (sinuca / "a tacada final"), 9:16 nativo DV/HLG. **Completo 5/5**
  (padrão + split). Receita por vídeo no `cpa-batch` da memória.
- **Lote C-PRO I** — 6 criativos, **completo 6/6** (padrão + split = 12 entregáveis).
- **Lote C-PRO R** — 5 criativos, **completo 5/5** (padrão + split = 10 entregáveis).
- **Série hook×corpo** — 12 combinatórios (2 hooks × 6 corpos), karaokê só no hook.
- **C-PRO I rebuild (4 formatos pelo app)** — 6 × normal+split+hybrid+faceless = 24, QA 24/24,
  aprovado 2026-09-21: **referência de ponta a ponta do fluxo Mesa de Corte**.
- **ANBIMA** (9 × 3 formatos), **PERPETUOS** (8), **CFP** (8), **FinCapital** (Lotes 1–3 + Avulsos),
  **MARE** (30 roteiros, slate falado), **VITALICIO** (combinatório 6×3×3), **MISSÃO CPA**
  (combinatório 10×10×3 = 300, em andamento), VSLs MARE faceless sem legenda. Detalhes por lote na memória.

---

## 11. Ferramentas auxiliares (instaladas 2026-07-27)

Cinco ferramentas adicionadas ao processo. Clones em `$TOOLS` (`Desktop\claude\tools\`) — os clones
são **referência/atualização**, o que vale é a instalação. Nenhuma substitui o pipeline: elas entram
como **camadas de verificação e apoio**.

| Ferramenta | Como chamar | Onde entra |
|---|---|---|
| **claude-video** | skill `/watch` | QA do render + leitura de referência/concorrente |
| **impeccable** | skill `/impeccable`, CLI `npx impeccable detect` | qualidade de design dos HTML de motion (split/hybrid) |
| **ponytail** | skills `/ponytail`, `/ponytail-review`, `/ponytail-audit` | enxugar helpers Python e composições |
| **graphify** | skill `/graphify`, CLI `graphify` | mapa navegável de helpers + projects |
| **notebooklm-py** | skill `/notebooklm`, CLI `notebooklm` | pesquisa/roteiro a partir de fontes |

### 11.1 `/watch` — ver o vídeo de verdade (claude-video)

Antes: pra conferir um render eu extraía contact sheet na mão com
`ffmpeg -vf "select='eq(n\,330)+…'"` (dezenas de linhas dessas no histórico). **Agora `/watch` faz isso**:
baixa (URL) ou lê direto (**caminho local**), extrai frames auto-escalados, junta transcrição e
devolve os caminhos pra leitura.

```powershell
# QA de um entregável (frames cena-a-cena)
python "$env:USERPROFILE\.agents\skills\watch\scripts\watch.py" "output\ANBIMA_1_split.mp4" `
   --detail balanced --no-whisper --resolution 512

# conferir instantes específicos (substitui o select= na mão)
python "$env:USERPROFILE\.agents\skills\watch\scripts\watch.py" "output\ANBIMA_1_split.mp4" `
   --detail transcript --timestamps 0:02,0:07,0:15 --no-whisper --resolution 720

# ler uma referência do YouTube
python "$env:USERPROFILE\.agents\skills\watch\scripts\watch.py" "https://youtu.be/xyz" --detail balanced
```

- **`SKILL_DIR` = `~\.agents\skills\watch`** (o `~\.claude\skills\watch` é junction pra lá).
- **Detail:** `efficient` = keyframes (rápido, **pouco frame** — 17s virou só 4 frames, ruim pra QA);
  `balanced` = scene-aware (**padrão pro nosso QA**); `token-burner` = sem teto;
  `transcript` = sem frames (combina com `--timestamps`).
- **`--resolution 512` é o default**; subir pra **720–1024** quando o ponto é **ler texto na tela**
  (legenda karaokê, headline do motion, selo).
- **Transcrição:** rodar **`--no-whisper`**. Não há chave Groq/OpenAI configurada, e a transcrição
  oficial do processo é o **Scribe** (§2.2) — o `/watch` aqui serve pros **frames**.
- Validado em `output/intro1_final1.mp4` (1080×1920): frames saem legíveis, legenda visível.

### 11.2 `/impeccable` — qualidade de design do motion

Detector determinístico (60 regras) + comandos de design. Roda sobre os `index.html` das composições
HyperFrames — é a primeira ferramenta objetiva que temos pro **lado visual** do split/hybrid,
que hoje só é avaliado a olho.

```powershell
npx --yes impeccable@latest detect "projects\<nome>\edit\hf\split\public\index.html"
```

- **Instalado no projeto** (`$VIDEOS\.claude\skills\impeccable`) + **2 hooks** em
  `.claude/settings.local.json`: `PostToolUse` (Edit/Write/MultiEdit, 5s) e `Stop` (passe completo, 30s).
  Rodam sozinhos ao editar arquivo de UI.
- **Ignores já configurados** (`.impeccable/config.json`):
  - `low-contrast=*` em `projects/**/hf/**` — **falso positivo**: o detector assume texto `#000000`
    quando a cor vem do SVG/GSAP e compara com o palco escuro (`#0a0713`). Conferido: não existe
    texto preto nesses arquivos.
  - arquivos `subs-*/**` ignorados (composição gerada pelo `hf_subs.py`, não é design nosso).
- Depois dos ignores, o ANBIMA_1 split sobra **1 apontamento real**: `overused-font: inter`.
  É uma **escolha**, não bug — mas fica registrado como o lugar óbvio de dar personalidade se
  quisermos diferenciar a tipografia do motion.
- Comandos úteis além do `detect`: `critique`, `polish`, `typeset`, `layout`, `colorize`, `animate`.
- **Calibrado pra web UI**, não pra motion graphics — usar como **sinal**, nunca como gate de entrega.
  O gate continua sendo o **motion-plan aprovado** (§7.2) e o olho do usuário.

### 11.3 `/ponytail` — cortar over-engineering

Modo "sênior preguiçoso": questiona se o código precisa existir, prefere stdlib/nativo, uma linha
antes de cinquenta — **sem** cortar validação, segurança ou perda de dados. Serve pros helpers Python
por projeto (cópias locais que vão inchando) e pras composições.

- `/ponytail lite|full|ultra|off` — intensidade. `/ponytail-review` (diff), `/ponytail-audit` (repo inteiro).
- Instalado **só as skills** (sem os hooks de ciclo de vida) — não interfere no fluxo automaticamente.

### 11.4 `/graphify` — mapa do repositório

Grafo de conhecimento por AST local (tree-sitter, sem LLM, sem telemetria) de código + docs.
Vale pra navegar `helpers/` + `projects/` sem varrer arquivo por arquivo.

```powershell
& "$PYSCRIPTS\graphify.exe" .                       # constrói o grafo
& "$PYSCRIPTS\graphify.exe" query "onde a legenda vira webm?"
```

Saída: `graph.html` (interativo), `GRAPH_REPORT.md`, `graph.json`. `--update` re-extrai só o que mudou.

> O `graphify install` criou um **`~/.claude/CLAUDE.md` global** (3 linhas, só o gatilho `/graphify`).
> É global, não do projeto — se atrapalhar, apagar.

### 11.5 `/notebooklm` — pesquisa e roteiro

Acesso programático ao NotebookLM (fontes → perguntas com citação, podcast, quiz, mapa mental).
Entra **antes** do pipeline: pesquisa de tema e apoio de roteiro, não edição.

- **Autenticado em 2026-07-27** (`Auth ✓ pass`, 27 cookies) — sessão salva em
  `~\.notebooklm\profiles\default\storage_state.json`. Usar: `notebooklm create "..."`,
  `source add`, `ask`, `generate audio|video|quiz…`, `download`.
- **Como refazer o login (cilada mapeada):** `--browser-cookies chrome` **NÃO funciona no Windows** —
  o Chrome 127+ usa *app-bound encryption* e o `rookiepy` não decripta ("Could not decrypt chrome
  cookies", com uma mensagem enganosa sobre Keychain do macOS). O caminho que funciona abre o Chrome
  do sistema (sem baixar os ~170 MB do Chromium do Playwright):
  ```powershell
  & "$PYSCRIPTS\notebooklm.exe" login --browser chrome     # perfil limpo: pede a conta de novo
  & "$PYSCRIPTS\notebooklm.exe" doctor                     # Auth tem que virar ✓ pass
  ```
- O `doctor` avisa `Profile Dir ! warn` (permissões `0o777` vs `0o700`) — **cosmético no Windows**,
  o modelo de permissão é outro. Ignorar.
- **Ressalva do próprio projeto:** usa **API não documentada do Google**, sem vínculo com o Google,
  pode quebrar sem aviso e tem rate limit. Tratar como apoio, nunca como dependência de entrega.

### 11.6 Reinstalar / atualizar

```powershell
npx --yes skills add bradautomates/claude-video -g     # /watch
npx --yes skills add DietrichGebert/ponytail -g        # /ponytail*
npx --yes impeccable@latest install                    # /impeccable (projeto + hooks)
python -m pip install --upgrade graphifyy "notebooklm-py[browser,cookies]" yt-dlp
& "$PYSCRIPTS\graphify.exe" install --platform claude
```

> No `skills add -g`, o erro **"PromptScript does not support global skill installation"** é
> **esperado e inofensivo** — é outro harness. O que importa é a linha `✓ ~\.agents\skills\<nome>`
> com `symlinked: Claude Code`.

---

## 12. Checklist de FECHAMENTO de vídeo (rodar antes de dar por pronto)

Consolidação das regras que mais escapam sob pressa. Vale pra **cada entregável** (padrão, split,
hybrid, faceless, trilha). Não é gate automático — é a passada final consciente.

**Consistência de qualidade (a regra que mais escorrega)**
- [ ] **Todas as cenas do MESMO vídeo no MESMO patamar** de motion. Nunca elevar só 1 cena a Lottie
      real deixando as outras cruas. Se uma sobe, todas sobem (§7.3.1).
- [ ] Tom do Lottie/ilustração **combina com o assunto** — mascote/infantil destoa de banco/
      certificação. Checklist técnico (movimento/vetor/recolor) não basta.
- [ ] Take escolhida está **olhando pra câmera** (cabeça baixa = ensaio → descartar), e só depois
      fiel ao roteiro.

**Legenda**
- [ ] Karaokê **nunca cobre o rosto** (medir com YuNet; rebaixar a caixa em close/contra-plongée).
- [ ] Fim da fala não decepado — conferir a **cauda comprimida do Scribe** (`silencedetect`).
- [ ] Sem **cue-fantasma** (cortar em fronteira limpa `end ≤ start`) nem micro-cue.
- [ ] Nome da **certificação grafado certo** (Scribe erra: ANBIMA, CPRO-R, C-PRO I, CFP…).

**Motion / HyperFrames — ciladas automatizáveis**
- [ ] Rodar **`py scripts/guard_ciladas.py projects/<nome>/edit`** → 0 erros; ler os avisos e julgar.
      (Pega drawSVG premium, `transformOrigin:'Npx Npx'` em SVG, `.webm` sem `-c:v libvpx-vp9`.)
- [ ] `hf.ps1 lint` **antes** de todo render, de dentro da pasta do `index.html`; casar **resolução+fps**.
- [ ] Overlay `.webm` composto com **`-c:v libvpx-vp9`** (alpha) e **`-t <dur da base>`** (cauda).

**QA final**
- [ ] **`/watch`** no arquivo de `output/` antes de fechar (frames cena-a-cena; `--resolution 720+`
      se precisar ler texto na tela).
- [ ] **Trilha:** passou pelo GATE de tipo/vibe (§7.7)? Se destoa, não anexar.
- [ ] Entrega bate com os formatos **combinados no início do lote** (§0/§3).

---

## 13. Mesa de Corte, finalizadores e bibliotecas (consolidado 2026-09-28)

### 13.1 App Mesa de Corte — como o pedido chega
- `apps/mesa-de-corte/` — `server.py` (stdlib, **http://localhost:8756**) + `index.html`. Subir com
  `py apps/mesa-de-corte/server.py` ou `preview_start mesa-de-corte` (`.claude/launch.json`).
  É o **cockpit**: não renderiza; quem executa é a sessão do Claude Code.
- **Novo anúncio:** lane **Lote padrão** (presets Lucas/LS · FinCapital · MARE/VSL via `applyConfig`)
  ou **Edição geral** (Formato + Legenda; resto em "⚙ Opções avançadas"). Suporta trechos in/out por
  bruta, exclusões, formatos por vídeo e **combinatório** gancho×corpo×CTA (mapa de papéis editável).
- "Começar" grava `orders/<lote>.json` (fila `pendente → em_edicao → revisar → aprovado`) e emite
  `START` em `orders/_events.txt`. Aprovar → `APPROVE … proximo=<id>`; pedir ajuste → `AJUSTE … nota=`.
  Excluir pedido move para `orders/_trash/` (reversível).
- **Watcher (re-armar em TODA sessão):** Monitor persistente
  `tail -n0 -F "apps/mesa-de-corte/orders/_events.txt"`. Ao receber: avisar "recebi" na hora e dar
  status a cada etapa. Fora de sessão, a Tarefa Agendada **`MesaDeCorte-QueueNotify`**
  (`queue_notify.ps1`, a cada 5 min) só dispara balão do Windows — não produz.
- Status/saída de um item: `py apps/mesa-de-corte/set_status.py <lote> <item> revisar <saida.mp4>`.
- Abas extras: **Biblioteca de animações** (`/lib/anim/` → `_scaffolds/anim-library`) e **b-roll**
  (`/lib/broll/` + `/api/broll`, upload/edição/exclusão). `PADROES.html` = página de padrões.
- Webview do app desktop bloqueia `window.prompt/confirm` — usar formulário/modal inline.

### 13.2 Finalizadores (usar SEMPRE em vez de ffmpeg inline)
| Formato | Comando | O que faz |
|---|---|---|
| Normal | `hf/compose_hfsubs.py` (cópia do projeto) | overlay karaokê + loudnorm (sem gate) |
| Split | `py apps/mesa-de-corte/finish_split.py --edit <dir> --out <mp4>` | gate → mux voz → legenda-divisória → SFX → loudnorm |
| Hybrid | `py apps/mesa-de-corte/finish_hybrid.py --edit <dir> --out <mp4>` | gate → mux voz → karaokê → loudnorm |
| Faceless | `py apps/mesa-de-corte/finish_faceless.py --edit <dir> --out <mp4>` | gate nos frames → loudnorm |

- **Gate `check_cert.py`**: cruza a certificação esperada (nota do `edl.json` ou `--cert`) com todo
  texto do motion e barra família divergente (CPA × CPRO-I × CPRO-R × CFP × ANBIMA × CEA × CGA).
  Bypass `SKIP_CERT=1` só com motivo. Atenção: no `finish_split` o gate é *fail-open* se o import falhar.
- **QA do lote:** `py apps/mesa-de-corte/qa_lote.py <lote> [fmt…]` — duração entre formatos,
  −14 ±1,5 LUFS, frame preto, mudo, 1080×1920/~30fps. Depois `/watch` nos entregáveis.
- Os finalizadores têm `HELPERS` com caminho absoluto (`C:\Users\betat\Desktop\claude\video use\helpers`) —
  ajustar em outra máquina.

### 13.3 Kits e bibliotecas (`_scaffolds/`)
| Pasta | Uso |
|---|---|
| `split-kit/` | motion do split: copiar, `index.template.html → index.html`, editar só `SCENES[]` + durações (ILLOS com animação-assinatura) |
| `faceless-shotseq/` | **padrão faceless** (áudio → b-roll → frames → captions, karaokê embutido) |
| `faceless-kit/` | variante data-viz dirigida por `SCENES[]` (13 tipos: headline, grid, offer, checklist, cta, broll…) |
| `faceless-editorial/` | **legado** — não usar |
| `anim-library/` | 22 heroes SVG capture-safe + ILLOS + registro Lottie (`library.json`); Lottie SVG puro morre no capture |
| `broll-pool/` | 32 clipes 1080×1920 sem áudio, com tags; `pick_broll.py <tags>`, `gen_gallery.py` após mudar; sem marca/instituição real visível |
| `brand/` | logo/avatar Lucas Silva (novas marcas entram aqui) |
| `flow-hybrid/` | contrato da base Flow/Veo (§7.3.3, opcional) |

Trilha: `projects/VITALICIO/trilha.py` (moods calmo/sério/enérgico); trilha musical de aftermovie:
`projects/FINCAP_DAY2026/music_gen.py`.

### 13.4 Reproduzir em outra máquina (resolvido 2026-09-28)
- **Scripts por-projeto têm fonte canônica:** `_scaffolds/pipeline-kit/edit/` (`zoom_concat.py`,
  `hf/compose_hfsubs.py`, `hf/facecrop.py`, `hf/yunet_ort.py`, `hf/yunet.onnx`, `hf/sfx_mix.py`).
  Projeto novo: `cp -r _scaffolds/pipeline-kit/edit/. projects/<nome>/edit/`. Corrigiu? Corrija lá.
- **Sem caminho fixo:** kit e `finish_*.py` acham os helpers por `VIDEO_USE_HELPERS` ou
  `<pai de VIDEOS>/claude/video use/helpers`; SFX por `HF_SFX_DIR` ou `~/.claude/skills/...`.
- **video-use:** as nossas mudanças (patch do `render.py` + `hf_subs.py` + `hf.ps1` + commit-base)
  estão em `_scaffolds/pipeline-kit/video-use/`, com o passo a passo de instalação no README de lá.
- **Git** versiona o processo: README, prompts, scripts, `apps/mesa-de-corte` (sem `orders/`),
  `_scaffolds/*`, `_codex/video-system`, `.claude/launch.json`. Fora: mídia, `projects/`, `output/`,
  `input/`, `.env`, `split-kit/top.mp4`. **Sem remote configurado** — para backup/colega, criar um
  repositório privado e dar push. As fontes `ariblk.ttf` (Arial Black, Microsoft) não podem ir para
  repositório público.
- Biblioteca de SFX: `~/.claude/skills/hyperframes-media/assets/sfx/*.mp3` (skill `hyperframes-media`; caminho fixo no `sfx_mix.py`).
