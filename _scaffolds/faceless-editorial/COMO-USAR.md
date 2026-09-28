# Scaffold faceless-editorial — como fazer um novo

Objetivo: gerar um faceless editorial gastando **só** o esforço das cenas (o framework CSS/JS é
reaproveitado, não reescrito). Ver o padrão completo no README §7.6 / §7.3.2.

## Passos

1. **Copiar** `_scaffolds/faceless-editorial/public/` → `projects/<NOME>/edit/hf/faceless-editorial/public/`.
2. **Trazer os assets do projeto** pra `public/assets/`: os 3–4 b-roll (dos `faceless-broll/` antigo ou
   novos do Pexels/Pixabay/Mixkit) e nada mais (os personagens Lottie já estão no scaffold).
3. **Editar só o `index.html`:**
   - `data-duration` do `#stage` = duração total do vídeo.
   - `<video class="bvid clip">` (track-index 1): um por cena de b-roll, com `data-start/duration`.
   - `<section>` das cenas (track-index 2): copiar o molde certo (motion-personagem / motion-SVG /
     b-roll / CTA), pôr a classe de paleta (`.pal-warm/.mint/.cyan/.azure/.rose`), kicker/headline
     (com `<b>` no acento)/sub, 3 badges, e a arte (canvas do personagem OU `<svg class="artsvg">`).
   - No `<script>` final: `import`(destructure) de `window.HF`, preload dos personagens usados,
     `wordSplit()`, `timeline()`, `enter/benter/cta` por cena, `idle` por cena de motion,
     `charLoop` por personagem, e as animações internas custom dos SVGs.
4. **Timings sem re-transcrever:** copiar os `data-start/duration` de cada cena do `faceless-broll/`
   antigo do próprio projeto.
5. **Render + compose:** `hf.ps1 render public -o render_ed.mp4` → `compose_ed.sh`
   (subs-divider `-c:v libvpx-vp9` no offset do projeto + áudio −14 do `base_zoom_seam`; mutar foley
   pré-fala se houver). Saída `output/TESTES/<NOME>_faceless_editorial.mp4`.

## Regras que não podem furar

- **Cor:** coesão POR CENA; a paleta muda por seção narrativa (não paleta única no vídeo).
- **Ilustração no disco:** viewBox `0 0 400 400`, centro do disco = `(200,200)`, preencher bem o disco
  (como os personagens). **NUNCA animar `x`/`y` num `<g transform="translate()">`** (o GSAP apaga o
  translate → figura vai pro topo) — desenhar em coordenadas absolutas. `scale` puro e
  `scale`/`rotation`+`svgOrigin` são seguros.
- **b-roll SEM zoom** (footage estático). **Idle** em toda cena de motion (nunca congela).
- Snapshot é flaky com preload de Lottie → **verificar sempre no vídeo renderizado**.

## Personagens disponíveis (em `assets/`)

`climbstairs` (subir/avançar), `graduation` (conquista/título/formação), `exam` (estudo/simulado),
`manworking` (trabalho/rotina), `wave` (celebração/CTA). Recolor automático pela paleta via `--charf`.
Pra outro personagem: baixar Lottie (LottieFiles), virar `window.__xData` em `assets/<n>-data.js`.
