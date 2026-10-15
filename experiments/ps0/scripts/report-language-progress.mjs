#!/usr/bin/env node
// Feature readiness is an explicitly subjective rubric, not measured conformance.
// Strict v7 PASS evidence comes from v7-coverage.json and exact-commit CI.
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, isAbsolute, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const feature = JSON.parse(readFileSync(resolve(root, "language-feature-progress.json"), "utf8"));
const coverage = JSON.parse(readFileSync(resolve(root, "v7-coverage.json"), "utf8"));
const fail = message => { throw new Error("PS0-LANGUAGE-PROGRESS: " + message); };
if (feature.schema !== "ps0-v7-language-readiness/1") fail("invalid schema");
if (feature.families.length !== 20) fail("20-family roster incomplete");
const ids = new Set();
let sum = 0;
for (const f of feature.families) {
  if (ids.has(f.id)) fail("duplicate family");
  ids.add(f.id);
  if (!Number.isInteger(f.score) || f.score < 0 || f.score > 5 || f.maxScore !== 5)
    fail("invalid score: " + f.id);
  if (f.score > 3 && f.stableCiQualified !== true)
    fail("high score without CI: " + f.id);
  if (f.score === 5 && coverage.cases.some(x => x.implementationStatus !== "PASS"))
    fail("no full v7 feature completion without full conformance receipts");
  if (!Array.isArray(f.sourceEvidence) || f.sourceEvidence.length === 0)
    fail("missing source evidence: " + f.id);
  for (const p of f.sourceEvidence) {
    if (isAbsolute(p) || p.includes("\\") || p.split("/").some(x => !x || x === "." || x === ".."))
      fail("unsafe evidence path " + p);
    const file = resolve(root, p);
    if (!file.startsWith(root + sep) || !existsSync(file))
      fail("missing evidence: " + file);
  }
  sum += f.score;
}
const max = feature.families.length * 5;
const percent = 100 * sum / max;
if (feature.score.sum !== sum || feature.score.max !== max ||
    feature.score.estimatedPercent !== percent) fail("percent drift");
const total = coverage.cases.length + coverage.errata.length +
  coverage.findings.length + coverage.corrections.length;
const qualified = coverage.cases.filter(x => x.implementationStatus === "PASS").length +
  [...coverage.errata,...coverage.findings,...coverage.corrections]
    .filter(x => x.status === "PASS").length;
const qualifiedPercent = 100 * qualified / total;
if (feature.score.qualifiedPercent !== qualifiedPercent) fail("qualified coverage drift");
console.log("PS0_LANGUAGE_PROGRESS: estimated readiness " + percent.toFixed(0) +
  "% (rubric " + sum + "/" + max + "); strict v7-qualified " +
  qualifiedPercent.toFixed(0) + "% (" + qualified + "/" + total + ")");
console.log("PS0_PROGRESS_METHOD: subjective feature-family estimate, NOT tests passed");
