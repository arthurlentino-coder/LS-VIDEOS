import fs from "node:fs";
import path from "node:path";

const [transcriptFile, edlFile, outputFile] = process.argv.slice(2);
if (!outputFile) {
  console.error("Uso: node map_edl.mjs <transcript.json> <edl.json> <output.json>");
  process.exit(2);
}

const transcript = JSON.parse(fs.readFileSync(transcriptFile, "utf8"));
const edl = JSON.parse(fs.readFileSync(edlFile, "utf8"));
const sourceWords = transcript.words ?? transcript.segments?.flatMap(segment => segment.words ?? []) ?? [];
const words = [];
let cursor = 0;

for (let rangeIndex = 0; rangeIndex < edl.ranges.length; rangeIndex++) {
  const range = edl.ranges[rangeIndex];
  const duration = range.end - range.start;
  for (const word of sourceWords) {
    if (word.start < range.start - 0.02 || word.end > range.end + 0.02) continue;
    words.push({
      ...word,
      id: `w${words.length}`,
      start: Number((cursor + word.start - range.start).toFixed(3)),
      end: Number((cursor + word.end - range.start).toFixed(3)),
      sourceStart: word.start,
      sourceEnd: word.end,
      rangeIndex
    });
  }
  cursor += duration;
}

const result = { duration: Number(cursor.toFixed(3)), ranges: edl.ranges, words };
fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), "utf8");
console.log(`${outputFile}: ${words.length} palavras em ${result.duration}s`);

