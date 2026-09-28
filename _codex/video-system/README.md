# Codex Video System

Infraestrutura independente para novas edições feitas pelo Codex. Nada nesta pasta altera `_scaffolds/`, `.claude/` ou o `README.md` da raiz.

## Uso em um projeto novo

1. Copiar `templates/codex-video.example.json` para `projects/<nome>/edit/codex-video.json`.
2. Preencher EDL, transcrição, formato, cenas, ritmo e zonas seguras.
3. Importar `components/codex-components.css` e `components/codex-components.js` na composição.
4. Construir os beats usando os componentes, sem editar a biblioteca no projeto.
5. Rodar o QA:

```powershell
node _codex/video-system/qa/video-qa.mjs projects/<nome>/edit/codex-video.json
```

6. Corrigir todos os erros antes dos snapshots e do render.

## Estrutura

- `presets/formats.json`: zonas seguras e regras dos quatro formatos.
- `presets/visual-grammar.json`: famílias visuais por intenção narrativa.
- `templates/codex-video.example.json`: mapa de ritmo e manifesto de QA.
- `components/`: CSS e funções para componentes reaproveitáveis.
- `qa/video-qa.mjs`: validação automática do manifesto e, opcionalmente, do HTML.

O padrão editorial humano continua em `CODEX_EDITING_STANDARD.md`.

## Geração de mídia com Freepik/Magnific

1. Copiar `templates/freepik-scene.example.json` para o projeto e ajustar cena, prompt e saída.
2. Guardar a chave apenas no ambiente e executar:

```powershell
$env:FREEPIK_API_KEY = "sua-chave"
node _codex/video-system/tools/freepik.mjs projects/EXEMPLO/edit/freepik-01.json --dry-run
node _codex/video-system/tools/freepik.mjs projects/EXEMPLO/edit/freepik-01.json
```

O helper envia, acompanha a tarefa, baixa o primeiro resultado e grava um ledger `<arquivo>.json`.
Imagens locais são enviadas como data URI; áudio generativo deve permanecer desligado no padrão de edição.
