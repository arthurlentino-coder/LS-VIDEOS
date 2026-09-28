// gen_cues.mjs — transcript (ElevenLabs Scribe) -> assets/cues.js p/ o karaokê embutido.
// uso: node gen_cues.mjs <transcript.json> [saida=assets/cues.js]
import fs from 'node:fs';

const src = process.argv[2];
const out = process.argv[3] || 'assets/cues.js';
if (!src) { console.error('uso: node gen_cues.mjs <transcript.json> [saida]'); process.exit(1); }

const d = JSON.parse(fs.readFileSync(src, 'utf8'));
const words = (d.words || []).filter(w => w.type === 'word' && typeof w.start === 'number');

// agrupa em cues curtas (pill de 1–2 linhas): quebra em pontuação forte, gap>0.55s, >30 chars, >6 palavras
const cues = [];
let cur = [];
const flush = () => { if (cur.length) { cues.push(cur); cur = []; } };
for (let i = 0; i < words.length; i++) {
  const w = words[i];
  cur.push({ t: +w.start.toFixed(3), tx: w.text });
  const txt = cur.map(x => x.tx).join(' ');
  const endsSent = /[.?!]$/.test(w.text);
  const gap = words[i + 1] ? words[i + 1].start - w.end : 99;
  if (endsSent || gap > 0.55 || txt.length > 30 || cur.length >= 6) flush();
}
flush();

const arr = cues.map(ws => ({ s: ws[0].t, e: +(ws[ws.length - 1].t + 0.6).toFixed(3), words: ws }));
// nunca deixar uma pill invadir a próxima (senão renderiza duas sobrepostas)
for (let i = 0; i < arr.length - 1; i++) {
  if (arr[i].e > arr[i + 1].s - 0.03) arr[i].e = +(arr[i + 1].s - 0.03).toFixed(3);
}
fs.writeFileSync(out, 'window.__cues=' + JSON.stringify(arr) + ';', 'utf8');
console.log(`cues: ${arr.length} pills, ${words.length} palavras -> ${out}`);
