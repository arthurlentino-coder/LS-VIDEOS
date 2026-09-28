import fs from 'node:fs';
import path from 'node:path';

const root = 'C:/Users/betat/Desktop/VIDEOS/_codex/validation/C0207';
const app = fs.readFileSync(path.join(root, 'hf-v5/talking-head/public/app.js'), 'utf8');
const match = app.match(/const captions = (\[[\s\S]*?\]);\n  const scenes/);
if (!match) throw new Error('Caption payload not found');
const groups = JSON.parse(match[1]);
const payload = JSON.stringify(groups, null, 2);
const code = `(()=>{const groups=${payload};const host=document.getElementById('captions');if(!host)return;host.innerHTML=groups.map((g,i)=>{const end=Math.max(g.end,g.start+.24);return '<div class="caption synced-caption clip" id="sync-cap-'+i+'" data-start="'+g.start+'" data-duration="'+(end-g.start).toFixed(3)+'" data-track-index="8"><span>'+g.words.map((w,j)=>'<i id="sync-word-'+i+'-'+j+'">'+w.text+'</i>').join(' ')+'</span></div>'}).join('');const root=document.querySelector('[data-composition-id]');const tl=window.__timelines&&window.__timelines[root.dataset.compositionId];if(!tl)return;groups.forEach((g,i)=>{tl.fromTo('#sync-cap-'+i,{opacity:0,y:18,scale:.98},{opacity:1,y:0,scale:1,duration:.16,ease:'power2.out'},g.start+.01);g.words.forEach((w,j)=>{tl.to('#sync-word-'+i+'-'+j,{color:'#111819',opacity:1,duration:.04},w.start);if(j>0)tl.to('#sync-word-'+i+'-'+(j-1),{color:'#8b928e',opacity:.72,duration:.04},w.start);});});})();\n`;
const css = `.synced-caption{position:absolute;left:80px;right:80px;z-index:30;text-align:center}.synced-caption span{display:inline-block;max-width:880px;padding:16px 26px;border-radius:12px;background:rgba(247,244,236,.96);color:#111819;font:500 38px/1.12 Inter,Arial,sans-serif;box-shadow:0 12px 35px #0008}.synced-caption i{font-style:normal;color:#8b928e;opacity:.72}.synced-caption i:first-child{color:#111819;opacity:1}\n`;
for (const format of ['talking-head','split','hybrid','faceless']) {
  const dir = path.join(root, 'reference-template-v1', format);
  fs.writeFileSync(path.join(dir, 'captions-sync.js'), code);
  fs.writeFileSync(path.join(dir, 'caption-standard.css'), css);
}
console.log(`Generated ${groups.length} caption groups for four reference templates.`);
