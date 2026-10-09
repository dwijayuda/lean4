import { readFileSync, mkdirSync, writeFileSync, renameSync } from "node:fs";
import { join } from "node:path";

const source = process.argv[2];
if (!source) {
  throw new Error("usage: node publish.mjs <successful-lean-stdout.log>");
}

// The caller MUST run this only after Lean exits with status zero.
// We cannot infer proof success from the mere presence of emitted blocks.
const output = readFileSync(source, "utf8");
const marker = /@@LEAN_TS_BEGIN:([A-Za-z_][A-Za-z0-9_]*)@@\r?\n([\s\S]*?)\r?\n@@LEAN_TS_END:\1@@/g;
const blocks = new Map();
for (const match of output.matchAll(marker)) {
  const name = match[1];
  if (blocks.has(name)) {
    throw new Error("duplicate Lean TypeScript export: " + name);
  }
  blocks.set(name, match[2].trimEnd() + "\n");
}

if (blocks.size === 0) {
  throw new Error("Lean did not produce TypeScript export blocks");
}
const unmatched = output.replace(marker, "");
if (unmatched.includes("@@LEAN_TS_BEGIN:") || unmatched.includes("@@LEAN_TS_END:")) {
  throw new Error("incomplete or malformed Lean TypeScript export block");
}

mkdirSync("generated", { recursive: true });
for (const [name, code] of blocks) {
  const tmp = join("generated", "." + name + ".ts.tmp-" + process.pid);
  const dest = join("generated", name + ".ts");
  writeFileSync(tmp, code, "utf8");
  renameSync(tmp, dest);
}
console.log("Published " + blocks.size + " TypeScript modules after successful Lean checking");
