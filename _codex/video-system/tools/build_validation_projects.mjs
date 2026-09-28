import fs from "node:fs";
import path from "node:path";

const workspace = path.resolve(
  path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")),
  "..",
  "..",
  "..",
);
const system = path.join(workspace, "_codex", "video-system");
const validation = path.join(workspace, "_codex", "validation");
const vendor = path.join(
  workspace,
  "_scaffolds",
  "faceless-editorial",
  "public",
  "vendor",
  "gsap.min.js",
);

const content = {
  C0207: {
    hook: {
      kicker: "INSCRIÇÕES ABERTAS",
      title: "NÃO PERCA A SUA CHANCE",
      copy: "Missão CPA está com uma nova turma.",
      kind: "progress",
      value: 82,
    },
    promise: {
      kicker: "MISSÃO CPA",
      title: "CPA-20 EM 15 DIAS",
      copy: "Um plano direto até a aprovação.",
      kind: "metric",
      value: "15",
    },
    proof: {
      kicker: "MUDE O MÉTODO",
      title: "MESES DE ESTUDO NÃO PRECISAM SER A REGRA",
      copy: "Treino direcionado, acompanhamento e rota clara.",
      kind: "checklist",
      items: ["Direção", "Prática", "Aprovação"],
    },
    cta: { kicker: "ÚLTIMA CHAMADA", title: "CLIQUE E VENHA", kind: "cta" },
  },
  IMG_5053: {
    question: {
      kicker: "TRABALHO DURO",
      title: "POR QUE A VIDA NÃO MUDA?",
      copy: "Esforço sem direção mantém o resultado no mesmo lugar.",
      kind: "comparison",
      left: "MUITO ESFORÇO",
      right: "POUCA MUDANÇA",
    },
    contrast: {
      kicker: "O PONTO NÃO É CAPACIDADE",
      title: "QUEM COMEÇA DO ZERO TAMBÉM AVANÇA",
      copy: "A diferença aparece no caminho escolhido.",
      kind: "timeline",
      items: ["Zero", "Direção", "Mudança"],
    },
    direction: {
      kicker: "OLHE DE NOVO",
      title: "O DIRECIONAMENTO CERTO MUDA A ROTA",
      copy: "Pare de insistir no lado errado.",
      kind: "progress",
      value: 74,
    },
    cta: { kicker: "PRÓXIMO PASSO", title: "CLIQUE AQUI EMBAIXO", kind: "cta" },
  },
};

const esc = (value) =>
  String(value).replace(
    /[&<>\"]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char],
  );
const js = (value) => JSON.stringify(value).replace(/</g, "\\u003c");

function groups(words) {
  const result = [];
  let group = [];
  for (const word of words) {
    const previous = group.at(-1);
    const boundary =
      previous &&
      (word.rangeIndex !== previous.rangeIndex ||
        word.start - previous.end > 0.75);
    const tooLong =
      group.length >= 6 || (group.length && word.end - group[0].start > 2.2);
    if (group.length && (boundary || tooLong)) {
      result.push(group);
      group = [];
    }
    group.push(word);
    if (/[.!?]$/.test(word.text)) {
      result.push(group);
      group = [];
    }
  }
  if (group.length) result.push(group);
  return result.map((items) => ({
    start: items[0].start,
    end: items.at(-1).end,
    words: items,
  }));
}

function visualMarkup(sceneId) {
  const common = `viewBox="0 0 320 320" fill="none" xmlns="http://www.w3.org/2000/svg"`;
  if (sceneId === "hook") return `<svg class="scene-icon icon-stopwatch" ${common}><circle class="draw" cx="160" cy="170" r="104"/><path class="draw" d="M128 36h64M160 36v28M235 91l22-22"/><path class="hand" d="M160 170l54-46"/><circle cx="160" cy="170" r="12" fill="currentColor"/></svg>`;
  if (sceneId === "promise") return `<svg class="scene-icon icon-calendar" ${common}><rect class="draw" x="55" y="68" width="210" height="198" rx="24"/><path class="draw" d="M55 118h210M103 48v42M217 48v42"/><text x="160" y="214" text-anchor="middle" class="svg-number">15</text></svg>`;
  if (sceneId === "proof") return `<svg class="scene-icon icon-route" ${common}><path class="route draw" d="M56 242C82 94 131 267 166 139S238 84 264 58"/><circle class="node n1" cx="56" cy="242" r="17"/><circle class="node n2" cx="166" cy="139" r="17"/><circle class="node n3" cx="264" cy="58" r="17"/><path class="check" d="m252 58 9 9 18-22"/></svg>`;
  if (sceneId === "question") return `<svg class="scene-icon icon-balance" ${common}><path class="draw" d="M160 54v208M76 92h168M96 92l-48 98h96L96 92Zm128 0-48 98h96L224 92Z"/><circle cx="160" cy="54" r="13" fill="currentColor"/></svg>`;
  if (sceneId === "contrast") return `<svg class="scene-icon icon-steps" ${common}><rect class="step s1" x="45" y="214" width="64" height="50" rx="8"/><rect class="step s2" x="128" y="156" width="64" height="108" rx="8"/><rect class="step s3" x="211" y="90" width="64" height="174" rx="8"/><circle class="person" cx="243" cy="59" r="18"/><path class="person-line" d="M243 78v64m0-44-28 27m28-27 27 23"/></svg>`;
  if (sceneId === "direction") return `<svg class="scene-icon icon-compass" ${common}><circle class="draw" cx="160" cy="160" r="112"/><circle class="draw" cx="160" cy="160" r="82"/><path class="needle" d="m205 105-28 72-72 28 28-72 72-28Z" fill="currentColor"/><circle cx="160" cy="160" r="10" fill="#f7f4ea"/></svg>`;
  return `<svg class="scene-icon icon-cta" ${common}><path class="cursor" d="m91 58 137 117-65 11-32 65L91 58Z"/><circle class="ripple r1" cx="198" cy="181" r="38"/><circle class="ripple r2" cx="198" cy="181" r="70"/></svg>`;
}

function cardMarkup(project, scene) {
  const item = content[project][scene.id];
  const data = esc(JSON.stringify(item));
  return `<section id="scene-${scene.id}" class="clip scene" data-scene-id="${scene.id}" data-start="${scene.start}" data-duration="${Math.max(0.04, scene.duration - 0.04).toFixed(2)}" data-track-index="2"><div class="scene-shell"><div class="ambient ambient-a" data-layout-ignore></div><div class="ambient ambient-b" data-layout-ignore></div><div class="grid" data-layout-ignore></div><div class="scene-visual">${visualMarkup(scene.id)}</div><div class="component-mount" data-component="${data}"></div><div class="meta">${esc(scene.id.toUpperCase())} · ${String(scene.start).padStart(5, "0")}s</div></div></section>`;
}

function indexHtml(project, format, plan, captionGroups) {
  const duration = captionGroups.length
    ? Math.max(
        plan.scenes.at(-1).start + plan.scenes.at(-1).duration,
        captionGroups.at(-1).end,
      )
    : plan.scenes.at(-1).start + plan.scenes.at(-1).duration;
  const scenes =
    format === "talking-head"
      ? ""
      : plan.scenes.map((scene) => cardMarkup(project, scene)).join("");
  const compositionId = `${project.toLowerCase()}-${format}`;
  return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920"><link rel="stylesheet" href="codex-components.css"><link rel="stylesheet" href="style.css"></head><body data-mode="${format}"><main id="root" data-composition-id="${compositionId}" data-start="0" data-width="1080" data-height="1920" data-duration="${duration.toFixed(3)}" data-fps="${plan.canvas.fps}"><div class="frame-fill"></div><video id="source-video-bg" src="base.mp4" data-start="0" data-duration="${duration.toFixed(3)}" data-track-index="0" data-has-audio="false" playsinline muted></video><video id="source-video" src="base.mp4" data-start="0" data-duration="${duration.toFixed(3)}" data-track-index="1" data-has-audio="true" playsinline></video>${scenes}</main><script src="gsap.min.js"></script><script>window.__timelines=window.__timelines||{};window.__codexTl=window.__codexTl||gsap.timeline({paused:true});window.__timelines[${js(compositionId)}]=window.__codexTl;</script><script src="codex-components.js"></script><script>window.__PROJECT__=${js(project)};window.__FORMAT__=${js(format)};window.__SCENES__=${js(plan.scenes)};window.__CAPTIONS__=${js(captionGroups)};</script><script src="app.js"></script></body></html>`;
}

const style = `
@font-face{font-family:Inter;src:local(Arial)}*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#101719}body{font-family:Inter,Arial,sans-serif}#root{position:relative;width:1080px;height:1920px;overflow:hidden}.frame-fill{position:absolute;inset:0;background:#101719;z-index:0}#source-video{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1}.clip{position:absolute}.scene{z-index:4;overflow:hidden}.scene-shell{position:absolute;inset:0;background:#101719;overflow:hidden}.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(244,240,231,.06) 2px,transparent 2px),linear-gradient(90deg,rgba(244,240,231,.06) 2px,transparent 2px);background-size:72px 72px}.ambient{position:absolute;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(227,74,67,.34),rgba(227,74,67,0) 68%)}.ambient-a{right:-180px;top:-160px}.ambient-b{left:-260px;bottom:-240px;transform:scale(.75)}.component-mount{position:absolute}.meta{position:absolute;color:#a9b1ad;font:700 20px/1 Inter,Arial,sans-serif;letter-spacing:.14em}.synced-caption{position:absolute;left:70px;right:70px;z-index:20;text-align:center}.synced-caption span{display:inline-block;max-width:900px;padding:17px 27px;border-radius:13px;background:rgba(247,244,236,.97);box-shadow:0 12px 34px rgba(0,0,0,.46);color:#8b928e;font:800 38px/1.13 Inter,Arial,sans-serif}.synced-caption i{font-style:normal;color:#8b928e;opacity:.72}.synced-caption i.spoken{color:#111819;opacity:1}body[data-mode="talking-head"] .synced-caption{bottom:230px}body[data-mode="split"] #source-video{height:960px;object-position:center center}body[data-mode="split"] .scene{inset:960px 0 0}body[data-mode="split"] .component-mount{inset:85px 70px 120px}body[data-mode="split"] .meta{left:72px;bottom:54px}body[data-mode="split"] .synced-caption{top:920px;bottom:auto}body[data-mode="hybrid"] .scene{inset:0}body[data-mode="hybrid"] .scene-shell{background:transparent}body[data-mode="hybrid"] .grid,body[data-mode="hybrid"] .ambient{display:none}body[data-mode="hybrid"] .component-mount{left:120px;right:120px;bottom:155px;height:390px}body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{position:absolute;inset:0;width:auto;height:auto;padding:34px 40px;background:rgba(16,23,25,.95)}body[data-mode="hybrid"] .cv-title{font-size:50px;max-width:720px}body[data-mode="hybrid"] .cv-copy{font-size:24px;margin-top:12px}body[data-mode="hybrid"] .cv-rule{margin:18px 0}body[data-mode="hybrid"] .cv-metric-value{font-size:96px}body[data-mode="hybrid"] .cv-list{grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px}body[data-mode="hybrid"] .cv-list-item{font-size:21px;grid-template-columns:30px 1fr;gap:8px}body[data-mode="hybrid"] .cv-list-mark{width:28px;height:28px}body[data-mode="hybrid"] .cv-timeline{margin-top:16px}body[data-mode="hybrid"] .cv-step{min-height:90px;padding:14px}body[data-mode="hybrid"] .meta{display:none}body[data-mode="hybrid"] .synced-caption{bottom:600px}body[data-mode="faceless"] #source-video{filter:blur(5px) brightness(.28) saturate(.72);transform:scale(1.04)}body[data-mode="faceless"] .scene{inset:0}body[data-mode="faceless"] .scene-shell{background:rgba(16,23,25,.62)}body[data-mode="faceless"] .component-mount{inset:190px 70px 330px}body[data-mode="faceless"] .cv-card,body[data-mode="faceless"] .cv-cta{min-height:1160px;padding:90px 64px}body[data-mode="faceless"] .cv-title{font-size:92px}body[data-mode="faceless"] .cv-copy{font-size:34px}body[data-mode="faceless"] .meta{left:72px;top:96px}body[data-mode="faceless"] .synced-caption{bottom:145px}
body[data-mode="hybrid"] .component-mount{bottom:90px;height:300px}
body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{padding:26px 34px}
body[data-mode="hybrid"] .cv-title{font-size:42px}
body[data-mode="hybrid"] .cv-copy{font-size:22px;margin-top:10px}
body[data-mode="hybrid"] .cv-rule{margin:12px 0}
body[data-mode="hybrid"] .cv-metric-value{font-size:82px}
body[data-mode="hybrid"] .cv-list{gap:8px;margin-top:12px}
body[data-mode="hybrid"] .cv-list-item{font-size:18px;grid-template-columns:25px 1fr;gap:7px}
body[data-mode="hybrid"] .cv-list-mark{width:24px;height:24px}
body[data-mode="hybrid"] .cv-timeline{margin-top:12px}
body[data-mode="hybrid"] .cv-step{min-height:72px;padding:11px}
body[data-mode="hybrid"] .synced-caption{bottom:430px}
body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{padding:20px 28px}
body[data-mode="hybrid"] .cv-kicker{font-size:14px;margin-bottom:8px}
body[data-mode="hybrid"] .cv-title{font-size:34px;line-height:.96}
body[data-mode="hybrid"] .cv-copy{font-size:18px;line-height:1.1;margin-top:7px}
body[data-mode="hybrid"] .cv-metric-value{font-size:66px}
body[data-mode="hybrid"] .cv-metric{gap:12px}
body[data-mode="hybrid"] .cv-list{margin-top:8px}
body[data-mode="hybrid"] .cv-list-item{font-size:15px}
body[data-mode="hybrid"] .cv-step{min-height:58px;padding:8px}
body[data-mode="hybrid"] .cv-cta .cv-kicker{color:#e34a43}
body[data-mode="hybrid"] .cv-cta .cv-title{color:#f4f0e7}
.synced-caption i{color:#6f7773}

/* V2 — gramática derivada das referências aprovadas */
:root{--cv-bg:#071b1e;--cv-surface:#0b2528;--cv-ink:#f7f4ea;--cv-muted:#b8c5c1;--cv-accent:#29df9b;--cv-radius:18px;--cv-stroke:2px}
.frame-fill{background:radial-gradient(circle at 50% 20%,#12373a 0,#071b1e 58%,#041114 100%)}
.grid{background-image:linear-gradient(rgba(41,223,155,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(41,223,155,.045) 1px,transparent 1px);background-size:64px 64px}
.ambient{background:radial-gradient(circle,rgba(41,223,155,.24),rgba(41,223,155,0) 68%)}
.synced-caption span{padding:14px 24px;border-radius:9px;background:rgba(249,247,240,.94);font-size:36px;font-weight:600;box-shadow:0 8px 20px rgba(0,0,0,.28)}
body[data-mode="talking-head"] .synced-caption{bottom:650px}

body[data-mode="split"] #source-video{height:800px;object-position:center center}
body[data-mode="split"] .scene{inset:800px 0 0}
body[data-mode="split"] .scene-shell{background:radial-gradient(circle at 50% 25%,#12393c 0,#071b1e 64%)}
body[data-mode="split"] .component-mount{inset:58px 42px 78px}
body[data-mode="split"] .cv-card,body[data-mode="split"] .cv-cta{min-height:900px;padding:56px 50px;border-color:rgba(41,223,155,.16);background:rgba(7,27,30,.9)}
body[data-mode="split"] .cv-card{display:flex;flex-direction:column;align-items:center;text-align:center}
body[data-mode="split"] .cv-card::before{content:"";display:block;flex:0 0 285px;width:285px;margin:0 auto 35px;border:2px solid rgba(41,223,155,.24);border-radius:50%;background:radial-gradient(circle at 42% 38%,rgba(247,244,234,.92) 0 9%,rgba(41,223,155,.9) 10% 18%,rgba(15,58,61,.96) 19% 48%,rgba(4,17,20,.96) 49% 100%);box-shadow:0 0 0 18px rgba(41,223,155,.035),0 28px 65px rgba(0,0,0,.36)}
body[data-mode="split"] .cv-title{font-size:66px;max-width:850px}
body[data-mode="split"] .cv-copy{font-size:27px}
body[data-mode="split"] .cv-metric-value{font-size:116px}
body[data-mode="split"] .meta{left:48px;bottom:35px;font-size:15px;color:#5ddfb0}
body[data-mode="split"] .synced-caption{top:760px;bottom:auto}

body[data-mode="hybrid"] .component-mount{left:78px;right:78px;bottom:72px;height:210px}
body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{padding:22px 30px;border-left:6px solid var(--cv-accent);border-radius:16px;background:rgba(6,20,22,.94);box-shadow:0 14px 38px rgba(0,0,0,.36)}
body[data-mode="hybrid"] .cv-kicker{font-size:12px;margin-bottom:7px;letter-spacing:.18em}
body[data-mode="hybrid"] .cv-title{font-size:31px;line-height:.98;max-width:710px}
body[data-mode="hybrid"] .cv-copy{font-size:15px;line-height:1.08;margin-top:5px}
body[data-mode="hybrid"] .cv-rule{height:3px;margin:8px 0}
body[data-mode="hybrid"] .cv-progress-track{height:10px}
body[data-mode="hybrid"] .cv-metric-value{font-size:58px}
body[data-mode="hybrid"] .cv-list{grid-template-columns:repeat(3,1fr);margin-top:7px;gap:7px}
body[data-mode="hybrid"] .cv-list-item{font-size:13px;grid-template-columns:20px 1fr}
body[data-mode="hybrid"] .cv-list-mark{width:19px;height:19px}
body[data-mode="hybrid"] .cv-timeline{margin-top:7px;gap:6px}
body[data-mode="hybrid"] .cv-step{min-height:45px;padding:6px;border-top-width:3px}
body[data-mode="hybrid"] .synced-caption{bottom:320px}
body[data-mode="hybrid"] .cv-cta{background:rgba(6,20,22,.96)}
body[data-mode="hybrid"] .cv-cta .cv-kicker{color:#29df9b}

body[data-mode="faceless"] #source-video{filter:none;transform:none}
body[data-mode="faceless"] .scene-shell{background:radial-gradient(circle at 50% 25%,#123b3e 0,#071b1e 66%)}
body[data-mode="faceless"] .component-mount{inset:120px 64px 260px}
body[data-mode="faceless"] .cv-card,body[data-mode="faceless"] .cv-cta{display:flex;min-height:1450px;padding:100px 58px;flex-direction:column;justify-content:center;border-color:rgba(41,223,155,.16);background:rgba(6,26,29,.78)}
body[data-mode="faceless"] .cv-card::before{content:"";display:block;flex:0 0 430px;width:430px;margin:0 auto 70px;border:2px solid rgba(41,223,155,.25);border-radius:50%;background:radial-gradient(circle at 38% 34%,rgba(247,244,234,.95) 0 8%,rgba(41,223,155,.92) 9% 18%,rgba(20,70,72,.98) 19% 49%,rgba(3,16,19,.98) 50% 100%);box-shadow:0 0 0 24px rgba(41,223,155,.035),0 34px 80px rgba(0,0,0,.42)}
body[data-mode="faceless"] .cv-title{font-size:86px;text-align:center;max-width:900px}
body[data-mode="faceless"] .cv-kicker{text-align:center;color:#29df9b}
body[data-mode="faceless"] .cv-copy{text-align:center;align-self:center}
body[data-mode="faceless"] .cv-metric{display:grid;grid-template-columns:1fr auto}
body[data-mode="faceless"] .cv-metric-value{font-size:150px}
body[data-mode="faceless"] .cv-list{width:100%}
body[data-mode="faceless"] .synced-caption{bottom:105px}
body[data-mode="faceless"] #scene-proof .scene-shell,body[data-mode="faceless"] #scene-direction .scene-shell{background:linear-gradient(to bottom,rgba(4,17,20,.12),rgba(4,17,20,.82))}
body[data-mode="faceless"] #scene-proof .cv-card,body[data-mode="faceless"] #scene-direction .cv-card{min-height:620px;margin-top:720px;background:rgba(4,17,20,.84)}
body[data-mode="faceless"] #scene-proof .cv-card::before,body[data-mode="faceless"] #scene-direction .cv-card::before{display:none}
.cv-cta .cv-title{color:#f7f4ea}
.cv-cta .cv-kicker{color:#29df9b}

/* V3 — ícones específicos e nenhum motion genérico repetido */
.scene-visual{position:absolute;z-index:3;color:var(--cv-accent)}
.scene-icon{width:100%;height:100%;overflow:visible}
.scene-icon .draw,.scene-icon .hand,.scene-icon .route,.scene-icon .check,.scene-icon .person-line,.scene-icon .cursor,.scene-icon .ripple{stroke:currentColor;stroke-width:8;stroke-linecap:round;stroke-linejoin:round;fill:none}
.scene-icon .node,.scene-icon .step,.scene-icon .person{fill:currentColor}
.scene-icon .svg-number{fill:#f7f4ea;font:900 96px Inter,Arial,sans-serif}
body[data-mode="split"] .cv-card::before,body[data-mode="faceless"] .cv-card::before{display:none}
body[data-mode="split"] .scene-visual{top:48px;left:350px;width:380px;height:380px}
body[data-mode="split"] .component-mount{inset:410px 42px 55px}
body[data-mode="split"] .cv-card{min-height:520px;padding:35px 48px;justify-content:flex-start}
body[data-mode="split"] .cv-title{font-size:58px}
body[data-mode="faceless"] .scene-visual{top:150px;left:250px;width:580px;height:580px}
body[data-mode="faceless"] .component-mount{inset:690px 64px 250px}
body[data-mode="faceless"] .cv-card{min-height:920px;padding:65px 58px;justify-content:flex-start}
body[data-mode="faceless"] .cv-title{font-size:78px}
body[data-mode="faceless"] #scene-proof .scene-visual,body[data-mode="faceless"] #scene-direction .scene-visual{top:170px;left:700px;width:250px;height:250px}
body[data-mode="faceless"] #scene-proof .component-mount,body[data-mode="faceless"] #scene-direction .component-mount{inset:900px 64px 150px}
body[data-mode="faceless"] #scene-proof .cv-card,body[data-mode="faceless"] #scene-direction .cv-card{min-height:700px;margin-top:0}
body[data-mode="hybrid"] .scene-visual{left:95px;bottom:96px;width:150px;height:150px}
body[data-mode="hybrid"] .component-mount{left:78px;right:78px;bottom:72px;height:210px}
body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{padding-left:190px}
#scene-hook,#scene-question{--cv-accent:#f7bd3b}
#scene-promise,#scene-contrast{--cv-accent:#2be0a0}
#scene-proof,#scene-direction{--cv-accent:#49b8ff}
#scene-cta{--cv-accent:#ff5f72}

/* V4 — enquadramento seguro, legenda editorial e melhor ocupação */
#source-video-bg{display:none;position:absolute;z-index:0}
body[data-mode="split"] #source-video-bg{display:block;left:0;top:0;width:1080px;height:800px;object-fit:cover;object-position:center 24%;filter:blur(28px) brightness(.44) saturate(.8);transform:scale(1.08)}
body[data-mode="split"] #source-video{left:0;top:0;width:1080px;height:800px;object-fit:contain;object-position:center center;background:transparent}
body[data-mode="split"] .synced-caption{top:720px;left:90px;right:90px}
body[data-mode="split"] .synced-caption span{font-size:40px;padding:15px 25px}
body[data-mode="split"] .scene-visual{top:30px;width:350px;height:350px;left:365px}
body[data-mode="split"] .component-mount{inset:360px 42px 45px}
body[data-mode="split"] .cv-card{min-height:600px;padding:38px 54px;justify-content:center}
body[data-mode="split"] .cv-title{font-size:62px;line-height:.95}
body[data-mode="split"] .cv-copy{font-size:29px;max-width:820px}
body[data-mode="hybrid"] .synced-caption{bottom:330px}
body[data-mode="hybrid"] .synced-caption span,body[data-mode="faceless"] .synced-caption span,body[data-mode="talking-head"] .synced-caption span{font-size:40px}
body[data-mode="faceless"] .scene-visual{top:105px;width:520px;height:520px;left:280px}
body[data-mode="faceless"] .component-mount{inset:585px 64px 210px}
body[data-mode="faceless"] .cv-card{min-height:1040px;padding:70px 58px;justify-content:center}
body[data-mode="faceless"] #scene-proof .component-mount,body[data-mode="faceless"] #scene-direction .component-mount{inset:760px 64px 180px}
body[data-mode="faceless"] #scene-proof .cv-card,body[data-mode="faceless"] #scene-direction .cv-card{min-height:830px}

/* V5 — composição espelhada nas referências aprovadas */
:root{--cv-bg:#06181f;--cv-surface:#071d24;--cv-ink:#f5f1e8;--cv-muted:#b9c2c0;--cv-accent:#f3bc3d}
.frame-fill{background:#06181f}
.grid{background-image:radial-gradient(rgba(255,255,255,.07) 1px,transparent 1px);background-size:34px 34px;opacity:.32}
.ambient{opacity:.22}
#scene-hook,#scene-question,#scene-contrast{--cv-accent:#f3bc3d}
#scene-promise,#scene-proof,#scene-direction,#scene-cta{--cv-accent:#31d6a0}

body[data-mode="talking-head"] #source-video-bg,body[data-mode="hybrid"] #source-video-bg,body[data-mode="faceless"] #source-video-bg{display:none}
body[data-mode="talking-head"] .synced-caption{bottom:610px}
body[data-mode="talking-head"] .synced-caption span{font-size:38px;font-weight:500;padding:13px 22px;background:rgba(244,244,240,.78);box-shadow:none}

body[data-mode="split"] #source-video-bg{height:900px;object-position:center 24%;filter:blur(26px) brightness(.48);transform:scale(1.08)}
body[data-mode="split"] #source-video{height:900px;object-fit:contain}
body[data-mode="split"] .scene{inset:900px 0 0}
body[data-mode="split"] .scene-shell{background:radial-gradient(circle at 28% 30%,#0b3038 0,#06181f 62%)}
body[data-mode="split"] .scene-visual{left:70px;top:170px;width:390px;height:390px;padding:45px;border:2px solid rgba(255,255,255,.10);border-radius:50%;background:#08232c;box-shadow:0 28px 65px rgba(0,0,0,.32)}
body[data-mode="split"] .component-mount{left:485px;right:48px;top:175px;bottom:130px}
body[data-mode="split"] .cv-card,body[data-mode="split"] .cv-cta{min-height:0;height:100%;padding:32px 18px;justify-content:center;align-items:flex-start;text-align:left;border:0;background:transparent;box-shadow:none}
body[data-mode="split"] .cv-kicker{text-align:left;font-size:14px;color:var(--cv-accent)}
body[data-mode="split"] .cv-title{text-align:left;font-size:54px;line-height:.93;max-width:500px}
body[data-mode="split"] .cv-copy{text-align:left;font-size:23px;line-height:1.2;max-width:480px}
body[data-mode="split"] .cv-rule{width:100%;height:3px}
body[data-mode="split"] .cv-list{grid-template-columns:1fr;gap:8px}
body[data-mode="split"] .cv-list-item{font-size:20px}
body[data-mode="split"] .synced-caption{top:850px;left:80px;right:80px}
body[data-mode="split"] .synced-caption span{font-size:38px;font-weight:500;padding:13px 22px;background:#f4f3ee;box-shadow:none}
body[data-mode="split"] .meta{display:none}

body[data-mode="hybrid"] .component-mount{left:68px;right:68px;bottom:88px;height:205px}
body[data-mode="hybrid"] .cv-card,body[data-mode="hybrid"] .cv-cta{padding:24px 34px 22px 190px;border:0;border-left:5px solid var(--cv-accent);border-radius:18px;background:rgba(5,16,19,.95);box-shadow:0 16px 42px rgba(0,0,0,.42)}
body[data-mode="hybrid"] .scene-visual{left:95px;bottom:119px;width:120px;height:120px;padding:12px}
body[data-mode="hybrid"] .cv-kicker{font-size:13px;margin-bottom:7px;color:var(--cv-accent)}
body[data-mode="hybrid"] .cv-title{font-size:38px;line-height:.95}
body[data-mode="hybrid"] .cv-copy{font-size:16px;margin-top:7px}
body[data-mode="hybrid"] .cv-list{display:flex;gap:12px}
body[data-mode="hybrid"] .cv-list-item{font-size:13px}
body[data-mode="hybrid"] .synced-caption{bottom:340px}
body[data-mode="hybrid"] .synced-caption span{font-size:38px;font-weight:500;padding:13px 22px;background:rgba(244,244,240,.8);box-shadow:none}

body[data-mode="faceless"] .scene-shell{background:radial-gradient(circle at 50% 22%,#0b3038 0,#06181f 60%)}
body[data-mode="faceless"] .scene-visual{top:145px;left:250px;width:580px;height:580px;padding:85px;border:2px solid rgba(255,255,255,.10);border-radius:50%;background:#08232c;box-shadow:0 36px 90px rgba(0,0,0,.36)}
body[data-mode="faceless"] .component-mount{inset:760px 78px 245px}
body[data-mode="faceless"] .cv-card,body[data-mode="faceless"] .cv-cta{min-height:0;height:100%;padding:48px 25px;justify-content:flex-start;border:0;background:transparent;box-shadow:none}
body[data-mode="faceless"] .cv-kicker{font-size:17px;color:var(--cv-accent)}
body[data-mode="faceless"] .cv-title{font-size:76px;line-height:.92;text-align:center;max-width:900px}
body[data-mode="faceless"] .cv-copy{font-size:27px;max-width:770px}
body[data-mode="faceless"] .cv-list{max-width:720px;margin:32px auto 0}
body[data-mode="faceless"] .cv-list-item{font-size:25px}
body[data-mode="faceless"] .synced-caption{bottom:110px}
body[data-mode="faceless"] .synced-caption span{font-size:38px;font-weight:500;padding:13px 22px;background:#f4f3ee;box-shadow:none}
body[data-mode="faceless"] .meta{display:none}
body[data-mode="faceless"] #scene-proof .scene-visual,body[data-mode="faceless"] #scene-direction .scene-visual{top:150px;left:670px;width:280px;height:280px;padding:40px}
body[data-mode="faceless"] #scene-proof .component-mount,body[data-mode="faceless"] #scene-direction .component-mount{inset:900px 74px 210px}
body[data-mode="faceless"] #scene-proof .cv-card,body[data-mode="faceless"] #scene-direction .cv-card{min-height:0;height:100%;padding:45px 28px;background:rgba(4,17,20,.78);border-radius:20px}
`;

const appScript = (sceneData, captionData) => `
(() => {
  const root = document.getElementById('root');
  const captions = ${js(captionData)};
  const scenes = ${js(sceneData)};
  const renderComponent = data => {
    const d = JSON.parse(data);
    const api = window.CodexVideo;
    if (d.kind === 'progress') return api.progress(d);
    if (d.kind === 'metric') return api.metric(d);
    if (d.kind === 'checklist') return api.checklist({ ...d, items: d.items || [] });
    if (d.kind === 'comparison') return api.comparison(d);
    if (d.kind === 'timeline') return api.timeline({ ...d, steps: d.items || [] });
    if (d.kind === 'cta') return api.cta(d);
    return api.alert(d);
  };
  Array.from(root.querySelectorAll('.component-mount')).forEach(mount => { mount.innerHTML = renderComponent(mount.dataset.component); });
  captions.forEach((group, groupIndex) => {
    const clip = document.createElement('div');
    clip.id = 'caption-' + groupIndex;
    clip.className = 'clip synced-caption';
    clip.dataset.start = group.start;
    clip.dataset.duration = Math.max(.12, group.end - group.start);
    clip.dataset.trackIndex = '9';
    const words = Array.isArray(group.words) ? group.words : [];
    clip.innerHTML = '<span>' + words.map((word, wordIndex) => '<i id="caption-' + groupIndex + '-word-' + wordIndex + '">' + word.text + '</i>').join(' ') + '</span>';
    root.appendChild(clip);
  });
  const tl = window.__codexTl || window.gsap.timeline({ paused: true });
  window.__codexTl = tl;
  window.__timelines = window.__timelines || {};
  window.__timelines[root.dataset.compositionId] = tl;
  const enterText = (card, start, mode) => {
    const title = card?.querySelector('.cv-title');
    const kicker = card?.querySelector('.cv-kicker');
    const details = card?.querySelectorAll('.cv-copy,.cv-list-item,.cv-step,.cv-compare-panel,.cv-metric-value,.cv-progress-track');
    if (mode === 'slam') {
      if (title) tl.fromTo(title,{scale:1.55,rotation:-3,opacity:0},{scale:1,rotation:0,opacity:1,duration:.48,ease:'expo.out'},start+.15);
    } else if (mode === 'side') {
      if (title) tl.fromTo(title,{x:-150,opacity:0},{x:0,opacity:1,duration:.55,ease:'power4.out'},start+.18);
    } else if (mode === 'rise') {
      if (title) tl.fromTo(title,{y:110,rotation:2,opacity:0},{y:0,rotation:0,opacity:1,duration:.62,ease:'back.out(1.5)'},start+.2);
    } else {
      if (title) tl.fromTo(title,{scale:.65,opacity:0},{scale:1,opacity:1,duration:.52,ease:'back.out(2)'},start+.18);
    }
    if (kicker) tl.fromTo(kicker,{opacity:0,y:-18},{opacity:1,y:0,duration:.3},start+.1);
    if (details?.length) tl.fromTo(details,{opacity:0,y:24},{opacity:1,y:0,duration:.38,stagger:.08,ease:'power3.out'},start+.48);
  };
  Array.from(document.querySelectorAll('.scene')).forEach((scene, index) => {
    const spec = scenes[index];
    const card = scene.querySelector('.cv-component');
    const id = scene.dataset.sceneId;
    const icon = scene.querySelector('.scene-icon');
    if (id === 'hook') {
      enterText(card,spec.start,'slam');
      tl.fromTo(icon,{scale:.25,rotation:-35,opacity:0},{scale:1,rotation:0,opacity:1,duration:.62,ease:'back.out(1.8)'},spec.start+.05);
      tl.fromTo(scene.querySelector('.hand'),{rotation:-110,transformOrigin:'160px 170px'},{rotation:250,duration:Math.max(1.2,spec.duration-.6),ease:'power2.inOut'},spec.start+.35);
    } else if (id === 'promise') {
      enterText(card,spec.start,'rise');
      tl.fromTo(icon,{rotationY:90,opacity:0},{rotationY:0,opacity:1,duration:.6,ease:'power3.out'},spec.start+.05);
      const number=scene.querySelector('.svg-number'); if(number) tl.fromTo(number,{scale:.1,opacity:0,transformOrigin:'160px 190px'},{scale:1,opacity:1,duration:.5,ease:'back.out(2.4)'},spec.start+.48);
    } else if (id === 'proof') {
      enterText(card,spec.start,'side');
      const route=scene.querySelector('.route'); if(route) tl.fromTo(route,{strokeDasharray:900,strokeDashoffset:900},{strokeDashoffset:0,duration:1.1,ease:'power2.inOut'},spec.start+.12);
      tl.fromTo(scene.querySelectorAll('.node'),{scale:0,transformOrigin:'center'},{scale:1,duration:.38,stagger:.22,ease:'back.out(2)'},spec.start+.32);
      tl.fromTo(scene.querySelector('.check'),{opacity:0,scale:.2,transformOrigin:'center'},{opacity:1,scale:1,duration:.4,ease:'back.out(2)'},spec.start+1.05);
    } else if (id === 'question') {
      enterText(card,spec.start,'side');
      tl.fromTo(icon,{rotation:-8,opacity:0},{rotation:0,opacity:1,duration:.5,ease:'power3.out'},spec.start+.08);
      tl.to(icon,{rotation:3,duration:.65,yoyo:true,repeat:3,ease:'sine.inOut'},spec.start+.65);
    } else if (id === 'contrast') {
      enterText(card,spec.start,'rise');
      tl.fromTo(scene.querySelectorAll('.step'),{scaleY:0,transformOrigin:'bottom'},{scaleY:1,duration:.55,stagger:.18,ease:'back.out(1.6)'},spec.start+.15);
      tl.fromTo(scene.querySelectorAll('.person,.person-line'),{x:-70,opacity:0},{x:0,opacity:1,duration:.5,ease:'power3.out'},spec.start+.82);
    } else if (id === 'direction') {
      enterText(card,spec.start,'pop');
      tl.fromTo(icon,{scale:.35,opacity:0},{scale:1,opacity:1,duration:.55,ease:'back.out(2)'},spec.start+.08);
      tl.fromTo(scene.querySelector('.needle'),{rotation:-140,transformOrigin:'160px 160px'},{rotation:35,duration:1.15,ease:'elastic.out(1,.35)'},spec.start+.38);
    } else {
      enterText(card,spec.start,'slam');
      const cursor=scene.querySelector('.cursor'); if(cursor) tl.fromTo(cursor,{x:-110,y:-90,opacity:0},{x:0,y:0,opacity:1,duration:.62,ease:'power3.out'},spec.start+.08);
      tl.fromTo(scene.querySelectorAll('.ripple'),{scale:.15,opacity:.8,transformOrigin:'198px 181px'},{scale:1.35,opacity:0,duration:.7,stagger:.16,ease:'power2.out'},spec.start+.58);
    }
    const a = scene.querySelector('.ambient-a');
    const b = scene.querySelector('.ambient-b');
    if (a) tl.fromTo(a, { opacity:.35, scale:.9 }, { opacity:.7, scale:1.08, duration:Math.max(1,spec.duration-.5), ease:'sine.inOut' }, spec.start+.15);
    if (b) tl.fromTo(b, { opacity:.2, x:-20 }, { opacity:.55, x:28, duration:Math.max(1,spec.duration-.5), ease:'none' }, spec.start+.15);
    tl.to(scene, { opacity:0, duration:.22, ease:'power2.in' }, Math.max(spec.start, spec.start+spec.duration-.24));
  });
  captions.forEach((group, groupIndex) => {
    const clip = document.getElementById('caption-' + groupIndex);
    tl.fromTo(clip, { y:18, scale:.985 }, { y:0, scale:1, duration:.16, ease:'power3.out' }, group.start);
    const words = Array.isArray(group.words) ? group.words : [];
    words.forEach((word, wordIndex) => tl.set('#caption-' + groupIndex + '-word-' + wordIndex, { color:'#111819', opacity:1 }, word.start));
    tl.to(clip, { y:-8, duration:.12, ease:'power2.in' }, Math.max(group.start, group.end-.12));
  });
})();
`;

for (const project of ["C0207", "IMG_5053"]) {
  const projectDir = path.join(validation, project);
  const plan = JSON.parse(
    fs.readFileSync(path.join(projectDir, "project-plan.json"), "utf8"),
  );
  const transcript = JSON.parse(
    fs.readFileSync(path.join(projectDir, "transcript-edited.json"), "utf8"),
  );
  const captionGroups = groups(transcript.words);
  for (const format of ["talking-head", "split", "hybrid", "faceless"]) {
  const publicDir = path.join(projectDir, "hf-v5", format, "public");
    fs.mkdirSync(publicDir, { recursive: true });
    fs.copyFileSync(
      path.join(projectDir, "base_vertical.mp4"),
      path.join(publicDir, "base.mp4"),
    );
    fs.copyFileSync(vendor, path.join(publicDir, "gsap.min.js"));
    fs.copyFileSync(
      path.join(system, "components", "codex-components.css"),
      path.join(publicDir, "codex-components.css"),
    );
    fs.copyFileSync(
      path.join(system, "components", "codex-components.js"),
      path.join(publicDir, "codex-components.js"),
    );
    fs.writeFileSync(
      path.join(publicDir, "index.html"),
      indexHtml(project, format, plan, captionGroups),
      "utf8",
    );
    fs.writeFileSync(path.join(publicDir, "style.css"), style, "utf8");
    fs.writeFileSync(
      path.join(publicDir, "app.js"),
      appScript(plan.scenes, captionGroups),
      "utf8",
    );
    console.log(`${project}/${format}: ${captionGroups.length} legendas`);
  }
}
