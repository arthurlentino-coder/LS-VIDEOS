import re, sys, pathlib
IDLE_FN = "          // idle: flutuacao/respiro continuo p/ o grafico NAO congelar depois da entrada.\n          function idle(id, at, endt) { var span = endt - at; if (span < 0.7) return; var cyc = 1.5; var reps = Math.max(1, Math.round(span / cyc)); tl.to(id, { y: -6, scale: 1.04, duration: cyc / 2, ease: 'sine.inOut', yoyo: true, repeat: reps * 2 - 1, transformOrigin: '50% 50%' }, q(at)); }\n"
for n in [1,2,3,4]:
    p = pathlib.Path(f"projects/CPA_{n}/edit/hf/split/public/index.html")
    s = p.read_text(encoding="utf-8")
    if "function idle(" in s:
        print(f"CPA_{n}: idle ja presente, pulando"); continue
    # scene windows
    scenes = re.findall(r'id="(b\d+)"\s+data-start="([\d.]+)"\s+data-duration="([\d.]+)"', s)
    calls = []
    for sid, st, du in scenes:
        st=float(st); du=float(du); end=round(st+du,3)
        calls.append(f"idle('#{sid}-g', {round(st+0.6,3)}, {end});")
    calls_line = "          // idle continuo por cena (evita congelar apos a entrada)\n          " + " ".join(calls) + "\n"
    # insere a funcao apos subIn
    s = re.sub(r"(function subIn\(id, at\) \{[^\n]*\}\n)", r"\1"+IDLE_FN, s, count=1)
    # insere as chamadas antes de window.__timelines
    s = s.replace("          window.__timelines = window.__timelines || {};",
                  calls_line + "\n          window.__timelines = window.__timelines || {};", 1)
    p.write_text(s, encoding="utf-8")
    print(f"CPA_{n}: {len(scenes)} cenas -> idle injetado")
