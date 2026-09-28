import fs from "node:fs";
import path from "node:path";

const input = process.argv[2];
if (!input) {
  console.error("Uso: node create_manifests.mjs <project-plan.json>");
  process.exit(2);
}

const plan = JSON.parse(fs.readFileSync(input, "utf8"));
const dir = path.dirname(path.resolve(input));
const captionPositions = {
  "talking-head": "lower-third",
  split: "divider",
  hybrid: "above-card",
  faceless: "safe-base"
};

for (const format of ["talking-head", "split", "hybrid", "faceless"]) {
  const scenes = plan.scenes.map(scene => format === "talking-head" ? {
    ...scene,
    components: [],
    motionVerbs: [],
    ambientMotion: false,
    occupancy: 1,
    artContained: true,
    protectsPresenter: true
  } : scene);
  const manifest = {
    schemaVersion: 1,
    project: plan.project,
    format,
    canvas: plan.canvas,
    source: plan.source,
    captions: { ...plan.captions, position: captionPositions[format] },
    rhythm: plan.rhythm,
    scenes,
    faceless: format === "faceless" ? plan.faceless : { brollUsed: false, montageTypes: [] },
    hybrid: format === "hybrid" ? plan.hybrid : { yellowStrip: false, cardInsideSafeZone: true },
    output: `output/${plan.project}_${format}_V1_REVIEW.mp4`
  };
  const target = path.join(dir, `codex-video-${format}.json`);
  fs.writeFileSync(target, JSON.stringify(manifest, null, 2), "utf8");
  console.log(target);
}

