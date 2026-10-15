#!/usr/bin/env node
// PS0 v7 coverage: never infer PASS from a fixture alone.
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, isAbsolute, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const inventory = JSON.parse(readFileSync(resolve(root, "v7-coverage.json"), "utf8"));
const fail = message => { throw new Error("PS0-COVERAGE: " + message); };
if (inventory.schema !== "ps0-v7-conformance-coverage/1") fail("schema drift");
if (inventory.source.leanStableCommit !== "eb6cafb7290e8bd5f2937522d8d804f58f02bafc") fail("wrong Lean pin");
if (inventory.source.gitBlob !== "25e1ef788794db175a2183679e37ff8c8e9b6a2e") fail("normative spec changed");
const sections = [["cases", 150], ["errata", 4], ["findings", 22], ["corrections", 5]];
const ids = new Set();
let complete = 0;
for (const [section, expected] of sections) {
  const rows = inventory[section];
  if (!Array.isArray(rows) || rows.length !== expected) fail(section + " incomplete");
  for (const row of rows) {
    if (typeof row.id !== "string" || ids.has(row.id)) fail("duplicate or invalid ID " + row.id);
    ids.add(row.id);
    const status = row.status ?? row.implementationStatus;
    if (!["PENDING", "PASS", "FAIL"].includes(status)) fail("bad status " + row.id);
    if (section === "cases") {
      const positive = row.id.startsWith("P-");
      const negative = row.id.startsWith("N-");
      if (!positive && !negative) fail("bad requirement ID");
      if (row.kind !== (positive ? "positive" : "negative")) fail("case kind drift " + row.id);
    }
    if (status === "PASS") {
      if (!row.qualifiedCommit || !/^[0-9a-f]{40}$/.test(row.qualifiedCommit)) fail("unqualified PASS " + row.id);
      if (section === "cases") {
        if (!row.qualifiedCiRun || !/^[0-9]+$/.test(String(row.qualifiedCiRun))) fail("CI evidence missing " + row.id);
        if (!row.fixture) fail("fixture missing " + row.id);
        if (row.kind === "negative" && !row.expectedDiagnostic) fail("negative diagnostic missing " + row.id);
      }
      complete++;
    }
    const fixtures = section === "cases" ? (row.fixture ? [row.fixture] : []) : (row.fixtureIds ?? []);
    for (const candidate of fixtures) {
      if (typeof candidate !== "string" || isAbsolute(candidate) || candidate.includes("\\") ||
          candidate.split("/").some(x => x === "" || x === "." || x === "..")) fail("unsafe fixture " + candidate);
      if (section === "cases" && !candidate.startsWith(row.kind === "positive" ? "tests/pass/" : "tests/fail/")) fail("fixture wrong category " + row.id);
      const file = resolve(root, candidate);
      if (!file.startsWith(root + sep) || !existsSync(file)) fail("fixture not found " + candidate);
    }
  }
}
const c = inventory.counts;
if (c.sourceSection13 !== 150 || c.positive !== 72 || c.negative !== 78 ||
    c.errata !== 4 || c.findings !== 22 || c.corrections !== 5) fail("coverage counts changed");
if (inventory.cases.filter(x => x.kind === "positive").length !== 72 ||
    inventory.cases.filter(x => x.kind === "negative").length !== 78) fail("test polarity changed");
const total = sections.reduce((n, [, size]) => n + size, 0);
console.log("PS0_V7_INVENTORY: 150 source cases (72 positive, 78 negative), 4 errata, 22 findings, 5 corrections; "+complete+"/"+total+" qualified");
if (process.argv.includes("--require-complete") && complete !== total)
  fail("v7 incomplete: " + (total - complete) + " requirements have no PASS receipt");
