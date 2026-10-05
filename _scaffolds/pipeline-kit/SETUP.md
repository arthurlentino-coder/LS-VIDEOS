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
| `MESA_HOST` | bind do console | `127.0.0.1` |
| `MESA_PORT` | porta | `8756` |
| `MESA_TOKEN` | **se definido, exige login** (Basic Auth, senha = token) | — (sem auth) |
| `MESA_CERT` / `MESA_KEY` | HTTPS direto (cert+chave PEM) | — (HTTP) |

## 5. Conferir o ambiente
```
py _scaffolds/pipeline-kit/doctor.py
```
`✓/⚠/✗` por item + dica. Falha (`✗`) = item essencial ausente.

## 6. Rodar o console
```
py apps/mesa-de-corte/server.py        # http://127.0.0.1:8756
```

## 7. Acesso remoto (seguro)
**Nunca** exponha sem `MESA_TOKEN`. Duas formas:
- **Túnel (recomendado)** — Cloudflare Tunnel ou Tailscale apontando p/ `127.0.0.1:8756`;
  o túnel cuida do HTTPS. Defina `MESA_TOKEN` mesmo assim.
- **Direto** — `MESA_HOST=0.0.0.0 MESA_TOKEN=<senha forte> py server.py` (+ `MESA_CERT`/`MESA_KEY`
  p/ HTTPS). Abra a porta no firewall só se souber o que está fazendo.

## 7.1 Contas e multiusuário (Estágio B)
Sem contas (e sem `MESA_TOKEN`) = **modo aberto**: single-user, acesso total (uso local).
Ao criar a 1ª conta, o console passa a **exigir login** (Basic Auth por usuário):
```
py apps/mesa-de-corte/useradd.py <usuario> <senha> [--role admin|user]
py apps/mesa-de-corte/useradd.py --list
```
- Contas ficam em `orders/_users.json` (senha pbkdf2-sha256; fora do git).
- Cada lote criado ganha **`owner`** = quem o criou. **user** só vê/mexe nos próprios lotes;
  **admin** vê/mexe em todos. `MESA_TOKEN` continua valendo como senha-mestra (= admin).
- Banco de dados e object storage ficam pro Estágio C (hosting); hoje os dados seguem em
  `orders/*.json` + mídia local, só que agora escopados por dono.

## 8. Build de um item (pipeline)
```
bash _scaffolds/pipeline-kit/build_item.sh projects/<X> output/<LOTE>/<X> <LOTE> "<item>"
```
`build_item.sh` deriva a raiz sozinho (ou use `VIDEOS_ROOT`). Flags: `RECONCILE=0`, `CTA_EXT=1`,
`MOOD=…`, `DRESS=0`, `SKIP_CERT=1`.

> **Nota:** o console **não renderiza** — ele configura/revisa/aprova. A produção de vídeo é o
> pipeline (ffmpeg/HyperFrames/kits) conduzido pelo operador (hoje, Claude + você).
