#!/usr/bin/env node
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";

const API = process.env.FREEPIK_API_URL || "https://api.freepik.com";
const terminal = new Set(["COMPLETED", "FAILED"]);

function die(message) { throw new Error(message); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function request(path, options = {}) {
  const key = process.env.FREEPIK_API_KEY || die("Defina FREEPIK_API_KEY no ambiente.");
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "x-freepik-api-key": key, "content-type": "application/json", ...options.headers }
  });
  const text = await response.text();
  if (!response.ok) die(`Freepik ${response.status}: ${text}`);
  return JSON.parse(text).data;
}

async function localImage(value, base) {
  if (!value || /^https?:|^data:/i.test(value)) return value;
  const file = resolve(base, value);
  const ext = extname(file).toLowerCase();
  const mime = ext === ".png" ? "image/png" : ext === ".webp" ? "image/webp" : "image/jpeg";
  return `data:${mime};base64,${(await readFile(file)).toString("base64")}`;
}

async function download(url, output) {
  const response = await fetch(url);
  if (!response.ok) die(`Download ${response.status}: ${url}`);
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, Buffer.from(await response.arrayBuffer()));
}

async function main() {
  const manifestFile = process.argv[2] || die("Uso: node freepik.mjs <manifest.json> [--dry-run]");
  const manifestPath = resolve(manifestFile);
  const base = dirname(manifestPath);
  const spec = JSON.parse(await readFile(manifestPath, "utf8"));
  if (!/^\/v1\/ai\/[a-z0-9/_-]+$/i.test(spec.endpoint || "")) die("endpoint inválido");
  if (!spec.output) die("output é obrigatório");

  const payload = { ...spec.input };
  for (const field of ["image", "image_url", "image_tail"]) {
    if (payload[field]) payload[field] = await localImage(payload[field], base);
  }
  if (process.argv.includes("--dry-run")) {
    console.log(JSON.stringify({ endpoint: spec.endpoint, input: { ...payload, image: payload.image && "<image>" } }, null, 2));
    return;
  }

  let task = await request(spec.endpoint, { method: "POST", body: JSON.stringify(payload) });
  console.log(`${task.status}: ${task.task_id}`);
  while (!terminal.has(task.status)) {
    await sleep(spec.poll_seconds ? spec.poll_seconds * 1000 : 10000);
    task = await request(`${spec.endpoint}/${task.task_id}`);
    console.log(task.status);
  }
  if (task.status === "FAILED") die(task.error || "Geração falhou.");
  if (!task.generated?.length) die("Tarefa concluída sem arquivo gerado.");

  const output = resolve(base, spec.output);
  await download(task.generated[0], output);
  const ledger = `${output}.json`;
  await writeFile(ledger, JSON.stringify({ provider: "freepik", endpoint: spec.endpoint, task_id: task.task_id, input: spec.input, generated: task.generated, output, created_at: new Date().toISOString() }, null, 2));
  console.log(output);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
