# Setup — console Mesa de Corte + pipeline (em qualquer máquina)

O repositório versiona **o processo** (console, scripts, kits). **Mídia** (brutas, saídas,
masters) e os **helpers do video-use** ficam FORA do git. Rode `doctor.py` pra ver o que falta.

## 1. Pré-requisitos
- **Python 3.10+** (no Windows, o launcher `py`).
- **ffmpeg + ffprobe** no PATH.
- **Node.js LTS** (traz `npx`) + **HyperFrames**: rode uma vez `npx hyperframes --version` (baixa/caça o CLI).
- (Opcional, p/ transcrição/TTS) chave **ElevenLabs/Scribe**.

## 2. Estrutura do VIDEOS
Raiz com: `input/` (brutas), `output/` (entregas), `projects/`, `_scaffolds/`, `apps/mesa-de-corte/`.
A raiz é auto-detectada (sobe até achar `input/`); force com `VIDEOS_ROOT` se precisar.

## 3. Peças que ficam fora do repo (copiar/apontar por env)
- **Helpers do video-use** (`render.py` etc.): default `<pai do VIDEOS>/claude/video use/helpers`;
  override `VIDEO_USE_HELPERS=/caminho/para/helpers`.
- **Lib de SFX**: default `~/.claude/skills/hyperframes-media/assets/sfx`; override `HF_SFX_DIR`.
- **YuNet** (`yunet.onnx`) e **fontes**: já vêm em `_scaffolds/pipeline-kit/edit/hf/` e nos kits.

## 4. Variáveis de ambiente
| var | p/ quê | default |
|---|---|---|
| `VIDEOS_ROOT` | raiz do VIDEOS | auto-detect |
| `VIDEO_USE_HELPERS` | helpers do video-use | `<pai>/claude/video use/helpers` |
| `HF_SFX_DIR` | lib de SFX | `~/.claude/skills/hyperframes-media/assets/sfx` |
| `ELEVENLABS_API_KEY` | Scribe/TTS | — |
| `MESA_PORT` | porta do console | `8756` |

## 5. Conferir (e instalar) o ambiente
```
py _scaffolds/pipeline-kit/doctor.py --fix    # instala o que dá e re-checa
py _scaffolds/pipeline-kit/doctor.py          # só diagnostica
```
`--fix` instala pacotes Python + baixa o HyperFrames + tenta ffmpeg/Node via winget.
Não automatiza (precisa de você): **mídia** (`input/`), **helpers do video-use** (§3) e
**`ELEVENLABS_API_KEY`**. `✗` = item essencial ausente. (Se ffmpeg/Node acabaram de instalar,
reabra o terminal pro PATH.)

## 6. Rodar o console
```
py apps/mesa-de-corte/server.py        # http://127.0.0.1:8756
```

## 7. Build de um item (pipeline)
```
bash _scaffolds/pipeline-kit/build_item.sh projects/<X> output/<LOTE>/<X> <LOTE> "<item>"
```
`build_item.sh` deriva a raiz sozinho (ou use `VIDEOS_ROOT`). Flags: `RECONCILE=0`, `CTA_EXT=1`,
`MOOD=…`, `DRESS=0`, `SKIP_CERT=1`.

> **Nota:** o console **não renderiza** — ele configura/revisa/aprova. A produção de vídeo é o
> pipeline (ffmpeg/HyperFrames/kits) conduzido pelo operador (hoje, Claude + você).
