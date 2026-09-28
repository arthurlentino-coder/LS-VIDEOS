# Prompt de setup — Processo padrão de edição automática de vídeos

> Cole o texto abaixo (entre as linhas `=====`) no Claude Code / Codex, preenchendo os
> campos entre colchetes `[ ]`. Ele configura o MESMO processo que já validamos:
> repositório Video Use + ElevenLabs Scribe + convenção de pastas `VIDEOS/` +
> legendas com fundo arredondado + verificação técnica antes do final.

==========================================================================

Estou começando um projeto de edição automática de vídeos com foco em QUALIDADE,
e quero replicar exatamente um processo padrão já validado por um colega.

Quero que você configure e use este repositório:
https://github.com/browser-use/video-use

## Objetivo
Editar vídeos que eu enviar ou apontar no disco, removendo silêncios longos, erros de
fala, falsos começos, repetições, frases abandonadas, pausas desnecessárias e trechos
de bastidor — mantendo a fala natural, clara e profissional. Sem alterar o vídeo original.

## Configurações do projeto (preencha)
- Pasta-raiz onde tudo vai morar (vou chamar de VIDEOS/):
  [CAMINHO_DA_PASTA_RAIZ_AQUI]   ex.: C:\Users\SEU_USUARIO\Desktop\VIDEOS
- Idioma principal do vídeo: [pt-BR]
- Orientação de saída: [VERTICAL_9x16  /  LANDSCAPE_16x9  /  AMBAS]
- Quero legendas queimadas no vídeo? [SIM ou NAO]
  - Se SIM, estilo: legenda com fundo arredondado, centralizada embaixo, branca,
    aparecendo por frase (calibrar fonte/tamanho conforme a orientação).
- Estilo de edição: [LIMPO_E_NATURAL]  (opções: LIMPO_E_NATURAL, DINAMICO, AGRESSIVO, DOCUMENTAL)
- Chave da ElevenLabs: [ELEVENLABS_API_KEY=COLE_SUA_CHAVE_AQUI]
- Prioridade: QUALIDADE_ACIMA_DE_ECONOMIA

## Estrutura de pastas OBRIGATÓRIA (convenção fechada)
Crie e use exatamente este layout dentro da pasta-raiz VIDEOS/:

```
VIDEOS/
  input/                      Fontes originais. NUNCA alteradas nem re-transcritas.
  output/                     Finais entregues, nomeados pelo vídeo.
  projects/<nome>/edit/       Todo o trabalho: transcript, edl.json, clips, legendas,
                              base/preview intermediários, helpers locais, project.md.
  README.md                   Documenta esta convenção.
```

Regras de nomeação:
- `<nome>` = nome-base do arquivo de origem (ex.: `IMG_5055`, `C0205`).
- A fonte vai para `input/` e o `edl.json` a referencia por CAMINHO ABSOLUTO. Fica intocada.
- Saída em `output/`: vídeo único → `<nome>.mp4`; duas orientações →
  `<nome>_landscape.mp4` e `<nome>_vertical.mp4`.

## Configuração técnica
- Use Video Use como ferramenta principal (instalação editável `video-use`).
- Helpers compartilhados (render, grade, transcribe, pack_transcripts, timeline_view)
  ficam numa pasta `helpers/` da instalação do video-use. Cada projeto tem CÓPIA LOCAL
  de `build_subs.py` e `round_subs.py` na sua `edit/` (legenda calibrada por orientação).
- Use ElevenLabs Scribe para transcrição word-level. Reaproveite transcrições cacheadas
  em `transcripts/<nome>.json` quando existirem — NÃO re-transcrever.
- Configure o ambiente Python necessário.
- Verifique se `ffmpeg` e `ffprobe` estão instalados. Se não estiverem, me diga
  exatamente como instalar no meu sistema ANTES de continuar.
- Registre o skill do Video Use, se fizer sentido.
- Não use HyperFrames, Remotion, overlays ou animações por padrão, a menos que eu peça.
- Use raciocínio médio/alto para decidir entre manter/remover trechos ambíguos.

## Fluxo obrigatório (passo a passo)
1. Configure o projeto e a estrutura de pastas acima.
2. Faça inventário da fonte com `ffprobe` (resolução, fps, transfer/HDR, áudio, duração)
   e anote no `project.md`.
3. Transcreva com ElevenLabs Scribe (ou reutilize o cache). Salve em `transcripts/`.
4. Gere `takes_packed.md` (frases agrupadas; marque o speaker em cenas com 2+ pessoas).
5. Leia a transcrição COMPLETA antes de cortar.
6. Identifique e liste internamente: silêncios longos, erros de fala, falsos começos,
   repetições, frases abandonadas, trechos corrigidos logo depois, pigarros/tosses/ruídos,
   e bastidor que não faz parte do conteúdo.
7. Monte o `edl.json` com cortes por palavra. Cada range: start/end, beat, quote, reason.
   - Regra "errou-e-repetiu": quando a pessoa erra e repete, corte o retake INTEIRO e
     mantenha só a versão correta e completa.
   - Para versão vertical com punch-in, use `crop_x` por range (fração da largura,
     centro do recorte 9:16). Cena com 2 pessoas: priorize quem faz o pitch/CTA.
8. Preserve pequenas pausas naturais para a fala não ficar robótica. Use `crossfade_s`
   curto (~0,13s) nas junções.
9. Color grade só quando necessário: tonemap APENAS se a fonte for HDR/HLG (fontes SDR
   não precisam).
10. Renderize a `base` (extract por segmento → xfade-concat → `base.mp4`, sem legenda).
    Case o fps com a fonte (ex.: `VIDEO_USE_FPS=25`).
11. Gere um `preview.mp4` (ou `preview_h.mp4` / `preview_v.mp4`) ANTES do final.
12. Verifique o preview:
    - duração coerente
    - áudio sem cortes secos / estalos
    - sem frases cortadas no meio
    - repetições óbvias removidas
    - legendas (se houver) sincronizadas
    - vídeo NÃO travado / fps correto
    - áudio NÃO dessincronizado do vídeo
13. Se houver problema claro, ajuste o `edl.json` e gere novo preview.
14. Só gere o final depois do preview aprovado ou claramente correto.
15. Legendas (se SIM): aplique por ÚLTIMO, via `round_subs.py` (fundo arredondado —
    libass não arredonda). Calibre fonte/tamanho pela orientação.
16. Final com `round_subs.py --final`: CRF 20 + loudnorm two-pass, alvo −14 LUFS /
    −2,8 dBTP. Salve em `output/<nome>.mp4` (ou `_landscape`/`_vertical`).
17. Salve um resumo da edição (inventário, decisões de corte, parâmetros, status) em
    `projects/<nome>/edit/project.md`.

## Critérios de qualidade
- Não cortar dentro de palavras nem em respirações naturais importantes.
- Não deixar a fala robótica/acelerada nem cortes secos com estalo.
- Não deixar legendas fora de sincronia. Não alterar o vídeo original.
- Não remover trechos que mudem o sentido da fala.
- Na dúvida entre remover ou manter, MANTENHA no preview e me avise.
- Para vídeos longos, use timeline views/imagens só nos pontos ambíguos/importantes.
- Antes de finalizar, faça pelo menos uma checagem técnica com `ffprobe`.

## Saídas esperadas (em projects/<nome>/edit/, exceto o final)
- `transcripts/<nome>.json`  - `takes_packed.md`  - `edl.json`
- `base.mp4` / `preview.mp4`  - `master.srt` (se houver legenda)
- `project.md`  - final em `output/<nome>.mp4` (ou `_landscape`/`_vertical`)

## Antes de editar qualquer vídeo, configure tudo e me diga:
- onde o projeto e as pastas foram criados
- onde os arquivos de trabalho e o final serão salvos
- se a chave da ElevenLabs funcionou
- se `ffmpeg` e `ffprobe` estão funcionando
- qual será o próximo comando/etapa

==========================================================================
