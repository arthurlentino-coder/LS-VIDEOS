import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const formats = JSON.parse(fs.readFileSync(path.join(root, "presets", "formats.json"), "utf8"));
const grammar = JSON.parse(fs.readFileSync(path.join(root, "presets", "visual-grammar.json"), "utf8"));

export function inspectManifest(manifest, baseDir = process.cwd()) {
  const errors = [];
  const warnings = [];
  const fail = (message) => errors.push(message);
  const warn = (message) => warnings.push(message);
  const preset = formats.formats[manifest.format];

  if (!preset) fail(`Formato desconhecido: ${manifest.format}`);
  if (manifest.canvas?.width !== 1080 || manifest.canvas?.height !== 1920) fail("Canvas deve ser 1080x1920.");
  if (!manifest.canvas?.fps) fail("FPS não definido.");
  if (!manifest.source?.edl || !manifest.source?.transcript) fail("EDL e transcrição são obrigatórias.");
  if (!manifest.source?.wordTimed) fail("A transcrição precisa ter timestamps por palavra.");
  if (!manifest.captions?.mappedThroughEdl) fail("Legendas precisam ser remapeadas pela EDL.");
  if ((manifest.captions?.maxWords ?? 99) > 6) fail("Legenda excede o limite de 6 palavras por bloco.");
  if ((manifest.captions?.maxDuration ?? 99) > 2.2) fail("Legenda excede 2,2 segundos por bloco.");
  if (preset && manifest.captions?.position !== preset.captionZone.name) fail(`Legenda de ${manifest.format} deve usar a zona '${preset.captionZone.name}'.`);

  const scenes = manifest.scenes ?? [];
  if (!scenes.length) fail("O mapa de ritmo não possui cenas.");
  if (!manifest.rhythm?.pattern || !manifest.rhythm?.peakBeat) fail("Ritmo e beat de pico precisam ser declarados.");
  if ((manifest.rhythm?.visualChangeMaxSeconds ?? 99) > 5) fail("Mudança visual deve ocorrer no máximo a cada 5 segundos.");

  const ids = new Set();
  for (const scene of scenes) {
    if (!scene.id) fail("Cena sem id.");
    if (ids.has(scene.id)) fail(`Id de cena duplicado: ${scene.id}`);
    ids.add(scene.id);
    if (!grammar.families[scene.intent]) fail(`Cena ${scene.id}: intenção visual desconhecida '${scene.intent}'.`);
    if (!scene.concept || !scene.mood) fail(`Cena ${scene.id}: conceito e mood são obrigatórios.`);
    if (manifest.format !== "talking-head" && !scene.components?.length) fail(`Cena ${scene.id}: nenhum componente definido.`);
    if (manifest.format !== "talking-head" && (scene.motionVerbs?.length ?? 0) < 2) fail(`Cena ${scene.id}: use pelo menos 2 verbos de movimento.`);
    if (manifest.format !== "talking-head" && !scene.ambientMotion) fail(`Cena ${scene.id}: motion estático; defina um idle determinístico.`);
    if (manifest.format !== "talking-head" && (scene.occupancy ?? 0) < .62) fail(`Cena ${scene.id}: ocupação do quadro abaixo de 62%.`);
    if (manifest.format !== "talking-head" && !scene.artContained) fail(`Cena ${scene.id}: arte não confirmada dentro da caixa/zona segura.`);
    if (["split", "hybrid"].includes(manifest.format) && !scene.protectsPresenter) fail(`Cena ${scene.id}: proteção de rosto/braços não confirmada.`);
    if (manifest.format !== "talking-head" && (scene.duration ?? 0) > 5 && (scene.motionVerbs?.length ?? 0) < 3) warn(`Cena ${scene.id}: duração acima de 5s pede desenvolvimento visual adicional.`);
  }

  if (manifest.format === "talking-head" && scenes.some(scene => scene.components?.length)) fail("Talking Head deve permanecer limpo, sem componentes gráficos.");
  if (manifest.format === "hybrid") {
    if (manifest.hybrid?.yellowStrip !== false) fail("Hybrid não pode ter faixa amarela.");
    if (!manifest.hybrid?.cardInsideSafeZone) fail("Hybrid precisa confirmar o card dentro da zona segura.");
  }
  if (manifest.format === "faceless") {
    if (!manifest.faceless?.brollUsed) fail("Faceless deve usar b-roll editorial.");
    if (new Set(manifest.faceless?.montageTypes ?? []).size < 3) fail("Faceless precisa de pelo menos 3 tipos de montagem.");
  }

  if (manifest.html) {
    const htmlPath = path.resolve(baseDir, manifest.html);
    if (!fs.existsSync(htmlPath)) fail(`HTML não encontrado: ${htmlPath}`);
    else {
      const html = fs.readFileSync(htmlPath, "utf8");
      for (const banned of grammar.discardedArtwork) if (html.toLocaleUpperCase("pt-BR").includes(banned.toLocaleUpperCase("pt-BR"))) fail(`Arte/texto descartado encontrado no HTML: ${banned}`);
      if (/repeat\s*:\s*-1/.test(html)) fail("Motion infinito não determinístico encontrado: repeat:-1.");
      if (/\b(?:Date\.now|Math\.random|performance\.now)\b/.test(html)) fail("Fonte de tempo/aleatoriedade não determinística encontrada.");
      if (/data-role=["']header["']/.test(html) && ["split", "hybrid", "faceless"].includes(manifest.format)) fail("Cabeçalho proibido encontrado no formato.");
    }
  }

  return { ok: errors.length === 0, errors, warnings };
}

function main() {
  const input = process.argv[2];
  if (!input) {
    console.error("Uso: node video-qa.mjs <codex-video.json>");
    process.exit(2);
  }
  const full = path.resolve(input);
  const result = inspectManifest(JSON.parse(fs.readFileSync(full, "utf8")), path.dirname(full));
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.ok ? 0 : 1);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
