# pipeline-kit — fonte canônica dos scripts do pipeline

Antes (até 2026-09-28) esses scripts só existiam como cópias soltas em `projects/*/edit/` (56–118
cópias cada, algumas divergentes). Esta pasta é a **versão oficial**: projeto novo copia daqui,
correção se faz aqui (e depois se copia para o projeto em andamento, se precisar).

## Conteúdo

```
edit/
  zoom_concat.py        base com transição zoom `seam` (README §4)
  hf/compose_hfsubs.py  overlay karaokê webm + loudnorm → final NORMAL (com fix `-t` da base)
  hf/facecrop.py        topo do split 1080×960 por rastreio de rosto (limiares relativos: 1080p e 4K)
  hf/yunet_ort.py       decoder YuNet via onnxruntime (o cv2 5.0 retorna 0 faces)
  hf/yunet.onnx         modelo YuNet (opencv_zoo)
  hf/sfx_mix.py         SFX de `sfx.json` + loudnorm (usado pelo finish_split)
video-use/
  BASE_COMMIT           commit do browser-use/video-use que usamos
  render.py.patch       nossas mudanças no render.py (VIDEO_USE_FPS, retrato ciente de rotação…)
  hf_subs.py            gerador da legenda karaokê (não existe no upstream)
  hf.ps1                wrapper PATH-safe do HyperFrames CLI (não existe no upstream)
```

Origem das versões escolhidas: `compose_hfsubs.py` ← MISSAO_CPA_NOVOS (é a única com o `-t`
que evita cauda congelada); `facecrop.py` ← MISSAO_CPA (a variante do MARE usava limiares
absolutos em px, que falham em 4K); os demais eram idênticos em todos os projetos.

## Projeto novo

```bash
mkdir -p projects/<nome>/edit
cp -r _scaffolds/pipeline-kit/edit/. projects/<nome>/edit/
```

## Caminhos (sem nada fixo na máquina)

Os scripts (e os `finish_*.py` do app) acham os helpers assim:
1. variável `VIDEO_USE_HELPERS`, se definida;
2. senão `<pai de VIDEOS>/claude/video use/helpers` (VIDEOS = primeira pasta acima com `input/`).

SFX: `HF_SFX_DIR`, senão `~/.claude/skills/hyperframes-media/assets/sfx`.

## Máquina nova — instalar o video-use com as nossas mudanças

```powershell
# ao lado da pasta VIDEOS: <pai>\claude\video use
git clone https://github.com/browser-use/video-use.git "..\claude\video use"
cd "..\claude\video use"
git checkout (Get-Content "<VIDEOS>\_scaffolds\pipeline-kit\video-use\BASE_COMMIT")
git apply "<VIDEOS>\_scaffolds\pipeline-kit\video-use\render.py.patch"
Copy-Item "<VIDEOS>\_scaffolds\pipeline-kit\video-use\hf_subs.py","<VIDEOS>\_scaffolds\pipeline-kit\video-use\hf.ps1" helpers\
py -m pip install -e .
py -m pip install opencv-python-headless onnxruntime numpy librosa requests yt-dlp
# criar .env com ELEVENLABS_API_KEY=... (ver .env.example) — nunca versionar
```

Se mudar `render.py`, `hf_subs.py` ou `hf.ps1` na instalação, **regravar aqui**:

```bash
VU="../claude/video use"
cp "$VU/helpers/hf_subs.py" "$VU/helpers/hf.ps1" _scaffolds/pipeline-kit/video-use/
(cd "$VU" && git diff helpers/render.py) > _scaffolds/pipeline-kit/video-use/render.py.patch
```
