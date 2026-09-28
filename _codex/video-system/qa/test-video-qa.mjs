import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { inspectManifest } from "./video-qa.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const template = JSON.parse(fs.readFileSync(path.join(here, "..", "templates", "codex-video.example.json"), "utf8"));
const valid = inspectManifest(template, path.join(here, "..", "templates"));
assert.equal(valid.ok, true, valid.errors.join("\n"));

const badSplit = structuredClone(template);
badSplit.captions.position = "lower-third";
badSplit.scenes[0].ambientMotion = false;
badSplit.scenes[0].occupancy = .4;
const invalid = inspectManifest(badSplit);
assert.equal(invalid.ok, false);
assert.ok(invalid.errors.some(message => message.includes("divider")));
assert.ok(invalid.errors.some(message => message.includes("estático")));
assert.ok(invalid.errors.some(message => message.includes("62%")));

console.log("video-qa: 2 cenários validados");

