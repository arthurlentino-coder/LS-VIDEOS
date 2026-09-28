/* ===== FACELESS EDITORIAL — framework JS compartilhado (não editar por projeto) =====
   Expõe window.HF com os helpers. Depende de gsap + lottie (carregar antes). */
(function () {
  const HF = {};

  // pré-render de um Lottie em frames de canvas (seek-safe no render do HyperFrames)
  HF.frames = async function (data, w, h, cap) {
    const box = document.createElement("div");
    box.style.cssText = "position:absolute;left:-9999px;top:-9999px;width:" + w + "px;height:" + h + "px";
    document.body.appendChild(box);
    const a = lottie.loadAnimation({ container: box, renderer: "svg", loop: false, autoplay: false, animationData: data });
    await new Promise(r => { if (a.isLoaded) r(); else a.addEventListener("DOMLoaded", r); });
    const total = a.totalFrames, svg = box.querySelector("svg"), out = [], N = cap ? Math.min(cap, total) : total;
    for (let k = 0; k < N; k++) {
      const fr = Math.round(k * (total - 1) / (N - 1 || 1));
      a.goToAndStop(fr, true);
      const xml = new XMLSerializer().serializeToString(svg), im = new Image();
      await new Promise((r, j) => { im.onload = r; im.onerror = j; im.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml))); });
      const c = document.createElement("canvas"); c.width = w; c.height = h; c.getContext("2d").drawImage(im, 0, 0, w, h); out.push(c);
    }
    box.remove(); return out;
  };

  // player que desenha o frame do personagem no canvas (loop dentro da cena)
  HF.player = function (fs, fr, id, w, h) {
    const ctx = document.getElementById(id).getContext("2d"), period = fs.length / fr;
    function draw(i) { ctx.clearRect(0, 0, w, h); ctx.drawImage(fs[Math.max(0, Math.min(fs.length - 1, i))], 0, 0); }
    draw(0);
    return { loop: e => { if (e >= 0) draw(Math.floor((e % period) / period * fs.length)); } };
  };

  // quebra cada headline em spans .word (para animar palavra a palavra)
  HF.wordSplit = function () {
    document.querySelectorAll(".headline").forEach(function (h) {
      [].slice.call(h.childNodes).forEach(function (n) {
        if (n.nodeType === 3 && n.textContent.trim()) {
          const f = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (p) {
            if (!p.trim()) { f.appendChild(document.createTextNode(p)); return; }
            const s = document.createElement("span"); s.className = "word"; s.textContent = p; f.appendChild(s);
          });
          h.replaceChild(f, n);
        }
      });
      h.querySelectorAll("b").forEach(function (b) { b.classList.add("word"); });
    });
  };

  HF.timeline = function () {
    const tl = gsap.timeline({ paused: true }), q = t => Math.round(t * 30) / 30;
    return { tl, q };
  };

  // entrada de uma cena de MOTION (disco + arte + copy + badges + sparks)
  HF.enter = function (tl, q, id, at) {
    tl.fromTo(id + " .art", { opacity: 0, y: -28, scale: .92 }, { opacity: 1, y: 0, scale: 1, duration: .7, ease: "power3.out" }, q(at + .05));
    tl.fromTo(id + " .disc", { opacity: 0, scale: .74 }, { opacity: 1, scale: 1, duration: .62, ease: "back.out(1.35)" }, q(at + .1));
    tl.fromTo(id + " .kick", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .4, ease: "power3.out" }, q(at + .28));
    tl.fromTo(id + " .headline .word", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: .46, ease: "power4.out", stagger: .05 }, q(at + .42));
    tl.fromTo(id + " .sub", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .44, ease: "power3.out" }, q(at + .8));
    tl.fromTo(id + " .badge", { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: .4, ease: "back.out(1.4)", stagger: .1 }, q(at + .55));
    tl.fromTo(id + " .spark", { opacity: 0, scale: .3 }, { opacity: .7, scale: 1, duration: .34, ease: "back.out(2)", stagger: .08 }, q(at + .76));
  };

  // entrada de uma cena de B-ROLL (scrim + copy no rodapé)
  HF.benter = function (tl, q, id, at) {
    tl.fromTo(id + " .bgrade", { opacity: .35 }, { opacity: 1, duration: .4, ease: "power2.out" }, q(at));
    tl.fromTo(id + " .kick", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .4, ease: "power3.out" }, q(at + .2));
    tl.fromTo(id + " .headline .word", { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: .46, ease: "power4.out", stagger: .05 }, q(at + .34));
    tl.fromTo(id + " .sub", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .44, ease: "power3.out" }, q(at + .72));
  };

  // idle: a arte flutua devagar depois da entrada (nunca congela). s,e = início/fim da cena
  HF.idle = function (tl, q, id, s, e) {
    const st = s + 1.1;
    if (e - st > 1.2) tl.to(id + " .art", { y: -9, duration: 1.3, ease: "sine.inOut", yoyo: true, repeat: Math.max(1, Math.floor((e - st) / 1.3) - 1) }, q(st));
  };

  // dirige o loop de um personagem entre [s,e] (offset = s + pequeno atraso da entrada)
  HF.charLoop = function (tl, pl, s, e, offset) {
    const off = offset == null ? s + 0.2 : offset;
    tl.to({}, { duration: e - off, ease: "none", onUpdate: () => pl.loop(tl.time() - off) }, off);
  };

  // animação padrão do CTA (card entra + cursor + toque + ring). Elementos: #<id>-card #<id>-cursor #<id>-ring
  HF.cta = function (tl, q, id, at) {
    tl.fromTo(id + "-card", { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: .42, ease: "back.out(2.2)", transformOrigin: "50% 50%" }, q(at + .1));
    tl.fromTo(id + "-cursor", { opacity: 0, x: 44, y: 36 }, { opacity: 1, x: 0, y: 0, duration: .5, ease: "power3.out" }, q(at + .4));
    tl.to(id + "-card", { scale: .93, duration: .1, ease: "power2.in", yoyo: true, repeat: 1, transformOrigin: "50% 50%" }, q(at + .8));
    tl.fromTo(id + "-ring", { opacity: .8, scale: .5, transformOrigin: "50% 50%" }, { opacity: 0, scale: 1.5, duration: .7, ease: "power2.out" }, q(at + .85));
  };

  window.HF = HF;
})();
