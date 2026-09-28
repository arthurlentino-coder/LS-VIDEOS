(() => {
  const esc = (value) => String(value ?? "").replace(/[&<>\"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[char]);
  const list = items => items.map(item => `<div class="cv-list-item"><span class="cv-list-mark">✓</span><span>${esc(item)}</span></div>`).join("");

  window.CodexVideo = {
    progress({ kicker = "PROGRESSO", title, copy = "", value = 65 }) {
      return `<section class="cv-component cv-card cv-progress"><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><div class="cv-rule"></div><div class="cv-progress-track"><div class="cv-progress-fill" style="--cv-progress:${Number(value)}%"></div></div><p class="cv-copy">${esc(copy)}</p></section>`;
    },
    checklist({ kicker = "PASSO A PASSO", title, items = [] }) {
      return `<section class="cv-component cv-card"><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><div class="cv-list">${list(items)}</div></section>`;
    },
    metric({ kicker = "NÚMERO-CHAVE", title, value, copy = "" }) {
      return `<section class="cv-component cv-card cv-metric"><div><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><p class="cv-copy">${esc(copy)}</p></div><strong class="cv-metric-value">${esc(value)}</strong></section>`;
    },
    comparison({ kicker = "COMPARAÇÃO", title, left, right }) {
      return `<section class="cv-component cv-card"><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><div class="cv-rule"></div><div class="cv-compare"><div class="cv-compare-panel">${esc(left)}</div><div class="cv-compare-panel">${esc(right)}</div></div></section>`;
    },
    timeline({ kicker = "CAMINHO", title, steps = [] }) {
      const body = steps.map((step, index) => `<div class="cv-step"><span class="cv-kicker">0${index + 1}</span><div class="cv-copy">${esc(step)}</div></div>`).join("");
      return `<section class="cv-component cv-card"><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><div class="cv-timeline" style="--cv-steps:${steps.length}">${body}</div></section>`;
    },
    alert({ kicker = "ATENÇÃO", title, copy = "" }) {
      return `<section class="cv-component cv-card cv-alert"><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2><p class="cv-copy">${esc(copy)}</p></section>`;
    },
    cta({ kicker = "PRÓXIMO PASSO", title }) {
      return `<section class="cv-component cv-cta"><div><p class="cv-kicker">${esc(kicker)}</p><h2 class="cv-title">${esc(title)}</h2></div></section>`;
    },
    animate(tl, root, start = 0, duration = 3) {
      const hero = root.querySelector(".cv-title");
      const kicker = root.querySelector(".cv-kicker");
      const rule = root.querySelector(".cv-rule");
      const details = root.querySelectorAll(".cv-copy,.cv-list-item,.cv-step,.cv-compare-panel,.cv-metric-value");
      if (kicker) tl.fromTo(kicker, { x: -42 }, { x: 0, duration: .38, ease: "power3.out" }, start + .12);
      if (hero) tl.fromTo(hero, { y: 54, scale: .97 }, { y: 0, scale: 1, duration: .56, ease: "expo.out" }, start + .2);
      if (rule) tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: .46, ease: "power2.out" }, start + .34);
      if (details.length) tl.fromTo(details, { y: 28 }, { y: 0, duration: .42, stagger: .07, ease: "back.out(1.35)" }, start + .42);
      tl.to(root, { y: -7, duration: 1.1, yoyo: true, repeat: Math.max(0, Math.floor((duration - 1.2) / 2.2)), ease: "sine.inOut" }, start + 1.1);
      return tl;
    }
  };
})();
