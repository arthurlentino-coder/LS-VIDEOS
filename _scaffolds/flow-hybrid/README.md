# Flow hybrid — base única para split e faceless

Este scaffold integra bases cinematográficas do Google Flow/Veo ao processo existente. Ele não
substitui o HyperFrames: o modelo gera somente pixels de fundo; o compositor mantém toda informação
legível e o timing editorial.

## Estrutura por projeto

```text
flow/
  manifest.json
  prompts/NN-conceito.txt
  incoming/NN.mp4
  generated/NN-normalized.mp4
  split/public/index.html
  faceless/public/index.html
  renders/<nome>_split_flow.mp4
  renders/<nome>_faceless_flow.mp4
```

## Contrato do manifest

Cada cena declara `id`, `start`, `duration`, `source`, `kicker`, `headline`, `accent` e `palette`.
`source` aponta para a geração bruta. O mesmo registro alimenta as duas composições.

## Prompt obrigatório

- descrever a ideia/sentimento, não repetir literalmente a fala;
- pedir 9:16, movimento contínuo e câmera controlada;
- reservar espaço negativo para a copy;
- proibir pessoas quando não forem necessárias;
- finalizar com: `No logos, no brands, no letters, no words, no numbers, no captions, no cuts.`

## Gates

1. `motion-plan.md` aprovado;
2. prompts aprovados ou derivados do plano aprovado;
3. bases geradas e inspecionadas em contact sheet;
4. normalização para 30 fps e duração real;
5. composição split e faceless;
6. `lint`, `validate`, `inspect` e contact sheet;
7. montagem com áudio/legenda locais e `/watch` no arquivo final.

O projeto `projects/FLOW_TEST_IMG5051/` é a implementação de referência inicial.
