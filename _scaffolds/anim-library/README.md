# anim-library — biblioteca de animações/ilustrações reutilizáveis

Catálogo do que já temos pronto para reusar em split / hybrid / faceless, para não redesenhar do zero a cada lote.

- **`library.json`** — registro (fonte de verdade): 3 famílias com id, descrição, params, tags e avisos de capture.
- **`index.html`** — galeria navegável (abrir no navegador ou pela Biblioteca do app).
- **`heroes/*.svg`** — 22 ícones SVG grandes feitos à mão (capture-safe), agrupados por tema em `library.json` → `heroes.grupos`. Copiar o `<svg>` e recolorir pelo acento (cy `#22d3ee`, am `#F5A623`, gr `#34d399`, rd `#ff5c67`).
  - **Finanças**: `coins`, `hand-coin`, `percent`, `bank`, `linechart`, `scale`, `growth-arrow`
  - **Tempo/prazo**: `calendar`, `clock`, `hourglass`
  - **Certificação**: `trophy`, `check-circle`, `book`
  - **CTA/confiança**: `whatsapp`, `deal`, `lock`, `rocket`, `lightbulb`
  - **Metáfora cozinha**: `chef-hat`, `pot`, `plate` · **Alerta**: `warning`

## 3 famílias
1. **ILLOS** (`_scaffolds/split-kit/kit.js`) — 19 ilustrações **animadas, capture-safe**. Uso: `art:{type:'<id>'}` no SCENES do split-kit. Também servem de base para os cards do hybrid e heróis do faceless.
2. **Lottie** (`_scaffolds/faceless-shotseq/assets/lottie/`) — 9 personagens/cenas. ⚠ **SVG puro morre no capture** → CANVAS pré-renderizado (blueprint `_blueprint-lottie-hero`, cap `MAXFR=60`). No lote C-PRO I **só `climbstairs` sobreviveu direto**; para os demais preferir hero SVG até revalidar caso a caso.
3. **heroes** (`heroes/`) — 22 SVG à mão, capture-safe, para faceless (~500px) e cards do hybrid (128px). Regra: texto dentro de forma não pode estourar (textLength+lengthAdjust). A galeria mostra por grupo temático e tem busca por nome/tag.

## Como adicionar
- **Ilustração nova reutilizável** (ex.: fiz à mão num lote e vale guardar): salvar o `<svg>` limpo em `heroes/<id>.svg`, adicionar entrada em `library.json` (heroes.itens) e um card no `index.html`.
- **ILLOS nova**: adicionar em `split-kit/kit.js` (par `svg`+`sig`) e registrar aqui.
- **Lottie/Flaticon pronto**: baixar o `.json`→`<id>-data.js` em `faceless-shotseq/assets/lottie/`, registrar aqui com o aviso de capture.

Fontes externas p/ buscar novas: LottieFiles, Flaticon animated-icons, Flow/Veo (b-roll). Ver `library.json` → `referencias_externas`. Relacionado: [[faceless-kit-broll-pool]], [[reference-flaticon-animated-icons]], [[flow-veo-base-integration]].
