# Padrão de edição — fluxo Codex

Documento independente para as próximas edições realizadas pelo Codex neste workspace.

> Não editar, substituir ou sincronizar automaticamente este documento com o `README.md`, arquivos em `.claude/` ou qualquer instrução mantida pelo Claude. Em caso de divergência, este arquivo rege apenas o fluxo feito por aqui.

Última consolidação: 2026-08-04, após a validação do projeto `C0221`.

Infraestrutura executável: `_codex/video-system/`.

## 1. Premissas gerais

- Formato principal: vertical `1080x1920`, mantendo o enquadramento correto da fonte vertical.
- Ferramentas visuais: HyperFrames + GSAP, Lottie e ícones/ilustrações do Flaticon.
- Não depender do Google Flow para gerar vídeos ou motions.
- Usar b-roll quando o formato pedir, mas sem substituir motions importantes por planos longos e estáticos.
- Não usar cabeçalhos editoriais repetidos no topo das cenas.
- Nenhum texto, selo, ilustração ou legenda pode se sobrepor de forma que outro elemento fique ilegível.
- Motions devem aproveitar bem a tela e permanecer vivos. Evitar elementos pequenos cercados por grandes áreas vazias.
- Toda arte precisa ficar contida em sua caixa ou região segura; nada pode escapar, cortar ou cobrir o apresentador sem intenção.
- Não reutilizar a antiga arte do cartão `CPA 20 / certificação atual / reta final`. Ela apresentou problemas recorrentes e foi descartada em todos os formatos.

## 2. Legendas — padrão compartilhado

- A legenda deve ser derivada da transcrição palavra por palavra e remapeada pelos cortes reais da EDL.
- Nunca usar blocos resumidos com tempos aproximados.
- Texto fiel ao áudio, incluindo a ordem e a duração das palavras.
- Agrupamento de referência validado no `C0221`: até 6 palavras ou aproximadamente 2,2 segundos por bloco.
- Quebrar o bloco em pausas longas, pontuação natural e fronteiras de cortes da EDL.
- Destaque progressivo por palavra: palavra ativa escura; palavras ainda não faladas em cinza.
- Caixa clara sólida ou quase sólida, cantos arredondados, contraste alto e sombra discreta.
- Tipografia de referência: Inter bold, aproximadamente 38 px em `1080x1920`.
- A posição é específica de cada formato; não aplicar uma coordenada global a todos.
- Conferir sincronismo no começo, em todas as mudanças de take/cena e no encerramento.
- Conferir que a legenda não cobre rosto, braços, textos, CTA ou a arte principal.

## 3. Talking Head

Formato completamente limpo.

- Manter o apresentador como foco durante todo o vídeo.
- Usar apenas cortes, reenquadramentos e transições discretas.
- Legenda no terço inferior, elevada o suficiente para respeitar a área segura da plataforma.
- Trilha de fundo sutil e compatível com o conteúdo.
- Efeitos sonoros apenas em momentos pontuais e justificados.
- Não inserir cabeçalho, cards explicativos, ilustrações ou motions sobre o apresentador.
- Uma versão com cards pode existir, mas deve ser classificada como `Hybrid`, nunca como Talking Head.

## 4. Split

- Divisão principal: apresentador na metade superior e motions na metade inferior.
- A legenda fica no meio da tela, sobre a região de divisão entre o vídeo e a área gráfica. Não fica no rodapé.
- Não usar texto de cabeçalho no topo da área gráfica.
- O motion inferior deve preencher a região disponível com hierarquia clara.
- Textos, selos, gráficos e ilustrações não podem se cobrir.
- Alternar entradas, progressões, contagens, traçados e movimentos ociosos para evitar cenas estáticas.
- Evitar manter a mesma montagem por tempo demais; adaptar a composição ao conteúdo de cada trecho.
- Respeitar a caixa da legenda central para que o motion não perca legibilidade.
- Referência mais recente: `projects/C0221/edit/output/C0221_split_V7_REVIEW.mp4`.

## 5. Hybrid

O apresentador permanece dominante, com uma caixa gráfica compacta e editorial.

- Não usar cabeçalho no topo do quadro.
- Posicionar a legenda acima da caixa gráfica e abaixo do rosto, sem cobrir a cabeça.
- A caixa deve ser menor do que a usada nos primeiros testes e não pode cobrir cabeça ou braços.
- Todas as artes precisam caber dentro da caixa, com margens internas consistentes.
- Remover a faixa/borda amarela lateral ou inferior da caixa.
- Preferir caixa escura neutra, cantos arredondados e acentos cromáticos discretos coerentes com a cena.
- Manter headline forte, apoio curto e arte/ícone proporcional; não comprimir uma composição de tela cheia dentro de um card.
- Motions precisam continuar ativos dentro da caixa: entrada, progresso, troca de estado e idle discreto.
- A variação `hybrid-overlay` é permitida como segunda opção, seguindo as mesmas zonas seguras.
- Referência de linguagem visual: card compacto validado com o texto `VOCÊ NÃO ESTÁ SOZINHO`, adaptado ao assunto de cada vídeo.

## 6. Faceless

- Usar como referência editorial de ritmo e composição o arquivo `output/TESTES/CPRO_1_faceless_editorial.mp4`.
- O apresentador não precisa permanecer visível; construir narrativa por motions, tipografia, ilustrações e b-roll.
- Variar a montagem de cena: pôster tipográfico, diagrama, progressão, comparação, ícone animado e b-roll editorial.
- Preencher melhor a tela, distribuindo conteúdo do topo à base e evitando uma arte pequena isolada no centro.
- Não usar cabeçalho repetido.
- Manter os mesmos cuidados do Split com sobreposição, legibilidade e legenda.
- Usar Lottie e Flaticon para artes ricas; evitar SVGs improvisados ou desenhos simples que pareçam provisórios.
- B-roll deve receber tratamento editorial e movimento sutil, sem virar um plano estático longo.
- Variar direções de entrada e transições; não repetir a mesma animação em cenas consecutivas.
- Todo elemento deve ter entrada, desenvolvimento ou idle. Evitar motions congelados.

## 7. Áudio

- A fala sempre tem prioridade.
- Trilha discreta, coerente com o tom institucional/educacional e sem sensação de música genérica animada.
- Aplicar ducking quando necessário.
- SFX apenas em transições ou acontecimentos visuais relevantes.
- Não adicionar efeitos continuamente nem competir com a voz.

## 8. Processo obrigatório por nova bruta

1. Inspecionar orientação, resolução, fps, áudio e duração da fonte.
2. Transcrever com timestamps por palavra.
3. Montar e registrar a EDL antes de gerar legendas e motions.
4. Criar uma base vertical única para todos os formatos.
5. Gerar as legendas a partir da transcrição remapeada pela EDL.
6. Produzir Talking Head, Split, Hybrid e Faceless conforme os padrões acima.
7. Validar snapshots de diferentes momentos, incluindo todas as mudanças de cena.
8. Conferir visualmente enquadramento, sobreposições, áreas vazias, movimento e posição da legenda.
9. Renderizar cada formato em `1080x1920`, preservando o fps definido para o projeto.
10. Recolocar/mixar o áudio e validar com `ffprobe` vídeo, áudio, resolução, fps e duração.
11. Entregar arquivos de revisão separados; nunca sobrescrever uma versão já aprovada.

## 9. Checklist de aprovação

- [ ] Talking Head está limpo, sem cards ou cabeçalhos.
- [ ] Split tem legenda no centro/divisória, não no rodapé.
- [ ] Hybrid não cobre rosto, cabeça ou braços.
- [ ] Hybrid não possui faixa amarela e mantém toda arte dentro da caixa.
- [ ] Faceless usa b-roll e montagem variada, sem grandes vazios.
- [ ] A antiga arte `CPA 20 / reta final` não aparece em nenhum formato.
- [ ] Não há motion estático por tempo excessivo.
- [ ] Não há textos ou elementos ilegíveis por sobreposição.
- [ ] Legendas estão sincronizadas palavra por palavra e dentro da zona segura de cada formato.
- [ ] Todos os arquivos finais contêm vídeo e áudio e têm duração correta.

## 10. Política de versões

- Criar uma nova versão numerada para cada rodada relevante: `V1`, `V2`, `V3` etc.
- Usar o sufixo `_REVIEW` para arquivos enviados para aprovação.
- Não apagar nem sobrescrever versões anteriores.
- Mudanças no padrão Codex devem ser registradas somente neste arquivo, salvo pedido explícito do usuário para alterar outra documentação.
